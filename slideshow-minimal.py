#!/usr/bin/env python3
import os
import time
from PIL import Image
import sys

# E-ink display imports
sys.path.append('/home/pi/e-Paper/RaspberryPi_JetsonNano/python/lib')
from waveshare_epd import epd7in5b_V2

# Configuration
IMG_DIR = "/home/pi/pics"
DELAY_SECONDS = 5  # Slower for debugging
WIDTH, HEIGHT = 800, 480

def list_images(folder):
    exts = (".png", ".jpg", ".jpeg", ".bmp")
    if not os.path.isdir(folder):
        return []
    files = [f for f in os.listdir(folder) if f.lower().endswith(exts)]
    files.sort()
    return [os.path.join(folder, f) for f in files]

def prepare_image(img, width, height):
    if img.height > img.width:
        img = img.rotate(-90, expand=True)
    return img.resize((width, height))

def convert_to_epaper_layers(img, width, height):
    img = img.convert("RGB")
    
    black_layer = Image.new("1", (width, height), 255)
    red_layer = Image.new("1", (width, height), 255)
    
    pixels = img.load()
    black_pixels = black_layer.load()
    red_pixels = red_layer.load()
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            
            if r > 150 and g < 80 and b < 80:
                red_pixels[x, y] = 0
                continue
            
            if (r + g + b) / 3 < 100:
                black_pixels[x, y] = 0
                continue
    
    return black_layer, red_layer

def main():
    print("🔴 MINIMAL ghosting test - checking for automatic clears")
    
    try:
        epd = epd7in5b_V2.EPD()
        print("Initializing display...")
        epd.init()
        
        # Clear ONLY ONCE at the very beginning
        print("🧹 ONE-TIME CLEAR at startup")
        epd.Clear()
        print("✅ Startup clear complete - NO MORE CLEARING")
        
    except Exception as e:
        print(f"Display failed: {e}")
        return
    
    image_count = 0
    
    try:
        while True:
            images = list_images(IMG_DIR)
            if not images:
                time.sleep(3)
                continue
            
            for img_path in images:
                try:
                    print(f"\\n🔴 Image {image_count + 1}: {os.path.basename(img_path)}")
                    print("    IMPORTANT: Watch for any flicker - this indicates auto-clearing")
                    
                    img = Image.open(img_path)
                    img = prepare_image(img, WIDTH, HEIGHT)
                    black_layer, red_layer = convert_to_epaper_layers(img, WIDTH, HEIGHT)
                    
                    black_buffer = epd.getbuffer(black_layer)
                    red_buffer = epd.getbuffer(red_layer)
                    
                    print("    📱 Calling epd.display() - NO epd.Clear() before this")
                    
                    # Just display - no clearing anywhere
                    epd.display(black_buffer, red_buffer)
                    
                    print(f"    ✅ Display call complete for image {image_count + 1}")
                    print(f"    🔍 Look for: ghosting of previous circles")
                    
                    image_count += 1
                    time.sleep(DELAY_SECONDS)
                    
                except Exception as e:
                    print(f"Error with {img_path}: {e}")
                    continue
                    
    except KeyboardInterrupt:
        print("\\n🛑 Minimal ghosting test stopped")
    finally:
        try:
            epd.sleep()
        except:
            pass

if __name__ == "__main__":
    main()