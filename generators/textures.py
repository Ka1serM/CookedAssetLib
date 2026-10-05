import math
import os
import struct
import tempfile
import zlib

import unreal

from common import duplicate_engine_asset, import_file, create_asset, load

SIZE = 256


def png_chunk(kind, data):
    body = kind + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))


def write_png(path, width, height, color_type, channels, pixel):
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            rows += bytes(pixel(x, y)[:channels])
    header = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    with open(path, "wb") as file:
        file.write(b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", header) + png_chunk(b"IDAT", zlib.compress(bytes(rows))) + png_chunk(b"IEND", b""))


def write_tga(path, width, height, pixel):
    header = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, width, height, 32, 8)
    with open(path, "wb") as file:
        file.write(header)
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixel(x, y)
                file.write(bytes((b, g, r, a)))


def write_hdr(path, width, height, pixel):
    with open(path, "wb") as file:
        file.write(f"#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n-Y {height} +X {width}\n".encode())
        for y in range(height):
            for x in range(width):
                red, green, blue = pixel(x, y)
                brightest = max(red, green, blue)
                mantissa, exponent = math.frexp(brightest)
                scale = mantissa * 256 / brightest if brightest > 0 else 0
                file.write(bytes((int(red * scale), int(green * scale), int(blue * scale), exponent + 128 if brightest > 0 else 0)))


def checker(x, y):
    return (x, y, 255 if (x // 32 + y // 32) % 2 else 64, 255 - x // 2)


def normal_bump(x, y):
    dx = math.cos(x * math.tau / 32) * 0.4
    dy = math.cos(y * math.tau / 32) * 0.4
    length = math.sqrt(dx * dx + dy * dy + 1)
    return (int((dx / length * 0.5 + 0.5) * 255), int((dy / length * 0.5 + 0.5) * 255), int((1 / length * 0.5 + 0.5) * 255), 255)


def import_texture(name, source, **settings):
    texture = import_file(source, "Texture", name)[0]
    for key, value in settings.items():
        texture.set_editor_property(key, value)
    return texture


def generate():
    folder = tempfile.gettempdir()
    paths = {name: os.path.join(folder, name) for name in ("checker.png", "nonpow2.png", "normal.png", "mask.png", "gray.png", "checker.tga", "sky.hdr")}
    write_png(paths["checker.png"], SIZE, SIZE, 6, 4, checker)
    write_png(paths["nonpow2.png"], 100, 60, 2, 3, lambda x, y: (x * 2, y * 4, 128))
    write_png(paths["normal.png"], SIZE, SIZE, 6, 4, normal_bump)
    write_png(paths["mask.png"], SIZE, SIZE, 2, 3, lambda x, y: (255 if x > y else 0, x, y))
    write_png(paths["gray.png"], SIZE, SIZE, 0, 1, lambda x, y: ((x + y) // 2,))
    write_tga(paths["checker.tga"], 128, 128, lambda x, y: (x * 2, y * 2, 128, 255))
    write_hdr(paths["sky.hdr"], 128, 64, lambda x, y: (x / 16, y / 8, 4.0 if (x + y) % 32 < 4 else 0.25))

    compression = unreal.TextureCompressionSettings
    import_texture("T_Checker", paths["checker.png"], virtual_texture_streaming=False)
    import_texture("T_CheckerVirtual", paths["checker.png"], virtual_texture_streaming=True)
    import_texture("T_NonPowerOfTwo", paths["nonpow2.png"])
    import_texture("T_Normal", paths["normal.png"], compression_settings=compression.TC_NORMALMAP)
    import_texture("T_Mask", paths["mask.png"], compression_settings=compression.TC_MASKS, srgb=False)
    import_texture("T_Grayscale", paths["gray.png"], compression_settings=compression.TC_GRAYSCALE)
    import_texture("T_Targa", paths["checker.tga"])
    import_texture("T_Hdr", paths["sky.hdr"], compression_settings=compression.TC_HDR)
    import_texture("T_HighQuality", paths["checker.png"], compression_settings=compression.TC_BC7)
    import_texture("T_NoMips", paths["checker.png"], mip_gen_settings=unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    import_texture("T_Interface", paths["checker.png"], lod_group=unreal.TextureGroup.TEXTUREGROUP_UI, never_stream=True)
    duplicate_engine_asset("/Engine/EngineResources/DefaultTextureCube", "Texture", "TC_Cube")
    target = create_asset("Texture", "RT_Target", unreal.TextureRenderTarget2D, unreal.TextureRenderTargetFactoryNew())
    target.set_editor_properties({"size_x": 128, "size_y": 128})
