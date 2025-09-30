from PIL import Image, ImageDraw, ImageFont
import os

# Create assets directory if it doesn't exist
assets_dir = r"C:\Typing Project\slywriter-electron\assets"
if not os.path.exists(assets_dir):
    os.makedirs(assets_dir)

# Color scheme matching the app's new subtle design
PRIMARY_COLOR = (79, 70, 229)  # Indigo-600
SECONDARY_COLOR = (99, 102, 241)  # Indigo-500
GRADIENT_START = (99, 102, 241)  # Indigo-500
GRADIENT_END = (59, 130, 246)  # Blue-500
BACKGROUND = (17, 24, 39)  # Gray-900
TEXT_COLOR = (243, 244, 246)  # Gray-100

def create_gradient(width, height, start_color, end_color, vertical=True):
    """Create a gradient image"""
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)

    for i in range(height if vertical else width):
        # Calculate interpolated color
        ratio = i / (height if vertical else width)
        r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
        g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
        b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)

        if vertical:
            draw.line([(0, i), (width, i)], fill=(r, g, b))
        else:
            draw.line([(i, 0), (i, height)], fill=(r, g, b))

    return image

def create_header_graphic():
    """Create 150x57px header graphic for NSIS installer"""
    width, height = 150, 57

    # Create gradient background
    img = create_gradient(width, height, GRADIENT_START, GRADIENT_END, vertical=False)
    draw = ImageDraw.Draw(img)

    # Add subtle pattern overlay
    for x in range(0, width, 20):
        draw.line([(x, 0), (x + 10, height)], fill=(255, 255, 255, 15), width=1)

    # Add text
    try:
        # Try to use a system font
        font = ImageFont.truetype("arial.ttf", 20)
        small_font = ImageFont.truetype("arial.ttf", 10)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Draw SlyWriter text
    text = "SlyWriter"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2 - 5

    # Add subtle shadow
    draw.text((x+1, y+1), text, fill=(0, 0, 0, 128), font=font)
    draw.text((x, y), text, fill=TEXT_COLOR, font=font)

    # Add tagline
    tagline = "AI Typing Assistant"
    bbox = draw.textbbox((0, 0), tagline, font=small_font)
    tag_width = bbox[2] - bbox[0]
    x = (width - tag_width) // 2
    y = height - 15
    draw.text((x, y), tagline, fill=(200, 200, 200), font=small_font)

    # Save as BMP
    img.save(os.path.join(assets_dir, "installerHeader.bmp"), "BMP")
    print("Created installerHeader.bmp (150x57)")

def create_sidebar_graphic():
    """Create 164x314px sidebar graphic for NSIS installer"""
    width, height = 164, 314

    # Create gradient background
    img = create_gradient(width, height, BACKGROUND, GRADIENT_END, vertical=True)
    draw = ImageDraw.Draw(img)

    # Add decorative elements
    # Top accent line
    draw.rectangle([(0, 0), (width, 3)], fill=GRADIENT_START)

    # Add circular design elements
    for i in range(3):
        y = 50 + i * 80
        x = width // 2
        radius = 25 - i * 5
        # Outer circle with gradient effect
        draw.ellipse([(x-radius-2, y-radius-2), (x+radius+2, y+radius+2)],
                     fill=None, outline=GRADIENT_START, width=2)
        draw.ellipse([(x-radius, y-radius), (x+radius, y+radius)],
                     fill=PRIMARY_COLOR)

    # Add feature text
    try:
        font = ImageFont.truetype("arial.ttf", 12)
        bold_font = ImageFont.truetype("arialbd.ttf", 14)
    except:
        font = ImageFont.load_default()
        bold_font = ImageFont.load_default()

    features = [
        "✓ Auto-Typing",
        "✓ AI Humanizer",
        "✓ Smart Hotkeys",
        "✓ Premium Features"
    ]

    y_start = 220
    for i, feature in enumerate(features):
        y = y_start + i * 25
        draw.text((20, y), feature, fill=TEXT_COLOR, font=font)

    # Add version info at bottom
    version_text = "Version 2.0.9"
    bbox = draw.textbbox((0, 0), version_text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) // 2
    draw.text((x, height - 20), version_text, fill=(150, 150, 150), font=font)

    # Add subtle pattern
    for y in range(0, height, 30):
        draw.line([(0, y), (width, y)], fill=(255, 255, 255, 10), width=1)

    # Save as BMP
    img.save(os.path.join(assets_dir, "installerSidebar.bmp"), "BMP")
    print("Created installerSidebar.bmp (164x314)")

def create_placeholder_icon():
    """Create a simple placeholder icon since we need the logo separately"""
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Create circular icon with gradient effect
    center = size // 2
    radius = size // 2 - 10

    # Draw gradient circle
    for r in range(radius, 0, -1):
        ratio = r / radius
        color = (
            int(GRADIENT_START[0] * ratio + GRADIENT_END[0] * (1-ratio)),
            int(GRADIENT_START[1] * ratio + GRADIENT_END[1] * (1-ratio)),
            int(GRADIENT_START[2] * ratio + GRADIENT_END[2] * (1-ratio)),
            255
        )
        draw.ellipse([(center-r, center-r), (center+r, center+r)], fill=color)

    # Add "S" letter in center
    try:
        font = ImageFont.truetype("arialbd.ttf", 120)
    except:
        font = ImageFont.load_default()

    text = "S"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = center - text_width // 2
    y = center - text_height // 2 - 10
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

    # Save as PNG (you'll need to convert to ICO)
    img.save(os.path.join(assets_dir, "icon_placeholder.png"), "PNG")
    print("Created icon_placeholder.png (256x256) - Convert to ICO with online tool or provide actual logo")

if __name__ == "__main__":
    print("Creating installer graphics...")
    create_header_graphic()
    create_sidebar_graphic()
    create_placeholder_icon()
    print("\nAll graphics created successfully!")
    print(f"Files saved to: {assets_dir}")
    print("\nNOTE: You'll need to:")
    print("1. Replace icon_placeholder.png with your actual logo")
    print("2. Convert the logo to .ico format (use an online converter)")
    print("3. The header and sidebar BMPs are ready to use!")