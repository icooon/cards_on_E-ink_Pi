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
DELAY_SECONDS = 3
WIDTH, HEIGHT = 800, 480

# Setup logging
logging.basicConfig(level=logging.INFO)

class DirectBufferEPD(epd7in5b_V2.EPD):
    """Custom EPD class that bypasses automatic clearing"""
    
    def display_direct(self, blackimage, redimage):
        """Display without any clearing - pure ghosting mode"""
        print("📱 Direct buffer write (no clear)...")
        
        # Send black layer data directly
        self.send_command(0x10)  # DATA START TRANSMISSION 1 (black)
        self.send_data2(blackimage)
        
        # Send red layer data directly  
        self.send_command(0x13)  # DATA START TRANSMISSION 2 (red)
        self.send_data2(redimage)
        
        # Trigger display update without clearing
        self.send_command(0x12)  # DISPLAY REFRESH
        self.ReadBusy()
        
        print("✅ Direct buffer write complete")
    
    def maintenance_clear(self):
        """Perform full clear when needed"""
        print("🧹 Performing maintenance clear...")
        self.send_command(0x10)  # Clear black layer
        for _ in range(self.width * self.height // 8):
            self.send_data([0xFF])
        
        self.send_command(0x13)  # Clear red layer
        for _ in range(self.width * self.height // 8):
            self.send_data([0xFF])
            
        self.send_command(0x12)  # DISPLAY REFRESH
        self.ReadBusy()
        print("🧹 Maintenance clear complete")

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
    """Convert to e-ink black/red layers"""
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
    print("🔴 Starting DIRECT BUFFER circle ghosting experiment...")
    print("This bypasses ALL screen clearing for maximum ghosting")
    
    # Initialize custom display
    try:
        epd = DirectBufferEPD()
        print("Initializing direct buffer e-Paper display...")
        epd.init()
        
        # Clear ONLY once at startup
        print("Initial screen clear...")
        epd.Clear()
        
    except Exception as e:
        print(f"Display initialization failed: {e}")
        return
    
    image_count = 0
    maintenance_counter = 0
    
    try:
        while True:
            images = list_images(IMG_DIR)
            if not images:
                print("No images found, waiting...")
                time.sleep(5)
                continue
            
            for img_path in images:
                try:
                    print(f"\\n🔴 Ghost Layer {image_count + 1}: {os.path.basename(img_path)}")
                    
                    # Load and process image
                    img = Image.open(img_path)
                    img = prepare_image(img, WIDTH, HEIGHT)
                    black_layer, red_layer = convert_to_epaper_layers(img, WIDTH, HEIGHT)
                    
                    # Convert for display
                    black_buffer = epd.getbuffer(black_layer)
                    red_buffer = epd.getbuffer(red_layer)
                    
                    # CRITICAL: Use direct buffer method
                    epd.display_direct(black_buffer, red_buffer)
                    
                    image_count += 1
                    maintenance_counter += 1
                    
                    print(f"✅ Ghost layer {image_count} accumulated")
                    
                    # Optional maintenance clear every 25 images
                    if maintenance_counter >= 25:
                        epd.maintenance_clear()
                        maintenance_counter = 0
                        time.sleep(2)
                    
                    time.sleep(DELAY_SECONDS)
                    
                except Exception as e:
                    print(f"Error processing {img_path}: {e}")
                    continue
                    
    except KeyboardInterrupt:
        print("\\n🛑 Direct buffer ghosting experiment stopped")
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