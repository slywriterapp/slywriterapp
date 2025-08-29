#!/usr/bin/env python3
"""
Generate a premium animated background with a soft purple blob drifting on a dark gradient.
240 frames @ 24fps = 10 second seamless loop
"""

import os
import math
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

def create_gradient_base(width, height):
    """Create the dark gradient base"""
    # Create base image
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    
    # Dark gradient colors (navy to darker navy)
    top_color = (15, 15, 35)      # #0F0F23
    bottom_color = (26, 27, 62)   # #1A1B3E
    
    # Create vertical gradient
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    return img

def create_soft_circle(size, color, fade_power=2):
    """Create a soft circular blob with smooth edges"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center = size // 2
    max_radius = center * 0.8
    
    # Create multiple concentric circles with decreasing opacity
    steps = 30
    for i in range(steps):
        radius = max_radius * (1 - i / steps)
        alpha = int(255 * (1 - i / steps) ** fade_power)
        
        # Calculate circle bounds
        x0 = center - radius
        y0 = center - radius
        x1 = center + radius
        y1 = center + radius
        
        # Draw circle with current alpha
        circle_color = (*color, alpha)
        draw.ellipse([x0, y0, x1, y1], fill=circle_color)
    
    # Apply additional gaussian blur for extra softness
    img = img.filter(ImageFilter.GaussianBlur(radius=3))
    return img

def blend_images(base, overlay, position, blend_mode='normal'):
    """Blend overlay onto base at given position"""
    result = base.copy()
    
    # Calculate paste position (centered)
    x, y = position
    overlay_size = overlay.size[0]
    paste_x = int(x - overlay_size // 2)
    paste_y = int(y - overlay_size // 2)
    
    # Ensure overlay stays within bounds
    if paste_x < -overlay_size or paste_y < -overlay_size:
        return result
    if paste_x > base.size[0] or paste_y > base.size[1]:
        return result
    
    # Paste with alpha blending
    result.paste(overlay, (paste_x, paste_y), overlay)
    return result

def generate_animation_frames():
    """Generate all 240 frames of the animation"""
    
    # Animation settings
    width, height = 1400, 900
    num_frames = 240
    fps = 24
    
    # Create output directory
    frames_dir = os.path.join('assets', 'backgrounds', 'frames')
    os.makedirs(frames_dir, exist_ok=True)
    
    # Create base gradient (reused for all frames)
    print("Creating base gradient...")
    base_gradient = create_gradient_base(width, height)
    
    # Create soft purple blob
    print("Creating purple blob...")
    blob_size = 300
    purple_color = (93, 31, 179)  # #5D1FB3
    soft_blob = create_soft_circle(blob_size, purple_color, fade_power=1.8)
    
    print(f"Generating {num_frames} frames...")
    
    for frame in range(num_frames):
        # Calculate time progress (0 to 2π for seamless loop)
        t = (frame / num_frames) * 2 * math.pi
        
        # Create complex motion path using multiple sine/cosine waves
        # Main orbital motion
        center_x = width // 2
        center_y = height // 2
        
        # Multiple circular motions for complex path
        orbit_radius_x = width * 0.25
        orbit_radius_y = height * 0.2
        
        # Primary motion (slow, large)
        primary_x = center_x + orbit_radius_x * math.cos(t)
        primary_y = center_y + orbit_radius_y * math.sin(t * 0.8)
        
        # Secondary motion (faster, smaller) - creates figure-8 like patterns
        secondary_radius = 80
        secondary_x = secondary_radius * math.cos(t * 2.3)
        secondary_y = secondary_radius * math.sin(t * 1.7)
        
        # Combine motions
        blob_x = primary_x + secondary_x
        blob_y = primary_y + secondary_y
        
        # Ensure blob stays within bounds
        blob_x = max(blob_size//2, min(width - blob_size//2, blob_x))
        blob_y = max(blob_size//2, min(height - blob_size//2, blob_y))
        
        # Create frame by blending blob onto gradient
        frame_img = blend_images(base_gradient, soft_blob, (blob_x, blob_y))
        
        # Add subtle color variation to blob based on position
        # This creates additional visual interest
        color_variation = math.sin(t * 1.5) * 0.1 + 1.0
        if color_variation != 1.0:
            # Slight color shift
            enhanced = Image.new('RGBA', (blob_size, blob_size), (0, 0, 0, 0))
            enhanced_draw = ImageDraw.Draw(enhanced)
            
            # Create color-shifted blob
            varied_color = (
                min(255, int(purple_color[0] * color_variation)),
                min(255, int(purple_color[1] * color_variation)),
                min(255, int(purple_color[2] * color_variation))
            )
            varied_blob = create_soft_circle(blob_size, varied_color, fade_power=1.8)
            frame_img = blend_images(base_gradient, varied_blob, (blob_x, blob_y))
        
        # Save frame
        frame_path = os.path.join(frames_dir, f"frame_{frame:03d}.png")
        frame_img.save(frame_path, 'PNG')
        
        # Progress indicator
        if frame % 24 == 0:
            print(f"Generated frame {frame}/{num_frames} ({frame/num_frames*100:.1f}%)")
    
    print(f"All {num_frames} frames generated in {frames_dir}/")
    return frames_dir

def create_gif_from_frames(frames_dir):
    """Convert frames to animated GIF"""
    print("Creating animated GIF...")
    
    # Load all frames
    frame_files = sorted([f for f in os.listdir(frames_dir) if f.endswith('.png')])
    frames = []
    
    for frame_file in frame_files:
        frame_path = os.path.join(frames_dir, frame_file)
        frame = Image.open(frame_path)
        frames.append(frame)
    
    # Create GIF
    gif_path = os.path.join('assets', 'backgrounds', 'main_bg.gif')
    
    # Save as animated GIF
    # Duration = 1000ms / 24fps = ~42ms per frame
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=42,  # 24 FPS
        loop=0,  # Infinite loop
        optimize=True
    )
    
    print(f"Animated GIF created: {gif_path}")
    return gif_path

def create_mp4_from_frames(frames_dir):
    """Convert frames to MP4 (if ffmpeg is available)"""
    try:
        import subprocess
        
        print("Creating MP4 video...")
        
        mp4_path = os.path.join('assets', 'backgrounds', 'main_bg.mp4')
        frame_pattern = os.path.join(frames_dir, 'frame_%03d.png')
        
        # Use ffmpeg to create MP4
        cmd = [
            'ffmpeg', '-y',  # Overwrite existing
            '-framerate', '24',
            '-i', frame_pattern,
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-crf', '18',  # High quality
            '-preset', 'slow',  # Better compression
            mp4_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"MP4 created: {mp4_path}")
            return mp4_path
        else:
            print(f"FFmpeg error: {result.stderr}")
            return None
            
    except (ImportError, FileNotFoundError):
        print("FFmpeg not available, skipping MP4 creation")
        return None

if __name__ == "__main__":
    print("Generating Premium Animated Background...")
    print("=" * 50)
    
    # Generate all frames
    frames_dir = generate_animation_frames()
    
    # Create GIF
    gif_path = create_gif_from_frames(frames_dir)
    
    # Try to create MP4 (better quality, smaller file)
    mp4_path = create_mp4_from_frames(frames_dir)
    
    print("\n" + "=" * 50)
    print("Animation generation complete!")
    
    if mp4_path:
        print(f"MP4: {mp4_path}")
    print(f"GIF: {gif_path}")
    print(f"Frames: {frames_dir}/")
    
    print("\nThe app will automatically use the animated background!")