"""A minimal PNG decoder, in the spirit of the rest of :mod:`mlxlib`.

Real MLX (and MLX42) ship a function that turns a PNG file straight
into an image the rest of the library can blit -- ``mlx_png_file_to_image``
and friends.  This module is that function's work-alike: it understands
exactly the subset of the PNG format the shipped artwork uses (8-bit
truecolour, with or without alpha, not interlaced) and turns it into a
flat RGBA byte buffer, using nothing but :mod:`struct` and :mod:`zlib`
the way a hand-rolled decoder would.
"""

import struct
import zlib
from pathlib import Path
from typing import Final, Optional

_SIGNATURE: Final = b"\x89PNG\r\n\x1a\n"
_CHANNELS_BY_COLOR_TYPE: Final = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}


class PngError(Exception):
    """Raised when a file is not a PNG this decoder can read."""


def decode(path: Path) -> tuple[bytes, int, int]:
    """Decode *path* into a flat top-to-bottom RGBA8 buffer.

    Returns:
        A ``(pixels, width, height)`` tuple; ``pixels`` holds
        ``width * height * 4`` bytes.

    Raises:
        PngError: When the file is missing, truncated, or uses a PNG
            feature this decoder does not implement (palettes,
            interlacing, bit depths other than 8, ...).
    """
    try:
        data = path.read_bytes()
    except OSError as error:
        raise PngError("cannot read %s (%s)" % (path, error)) from error
    if not data.startswith(_SIGNATURE):
        raise PngError("%s is not a PNG file" % path)
    header, body = _read_chunks(data, path)
    width, height, color_type = header
    channels = _CHANNELS_BY_COLOR_TYPE[color_type]
    try:
        raw = zlib.decompress(bytes(body))
    except zlib.error as error:
        raise PngError("corrupt PNG stream in %s (%s)" % (path, error)) \
            from error
    scanlines = _unfilter(raw, width, height, channels)
    if channels == 4:
        return bytes(scanlines), width, height
    return _add_alpha(scanlines, width, height), width, height


def _read_chunks(data: bytes,
                 path: Path) -> tuple[tuple[int, int, int], bytearray]:
    """Walk every chunk, validating the header and collecting IDAT."""
    header: Optional[tuple[int, int, int]] = None
    body = bytearray()
    offset = len(_SIGNATURE)
    while offset < len(data):
        if offset + 8 > len(data):
            raise PngError("%s is truncated" % path)
        length, kind = struct.unpack_from(">I4s", data, offset)
        chunk_start = offset + 8
        chunk = data[chunk_start:chunk_start + length]
        if kind == b"IHDR":
            header = _read_ihdr(chunk, path)
        elif kind == b"IDAT":
            body += chunk
        elif kind == b"IEND":
            break
        offset = chunk_start + length + 4  # skip the trailing CRC
    if header is None:
        raise PngError("%s has no IHDR chunk" % path)
    return header, body


def _read_ihdr(chunk: bytes, path: Path) -> tuple[int, int, int]:
    """Validate the IHDR chunk and return ``(width, height, colour type)``."""
    width, height, depth, color_type, _compression, _filter, interlace = \
        struct.unpack(">IIBBBBB", chunk)
    if depth != 8:
        raise PngError("unsupported bit depth %d in %s" % (depth, path))
    if color_type not in (2, 6):
        raise PngError("unsupported colour type %d in %s" %
                       (color_type, path))
    if interlace:
        raise PngError("interlaced PNGs are not supported (%s)" % path)
    return width, height, color_type


def _unfilter(raw: bytes, width: int, height: int,
              channels: int) -> bytearray:
    """Reverse the per-scanline PNG filters into a flat pixel buffer."""
    stride = width * channels
    expected = (stride + 1) * height
    if len(raw) < expected:
        raise PngError("PNG pixel data is shorter than expected")
    out = bytearray(stride * height)
    previous = bytearray(stride)
    position = 0
    for row in range(height):
        filter_type = raw[position]
        position += 1
        current = bytearray(raw[position:position + stride])
        position += stride
        _unfilter_row(filter_type, current, previous, channels)
        out[row * stride:(row + 1) * stride] = current
        previous = current
    return out


def _unfilter_row(filter_type: int, current: bytearray, previous: bytearray,
                  channels: int) -> None:
    """Undo one scanline filter in place."""
    if filter_type == 0:
        return
    if filter_type == 1:
        for i in range(channels, len(current)):
            current[i] = (current[i] + current[i - channels]) & 0xFF
    elif filter_type == 2:
        for i in range(len(current)):
            current[i] = (current[i] + previous[i]) & 0xFF
    elif filter_type == 3:
        for i in range(len(current)):
            left = current[i - channels] if i >= channels else 0
            current[i] = (current[i] + (left + previous[i]) // 2) & 0xFF
    elif filter_type == 4:
        for i in range(len(current)):
            left = current[i - channels] if i >= channels else 0
            up_left = previous[i - channels] if i >= channels else 0
            current[i] = (current[i]
                          + _paeth(left, previous[i], up_left)) & 0xFF
    else:
        raise PngError("unsupported PNG filter type %d" % filter_type)


def _paeth(left: int, up: int, up_left: int) -> int:
    """The PNG "Paeth" predictor used by filter type 4."""
    estimate = left + up - up_left
    dist_left = abs(estimate - left)
    dist_up = abs(estimate - up)
    dist_up_left = abs(estimate - up_left)
    if dist_left <= dist_up and dist_left <= dist_up_left:
        return left
    if dist_up <= dist_up_left:
        return up
    return up_left


def _add_alpha(rgb: bytearray, width: int, height: int) -> bytes:
    """Expand an opaque RGB buffer into RGBA, alpha forced to 255."""
    out = bytearray(width * height * 4)
    for pixel in range(width * height):
        out[pixel * 4:pixel * 4 + 3] = rgb[pixel * 3:pixel * 3 + 3]
        out[pixel * 4 + 3] = 255
    return bytes(out)
