#!/usr/bin/env python3
import sys
sys.path.append('/home/pi/e-Paper/RaspberryPi_JetsonNano/python/lib')

import os
import time
from PIL import Image
from waveshare_epd import epd7in5b_V2

# Configuration
IMG_DIR = "/home/pi/pics"
DELAY_SECONDS = 3
WIDTH, HEIGHT = 800, 480

class MemoryPartialEPD(epd7in5b_V2.EPD):
    """Memory Canvas + True Partial Refresh = No white flashing"""
    
    def init_partial_mode(self):
        """Initialize for partial refresh only"""
        print("🔧 Setting up partial refresh mode...")
        self.init_part()  # Use Waveshare's partial refresh init
        print("✅ Partial refresh mode ready")
    
    def partial_update_region(self, image, x_start, y_start, x_end, y_end):
        """Update only specific region - NO full screen refresh"""
        print(f"⚡ Partial update: ({x_start},{y_start}) to ({x_end},{y_end})")
        
        # Align to 8-pixel boundaries (e-ink requirement)
        x_start = (x_start // 8) * 8
        x_end = ((x_end + 7) // 8) * 8
        
        # Extract region
        width = x_end - x_start
        height = y_end - y_start
        
        if width <= 0 or height <= 0:
            return
            
        # Crop image to region
        region_img = image.crop((x_start, y_start, x_end, y_end))
        
        # Use Waveshare's partial display
        self.display_Partial(self.getbuffer(region_img), x_start, y_start, x_end, y_end)

class MemoryCanvasPartial:
    """Memory Canvas + Partial Refresh = Perfect Ghosting"""
    
    def __init__(self):
        self.master_black = Image.new("1", (WIDTH, HEIGHT), 255)  # White
        self.master_red = Image.new("1", (WIDTH, HEIGHT), 255)    # White
        self.layer_count = 0
        
    def add_circle_and_get_region(self, img_path):
        """Add circle to canvas and return only the changed region"""
        print(f"🎨 Adding circle to canvas: {os.path.basename(img_path)}")
        
        # Load new image
        new_img = Image.open(img_path)
        if new_img.height > new_img.width:
            new_img = new_img.rotate(-90, expand=True)
        new_img = new_img.resize((WIDTH, HEIGHT))
        
        # Find content region in new image (where circles are)
        content_region = self.find_content_region(new_img)
        if not content_region:
            return None, None, None
        
        x_start, y_start, x_end, y_end = content_region
        
        # Convert new image to layers
        new_black, new_red = self.convert_to_layers(new_img)
        
        # Overlay onto master canvas
        self.master_black = self.overlay_layers(self.master_black, new_black)
        self.master_red = self.overlay_layers(self.master_red, new_red)
        
        self.layer_count += 1
        print(f"✅ Canvas has {self.layer_count} layers, updating region: ({x_start},{y_start}) to ({x_end},{y_end})")
        
        # Return only the changed region from master canvas
        region_black = self.master_black.crop((x_start, y_start, x_end, y_end))
        
        return region_black, x_start, y_start, x_end, y_end
    
    def find_content_region(self, img):
        """Find bounding box of non-transparent content"""
        if img.mode != 'RGBA':
            return None
            
        pixels = img.load()
        min_x, min_y = WIDTH, HEIGHT
        max_x = max_y = 0
        found_content = False
        
        for y in range(HEIGHT):
            for x in range(WIDTH):
                r, g, b, a = pixels[x, y]
                if a > 128:  # Non-transparent
                    found_content = True
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)
        
        if not found_content:
            return None
            
        # Add margin and align to 8-pixel boundaries
        margin = 20
        min_x = max(0, (min_x - margin) // 8 * 8)
        max_x = min(WIDTH, ((max_x + margin + 7) // 8) * 8)
        min_y = max(0, min_y - margin)
        max_y = min(HEIGHT, max_y + margin)
        
        return (min_x, min_y, max_x, max_y)
    
    def overlay_layers(self, base_layer, new_layer):
        """Overlay new layer onto base - preserves existing content"""
        result = base_layer.copy()
        base_pixels = result.load()
        new_pixels = new_layer.load()
        
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if new_pixels[x, y] == 0:  # New content
                    base_pixels[x, y] = 0
        
        return result
    
    def convert_to_layers(self, img):
        """Convert to e-ink layers with PERFECT transparency preservation"""
        print(f"🎨 Converting with transparency preservation...")
        
        # Ensure we're working with RGBA
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        black_layer = Image.new("1", (WIDTH, HEIGHT), 255)  # White background
        red_layer = Image.new("1", (WIDTH, HEIGHT), 255)    # White background
        
        # Access pixel data directly
        img_pixels = img.load()
        black_pixels = black_layer.load()
        red_pixels = red_layer.load()
        
        circles_found = 0
        
        for y in range(HEIGHT):
            for x in range(WIDTH):
                r, g, b, a = img_pixels[x, y]
                
                # CRITICAL: Only process NON-TRANSPARENT pixels
                if a < 128:  # Transparent - skip completely
                    continue
                
                # Process opaque pixels to preserve circular shape
                if r > 150 and g < 80 and b < 80:  # Red circle
                    red_pixels[x, y] = 0  # Show red
                    circles_found += 1
                elif (r + g + b) / 3 < 100:  # Black circle  
                    black_pixels[x, y] = 0  # Show black
                    circles_found += 1
                # Transparent areas stay white (255)
        
        print(f"✅ Preserved circular shape: {circles_found} circle pixels processed")
        return black_layer, red_layer

def list_images(folder):
    exts = (".png", ".jpg", ".jpeg", ".bmp")
    if not os.path.isdir(folder):
        return []
    files = [f for f in os.listdir(folder) if f.lower().endswith(exts)]
    files.sort()
    return [os.path.join(folder, f) for f in files]

def main():
    print("🎯 MEMORY CANVAS + PARTIAL REFRESH = NO WHITE FLASHING")
    print("🧠 Memory: Circles accumulate in software")  
    print("⚡ Partial: Only update circle regions - no full refresh")
    
    # Initialize display
    try:
        epd = MemoryPartialEPD()
        epd.init()
        epd.Clear()  # Clear once
        
        # Switch to partial refresh mode
        epd.init_partial_mode()
        print("🖥️  Display ready for partial updates")
        
    except Exception as e:
        print(f"Display initialization failed: {e}")
        return
    
    # Initialize memory canvas
    canvas = MemoryCanvasPartial()
    
    try:
        while True:
            images = list_images(IMG_DIR)
            if not images:
                print("No images found, waiting...")
                time.sleep(5)
                continue
            
            for img_path in images:
                try:
                    print(f"\n⚡ Partial Layer {canvas.layer_count + 1}")
                    
                    # Add circle to canvas and get changed region
                    region_img, x_start, y_start, x_end, y_end = canvas.add_circle_and_get_region(img_path)
                    
                    if region_img is None:
                        print("No content found in image")
                        continue
                    
                    # Update ONLY the circle region - NO full screen refresh!
                    print("📺 Partial update - NO WHITE FLASH!")
                    epd.partial_update_region(region_img, x_start, y_start, x_end, y_end)
                    
                    print(f"✅ Circle added with partial refresh - {canvas.layer_count} layers total")
                    
                    # Reset every 15 layers to prevent overcrowding
                    if canvas.layer_count >= 15:
                        print("\n🔄 Resetting canvas...")
                        canvas = MemoryCanvasPartial()
                        epd.Clear()  # Full clear
                        epd.init_partial_mode()  # Back to partial mode
                    
                    time.sleep(DELAY_SECONDS)
                    
                except Exception as e:
                    print(f"Error: {e}")
                    continue
                    
    except KeyboardInterrupt:
        print("\n🛑 Memory partial ghosting stopped")
    finally:
        try:
            epd.sleep()
        except:
            pass

if __name__ == "__main__":
    main()