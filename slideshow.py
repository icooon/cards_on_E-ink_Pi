#!/usr/bin/env python3
import sys
sys.path.append('/home/pi/e-Paper/RaspberryPi_JetsonNano/python/lib')

import os
import time
from PIL import Image
from waveshare_epd import epd7in5b_V2

IMG_DIR = "/home/pi/pics"
DELAY_SECONDS = 30  # change later if you want slower slideshow


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
    epd = epd7in5b_V2.EPD()
    print("Initializing display...")
    epd.init()
    epd.Clear()

    images = list_images(IMG_DIR)
    if not images:
        print("No images found.")
        return

    print("Found images:")
    for p in images:
        print("  ", p)

    while True:
        for path in images:
            print("Displaying:", path)

            try:
                img = Image.open(path)
            except Exception as e:
                print("Could not open image:", e)
                continue

            img = prepare_image(img, epd.width, epd.height)
            black, red = convert_to_epaper_layers(img, epd.width, epd.height)

            epd.display(epd.getbuffer(black), epd.getbuffer(red))
            time.sleep(DELAY_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting…")
        try:
            epd7in5b_V2.EPD().sleep()
        except:
            pass
import sys
sys.path.append('/home/pi/e-Paper/RaspberryPi_JetsonNano/python/lib')
#!/usr/bin/env python3
import os
import time
from PIL import Image
from waveshare_epd import epd7in5b_V2

IMG_DIR = "/home/pi/pics"
DELAY_SECONDS = 30  # change images every 30s for testing

def list_images(folder):
    exts = (".png", ".jpg", ".jpeg", ".bmp")
    files = [f for f in os.listdir(folder) if f.lower().endswith(exts)]
    files.sort()
    return [os.path.join(folder, f) for f in files]

def main():
    epd = epd7in5b_V2.EPD()
    epd.init()
    epd.Clear()

    images = list_images(IMG_DIR)
    if not images:
        print("No images found in", IMG_DIR)
        return

    print("Found images:", images)

    while True:
        for path in images:
            print("Displaying:", path)
            img = Image.open(path).convert("1")
            img = img.resize((epd.width, epd.height))

            black = img
            red = Image.new("1", (epd.width, epd.height), 255)

            epd.display(epd.getbuffer(black), epd.getbuffer(red))
            time.sleep(DELAY_SECONDS)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting, putting display to sleep")
        epd7in5b_V2.EPD().sleep()
