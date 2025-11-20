#!/usr/bin/env python3
import os
import time
import logging
import sys
from PIL import Image

# E-ink display imports
sys.path.append('/home/pi/e-Paper/RaspberryPi_JetsonNano/python/lib')
from waveshare_epd import epd7in5b_V2

# Configuration
IMG_DIR = "/home/pi/pics"
DELAY_SECONDS = 3  # Fast for testing ghosting
WIDTH, HEIGHT = 800, 480

# Setup logging
logging.basicConfig(level=logging.INFO)

def list_images(folder):
    exts = (".png", ".jpg", ".jpeg", ".bmp")
    if not os.path.isdir(folder):
        print(f"Image folder does not exist: {folder}")
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
    """Convert to e-ink black/red layers without dithering"""
    img = img.convert("RGB")
    
    black_layer = Image.new("1", (width, height), 255)  # white
    red_layer = Image.new("1", (width, height), 255)   # white
    
    pixels = img.load()
    black_pixels = black_layer.load()
    red_pixels = red_layer.load()
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            
            # Strong red detection
            if r > 150 and g < 80 and b < 80:
                red_pixels[x, y] = 0  # show red
                continue
            
            # Black detection
            if (r + g + b) / 3 < 100:
                black_pixels[x, y] = 0  # show black
                continue
    
    return black_layer, red_layer

def main():
    print("🔴 Starting NO-REFRESH circle ghosting experiment...")
    print("This will layer circles WITHOUT clearing the screen")
    
    # Initialize display
    try:
        epd = epd7in5b_V2.EPD()
        print("Initializing e-Paper display...")
        epd.init()
        
        # IMPORTANT: Clear only once at the start
        print("Clearing screen once at start...")
        epd.Clear()
        
    except Exception as e:
        print(f"Display initialization failed: {e}")
        return
    
    image_count = 0
    
    try:
        while True:
            images = list_images(IMG_DIR)
            if not images:
                print("No images found, waiting...")
                time.sleep(5)
                continue
            
            for img_path in images:
                try:
                    print(f"\\n🔴 Image {image_count + 1}: {os.path.basename(img_path)}")
                    
                    # Load and process image
                    img = Image.open(img_path)
                    img = prepare_image(img, WIDTH, HEIGHT)
                    black_layer, red_layer = convert_to_epaper_layers(img, WIDTH, HEIGHT)
                    
                    # Convert for display
                    black_buffer = epd.getbuffer(black_layer)
                    red_buffer = epd.getbuffer(red_layer)
                    
                    # CRITICAL: Display WITHOUT clearing
                    # This will layer over existing content = GHOSTING!
                    print("📱 Displaying WITHOUT refresh (ghosting mode)...")
                    epd.display(black_buffer, red_buffer)
                    
                    image_count += 1
                    print(f"✅ Ghosted image {image_count} onto display")
                    
                    time.sleep(DELAY_SECONDS)
                    
                except Exception as e:
                    print(f"Error processing {img_path}: {e}")
                    continue
                    
    except KeyboardInterrupt:
        print("\\n🛑 Ghosting experiment stopped")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            epd.sleep()
            print("Display sleeping")
        except:
            pass

if __name__ == "__main__":
    main()