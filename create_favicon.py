#!/usr/bin/env python3
"""
Create PNG favicon files for better browser compatibility.
This script creates a simple orange/white favicon without requiring PIL.
"""

import struct
import zlib

def create_png_chunk(chunk_type, data):
    """Create a PNG chunk with type and data"""
    chunk = chunk_type + data
    return struct.pack('>I', len(data)) + chunk + struct.pack('>I', zlib.crc32(chunk) & 0xffffffff)

def create_png_image(width, height, background_color, inner_color=None):
    """Create a PNG image with a circle"""
    # PNG signature
    signature = b'\x89PNG\r\n\x1a\n'
    
    # IHDR chunk (image header)
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr = create_png_chunk(b'IHDR', ihdr_data)
    
    # IDAT chunk (image data)
    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'  # Filter byte
        for x in range(width):
            # Calculate pixel color
            cx, cy = x - width//2, y - height//2
            radius = width // 2
            
            if inner_color and (cx*cx + cy*cy) <= (radius * 0.6)**2:
                # Inner circle (orange)
                raw_data += bytes(inner_color)
            elif (cx*cx + cy*cy) <= radius**2:
                # Outer ring (white)
                raw_data += bytes(background_color)
            else:
                # Transparent background
                raw_data += b'\xff\xff\xff\x00'
    
    compressed = zlib.compress(raw_data, 9)
    idat = create_png_chunk(b'IDAT', compressed)
    
    # IEND chunk
    iend = create_png_chunk(b'IEND', b'')
    
    return signature + ihdr + idat + iend

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_favicons():
    """Create favicon.png and apple-touch-icon.png"""
    # Colors
    orange = hex_to_rgb('#FF9F0A')
    white = hex_to_rgb('#FFFFFF')
    
    # Create 32x32 favicon.png
    print("Creating favicon.png (32x32)...")
    favicon_data = create_png_image(32, 32, white, orange)
    with open('static/favicon.png', 'wb') as f:
        f.write(favicon_data)
    print("  Created static/favicon.png")
    
    # Create 180x180 apple-touch-icon.png
    print("Creating apple-touch-icon.png (180x180)...")
    apple_icon_data = create_png_image(180, 180, white, orange)
    with open('static/apple-touch-icon.png', 'wb') as f:
        f.write(apple_icon_data)
    print("  Created static/apple-touch-icon.png")
    
    # Also create a 192x192 icon for Android
    print("Creating icon-192.png (192x192)...")
    icon_192_data = create_png_image(192, 192, white, orange)
    with open('static/icon-192.png', 'wb') as f:
        f.write(icon_192_data)
    print("  Created static/icon-192.png")
    
    # Also create a 512x512 icon for high DPI displays
    print("Creating icon-512.png (512x512)...")
    icon_512_data = create_png_image(512, 512, white, orange)
    with open('static/icon-512.png', 'wb') as f:
        f.write(icon_512_data)
    print("  Created static/icon-512.png")
    
    # Also create a 144x144 icon for Microsoft tiles
    print("Creating icon-144.png (144x144)...")
    icon_144_data = create_png_image(144, 144, white, orange)
    with open('static/icon-144.png', 'wb') as f:
        f.write(icon_144_data)
    print("  Created static/icon-144.png")
    
    print("\nAll favicon files created successfully!")

if __name__ == '__main__':
    create_favicons()

