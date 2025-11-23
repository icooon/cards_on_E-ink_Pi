#!/usr/bin/env python3
import sys
sys.path.append('/home/pi/e-Paper/RaspberryPi_JetsonNano/python/lib')

import os
import time
from PIL import Image, ImageDraw
from waveshare_epd import epd7in5b_V2

# Configuration
IMG_DIR = "/home/pi/pics"
DELAY_SECONDS = 3
WIDTH, HEIGHT = 800, 480

class MemoryCanvasGhosting:
    """
    Brilliant Memory Canvas Approach:
    - Maintains accumulated image state in software memory
    - Each new circle is overlaid onto master canvas
    - Display always shows complete accumulated effect
    - True ghosting without relying on hardware memory
    """
    
    def __init__(self):
        # Master canvases that accumulate all content
        self.master_black = Image.new("1", (WIDTH, HEIGHT), 255)  # White background
        self.master_red = Image.new("1", (WIDTH, HEIGHT), 255)    # White background
        self.layer_count = 0
        
    def clear_canvas(self):
        """Clear the master canvases - like clearing the display memory"""
        print("🧹 Clearing memory canvas...")
        self.master_black = Image.new("1", (WIDTH, HEIGHT), 255)
        self.master_red = Image.new("1", (WIDTH, HEIGHT), 255)
        self.layer_count = 0
        
    def overlay_image_on_canvas(self, img_path):
        """Overlay new image onto the accumulated master canvas"""
        print(f"🎨 Overlaying onto memory canvas: {os.path.basename(img_path)}")
        
        # Load new image
        new_img = Image.open(img_path)
        if new_img.height > new_img.width:
            new_img = new_img.rotate(-90, expand=True)
        new_img = new_img.resize((WIDTH, HEIGHT))
        
        # Convert new image to layers
        new_black, new_red = self.convert_to_layers(new_img)
        
        # CRITICAL: Overlay onto master canvases (not replace!)
        self.master_black = self.overlay_layers(self.master_black, new_black)
        self.master_red = self.overlay_layers(self.master_red, new_red)
        
        self.layer_count += 1
        print(f"✅ Canvas now has {self.layer_count} accumulated layers")
        
        return self.master_black, self.master_red
    
    def overlay_layers(self, base_layer, new_layer):
        """Overlay new layer onto base layer - preserves existing content"""
        result = base_layer.copy()
        base_pixels = result.load()
        new_pixels = new_layer.load()
        
        for y in range(HEIGHT):
            for x in range(WIDTH):
                # If new layer has content (0 = black/red), use it
                # Otherwise keep existing base layer content
                if new_pixels[x, y] == 0:  # New content
                    base_pixels[x, y] = 0
                # If new_pixels[x, y] == 255 (white/transparent), keep base_pixels[x, y]
        
        return result
    
    def convert_to_layers(self, img):
        """Convert image to black and red layers"""
        img_rgb = img.convert("RGB")
        
        black_layer = Image.new("1", (WIDTH, HEIGHT), 255)
        red_layer = Image.new("1", (WIDTH, HEIGHT), 255)
        
        pixels = img_rgb.load()
        black_pixels = black_layer.load()
        red_pixels = red_layer.load()
        
        for y in range(HEIGHT):
            for x in range(WIDTH):
                r, g, b = pixels[x, y]
                
                # Red detection
                if r > 150 and g < 80 and b < 80:
                    red_pixels[x, y] = 0
                # Black detection  
                elif (r + g + b) / 3 < 100:
                    black_pixels[x, y] = 0
                # White stays white (255)
        
        return black_layer, red_layer

def list_images(folder):
    exts = (".png", ".jpg", ".jpeg", ".bmp")
    if not os.path.isdir(folder):
        return []
    files = [f for f in os.listdir(folder) if f.lower().endswith(exts)]
    files.sort()
    return [os.path.join(folder, f) for f in files]

def main():
    print("🧠 MEMORY CANVAS GHOSTING - Brilliant Software Memory Effect")
    print("🎭 Each image overlays onto accumulated master canvas")
    print("✨ Display shows complete layered effect with every refresh")
    
    # Initialize display
    try:
        epd = epd7in5b_V2.EPD()
        epd.init()
        epd.Clear()  # Clear once at startup
        print("🖥️  Display initialized and cleared")
    except Exception as e:
        print(f"Display initialization failed: {e}")
        return
    
    # Initialize memory canvas system
    canvas = MemoryCanvasGhosting()
    
    try:
        while True:
            images = list_images(IMG_DIR)
            if not images:
                print("No images found, waiting...")
                time.sleep(5)
                continue
            
            for img_path in images:
                try:
                    print(f"\n🎨 Memory Layer {canvas.layer_count + 1}")
                    
                    # Overlay new image onto accumulated canvas
                    master_black, master_red = canvas.overlay_image_on_canvas(img_path)
                    
                    # Display the COMPLETE accumulated canvas
                    print("📺 Displaying accumulated memory canvas...")
                    epd.display(epd.getbuffer(master_black), epd.getbuffer(master_red))
                    
                    print(f"✅ Memory effect: {canvas.layer_count} layers accumulated")
                    
                    # Reset canvas every 20 layers to prevent overcrowding
                    if canvas.layer_count >= 20:
                        print("\n🔄 Canvas getting full - clearing for fresh start")
                        canvas.clear_canvas()
                        epd.Clear()  # Clear display too
                    
                    time.sleep(DELAY_SECONDS)
                    
                except Exception as e:
                    print(f"Error processing {img_path}: {e}")
                    continue
                    
    except KeyboardInterrupt:
        print("\n🛑 Memory canvas ghosting stopped")
    finally:
        try:
            epd.sleep()
        except:
            pass

if __name__ == "__main__":
    main()