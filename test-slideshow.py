#!/usr/bin/env python3
import os
import time
from PIL import Image

IMG_DIR = "./pics"  # Use local pics folder
DELAY_SECONDS = 5   # Faster for testing

def list_images(folder):
    exts = (".png", ".jpg", ".jpeg", ".bmp")
    if not os.path.isdir(folder):
        print("Image folder does not exist:", folder)
        return []
    files = [f for f in os.listdir(folder) if f.lower().endswith(exts)]
    files.sort()
    return [os.path.join(folder, f) for f in files]

def prepare_image(img, width, height):
    """Prepare image: rotate if portrait, resize."""
    if img.height > img.width:
        img = img.rotate(-90, expand=True)
    return img.resize((width, height))

def convert_to_epaper_layers(img, width, height):
    """
    Convert full-color image into two 1-bit layers:
    - black layer
    - red layer
    All others become white.
    """
    img = img.convert("RGB")  # keep color info

    black_layer = Image.new("1", (width, height), 255)  # white
    red_layer   = Image.new("1", (width, height), 255)  # white

    pixels = img.load()
    black_pixels = black_layer.load()
    red_pixels = red_layer.load()

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]

            # Decide red
            # Strong red is: high R, low G, low B
            if r > 150 and g < 80 and b < 80:
                red_pixels[x, y] = 0  # show red
                continue

            # Decide black
            # Dark pixel if average < 100
            if (r + g + b) / 3 < 100:
                black_pixels[x, y] = 0  # show black
                continue

            # Otherwise: pixel stays white (255)

    return black_layer, red_layer

def main():
    WIDTH, HEIGHT = 800, 480  # E-ink dimensions
    
    images = list_images(IMG_DIR)
    if not images:
        print("No images found.")
        return

    print("Found images:")
    for p in images:
        print("  ", p)

    for path in images:
        print("Processing:", path)

        try:
            img = Image.open(path)
        except Exception as e:
            print("Could not open image:", e)
            continue

        img = prepare_image(img, WIDTH, HEIGHT)
        black, red = convert_to_epaper_layers(img, WIDTH, HEIGHT)

        # Save processed images for inspection
        basename = os.path.splitext(os.path.basename(path))[0]
        black.save(f"./pics/{basename}_black.png")
        red.save(f"./pics/{basename}_red.png")
        
        print(f"✅ Processed {path} -> black/red layers saved")

if __name__ == "__main__":
    main()