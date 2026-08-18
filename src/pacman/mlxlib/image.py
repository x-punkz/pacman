"""An off-screen image buffer, the equivalent of an MLX image.

``mlx_new_image`` hands back an opaque image and ``mlx_get_data_addr``
hands back the raw pixel buffer behind it; everything a 42 student
draws is then written straight into that buffer.  :class:`Image` is
exactly that: a ``bytearray`` of RGB triplets plus the small helpers a
student would write on top of ``mlx_pixel_put``.
"""

from typing import Final

BYTES_PER_PIXEL: Final = 3

_DIM_TABLES: dict[int, bytes] = {}


def rgb(red: int, green: int, blue: int) -> int:
    """Pack *red*, *green* and *blue* (0-255) into a 0xRRGGBB integer."""
    return ((red & 0xFF) << 16) | ((green & 0xFF) << 8) | (blue & 0xFF)


def channels(color: int) -> tuple[int, int, int]:
    """Split a 0xRRGGBB integer into its three channels."""
    return (color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF


def mix(first: int, second: int, ratio: float) -> int:
    """Blend *first* towards *second*; *ratio* 0.0 keeps *first*."""
    ratio = min(1.0, max(0.0, ratio))
    red_a, green_a, blue_a = channels(first)
    red_b, green_b, blue_b = channels(second)
    return rgb(int(red_a + (red_b - red_a) * ratio),
               int(green_a + (green_b - green_a) * ratio),
               int(blue_a + (blue_b - blue_a) * ratio))


def _dim_table(factor: float) -> bytes:
    """Return (and cache) a 256-entry darkening table for *factor*."""
    key = int(max(0.0, min(1.0, factor)) * 255.0)
    table = _DIM_TABLES.get(key)
    if table is None:
        table = bytes((value * key) // 255 for value in range(256))
        _DIM_TABLES[key] = table
    return table


class Image:
    """A writable RGB pixel buffer."""

    __slots__ = ("width", "height", "stride", "data")

    def __init__(self, width: int, height: int) -> None:
        """Create an opaque black image of *width* x *height* pixels."""
        self.width = max(1, width)
        self.height = max(1, height)
        self.stride = self.width * BYTES_PER_PIXEL
        self.data = bytearray(self.stride * self.height)

    def clear(self, color: int = 0x000000) -> None:
        """Fill the whole image with *color*."""
        red, green, blue = channels(color)
        self.data[:] = bytes((red, green, blue)) * (self.width * self.height)

    def pixel_put(self, x: int, y: int, color: int) -> None:
        """Write a single pixel, silently ignoring out-of-bounds writes."""
        if 0 <= x < self.width and 0 <= y < self.height:
            offset = y * self.stride + x * BYTES_PER_PIXEL
            red, green, blue = channels(color)
            self.data[offset] = red
            self.data[offset + 1] = green
            self.data[offset + 2] = blue

    def pixel_get(self, x: int, y: int) -> int:
        """Read a single pixel; out-of-bounds reads return black."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return 0x000000
        offset = y * self.stride + x * BYTES_PER_PIXEL
        return rgb(self.data[offset], self.data[offset + 1],
                   self.data[offset + 2])

    def fill_rect(self, x: int, y: int, width: int, height: int,
                  color: int) -> None:
        """Fill a clipped rectangle with *color*."""
        left = max(0, x)
        top = max(0, y)
        right = min(self.width, x + width)
        bottom = min(self.height, y + height)
        if right <= left or bottom <= top:
            return
        red, green, blue = channels(color)
        span = bytes((red, green, blue)) * (right - left)
        offset = top * self.stride + left * BYTES_PER_PIXEL
        for _ in range(bottom - top):
            self.data[offset:offset + len(span)] = span
            offset += self.stride

    def rect_outline(self, x: int, y: int, width: int, height: int,
                     color: int, thickness: int = 1) -> None:
        """Draw the outline of a rectangle with *color*."""
        thickness = max(1, thickness)
        self.fill_rect(x, y, width, thickness, color)
        self.fill_rect(x, y + height - thickness, width, thickness, color)
        self.fill_rect(x, y, thickness, height, color)
        self.fill_rect(x + width - thickness, y, thickness, height, color)

    def fill_disc(self, center_x: int, center_y: int, radius: int,
                  color: int) -> None:
        """Fill a disc of *radius* pixels centred on the given point."""
        if radius <= 0:
            return
        squared = radius * radius
        for offset_y in range(-radius, radius + 1):
            half = int((squared - offset_y * offset_y) ** 0.5)
            self.fill_rect(center_x - half, center_y + offset_y,
                           half * 2 + 1, 1, color)

    def dim_rect(self, x: int, y: int, width: int, height: int,
                 factor: float) -> None:
        """Darken a clipped rectangle, keeping *factor* of each channel."""
        left = max(0, x)
        top = max(0, y)
        right = min(self.width, x + width)
        bottom = min(self.height, y + height)
        if right <= left or bottom <= top:
            return
        table = _dim_table(factor)
        length = (right - left) * BYTES_PER_PIXEL
        offset = top * self.stride + left * BYTES_PER_PIXEL
        for _ in range(bottom - top):
            end = offset + length
            self.data[offset:end] = bytes(self.data[offset:end]).translate(
                table)
            offset += self.stride

    def copy_from(self, other: "Image") -> None:
        """Replace the whole buffer with the contents of *other*."""
        if other.width != self.width or other.height != self.height:
            raise ValueError("image sizes differ")
        self.data[:] = other.data

    def to_bytes(self) -> bytes:
        """Return an immutable copy of the raw RGB buffer."""
        return bytes(self.data)
