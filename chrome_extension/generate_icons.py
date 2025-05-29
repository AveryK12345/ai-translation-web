from cairosvg import svg2png
import os

def generate_icons():
    # Create icons directory if it doesn't exist
    if not os.path.exists('icons'):
        os.makedirs('icons')

    # SVG content
    svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="128" height="128" viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
  <rect width="128" height="128" fill="#4CAF50" rx="20"/>
  <text x="64" y="80" font-family="Arial" font-size="80" fill="white" text-anchor="middle">T</text>
</svg>'''

    # Generate icons in different sizes
    sizes = [16, 48, 128]
    for size in sizes:
        svg2png(bytestring=svg_content.encode('utf-8'),
                write_to=f'icons/icon{size}.png',
                output_width=size,
                output_height=size)

if __name__ == '__main__':
    generate_icons() 