#!/usr/bin/env python3
import sys
sys.path.append('/home/pi/e-Paper/RaspberryPi_JetsonNano/python/lib')

import os
import time
from PIL import Image
from waveshare_epd import epd7in5b_V2

IMG_DIR = "/home/pi/pics"
DELAY_SECONDS = 3

def list_images(folder):
    exts = (".png", ".jpg", ".jpeg", ".bmp")
    if not os.path.isdir(folder):
        return []
    files = [f for f in os.listdir(folder) if f.lower().endswith(exts)]
    files.sort()
    return [os.path.join(folder, f) for f in files]

def convert_to_epaper_layers(img, width, height):
    img = img.convert("RGB")
    black_layer = Image.new("1", (width, height), 255)  # white
    red_layer = Image.new("1", (width, height), 255)    # white

    pixels = img.load()
    black_pixels = black_layer.load()
    red_pixels = red_layer.load()

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            
            if r > 150 and g < 80 and b < 80:  # Red
                red_pixels[x, y] = 0
            elif (r + g + b) / 3 < 100:  # Black
                black_pixels[x, y] = 0

    return black_layer, red_layer

def main():
    print("🎭 Simple Ghost Slideshow - No clearing between images")
    
    epd = epd7in5b_V2.EPD()
    epd.init()
    
    # Clear ONCE at the start
    print("Initial clear...")
    epd.Clear()
    time.sleep(2)
    
    first_image = True
    
    while True:
        images = list_images(IMG_DIR)
        if not images:
            time.sleep(2)
            continue
            
        for img_path in images:
            print(f"Adding: {os.path.basename(img_path)}")
            
            try:
                img = Image.open(img_path)
                if img.height > img.width:
                    img = img.rotate(-90, expand=True)
                img = img.resize((epd.width, epd.height))
                
                black_layer, red_layer = convert_to_epaper_layers(img, epd.width, epd.height)
                
                if first_image:
                    print("First image - full display")
                    epd.display(epd.getbuffer(black_layer), epd.getbuffer(red_layer))
                    first_image = False
                else:
                    # For ghosting: don't clear, just overlay
                    print("Ghosting - overlay only")
                    epd.display(epd.getbuffer(black_layer), epd.getbuffer(red_layer))
                
                time.sleep(DELAY_SECONDS)
                
            except Exception as e:
                print(f"Error: {e}")
                continue

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Slideshow stopped")
        try:
            epd7in5b_V2.EPD().sleep()
        except:
            pass