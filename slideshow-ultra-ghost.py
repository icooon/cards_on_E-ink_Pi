#!/usr/bin/env python3
import sys
sys.path.append('/home/pi/e-Paper/RaspberryPi_JetsonNano/python/lib')

import os
import time
import logging
from PIL import Image
from waveshare_epd import epd7in5b_V2

# Configuration
IMG_DIR = "/home/pi/pics"
DELAY_SECONDS = 1  # Ultra-fast for maximum ghosting
WIDTH, HEIGHT = 800, 480

class UltraGhostEPD(epd7in5b_V2.EPD):
    """True partial refresh ghosting"""
    
    def init_ghost_mode(self):
        """Initialize for partial refresh mode"""
        print("🔧 Setting up partial refresh ghost mode...")
        self.init_part()  # Use partial refresh initialization
        print("✅ Partial ghost mode ready")
    
    def partial_display(self, image, x_start, y_start, x_end, y_end):
        """Display only a specific region - true partial refresh"""
        print(f"⚡ Partial update: ({x_start},{y_start}) to ({x_end},{y_end})")
        
        # Extract the region from the image
        width = x_end - x_start
        height = y_end - y_start
        
        if width <= 0 or height <= 0:
            return
            
        # Create a cropped buffer for just this region
        region_img = image.crop((x_start, y_start, x_end, y_end))
        region_buffer = self.getbuffer(region_img)
        
        # Use Waveshare's built-in partial display
        self.display_Partial(region_buffer, x_start, y_start, x_end, y_end)
    
    def ghost_display_regions(self, black_layer, red_layer, regions):
        """Display only specific regions for true selective ghosting"""
        for region in regions:
            x_start, y_start, x_end, y_end = region
            
            # Extract region from black layer and display
            region_black = black_layer.crop((x_start, y_start, x_end, y_end))
            region_buffer = self.getbuffer(region_black)
            self.display_Partial(region_buffer, x_start, y_start, x_end, y_end)
            
            print(f"⚡ Updated region: ({x_start},{y_start}) to ({x_end},{y_end})")
    
    def emergency_clear(self):
        """Emergency full clear if display gets too corrupted"""
        print("🚨 Emergency clear - display corruption detected")
        self.Clear()
        time.sleep(3)

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

def convert_to_epaper_layers(img, width, height, preserve_background=False, previous_black=None, previous_red=None):
    """Convert image to e-paper layers with optional selective updates"""
    
    # Handle alpha channel if present
    if img.mode == 'RGBA':
        # Create new layers starting from previous state if available
        if preserve_background and previous_black and previous_red:
            black_layer = previous_black.copy()
            red_layer = previous_red.copy()
        else:
            black_layer = Image.new("1", (width, height), 255)  # White background
            red_layer = Image.new("1", (width, height), 255)
        
        pixels = img.load()
        black_pixels = black_layer.load()
        red_pixels = red_layer.load()
        
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                
                # Skip transparent pixels - preserve background
                if a < 128:  # Semi-transparent threshold
                    continue
                    
                # Only update pixels with content
                if r > 150 and g < 80 and b < 80:  # Red
                    red_pixels[x, y] = 0
                    black_pixels[x, y] = 255  # Clear black at this position
                elif (r + g + b) / 3 < 100:  # Black
                    black_pixels[x, y] = 0
                    red_pixels[x, y] = 255  # Clear red at this position
                else:  # White/light - clear both layers
                    black_pixels[x, y] = 255
                    red_pixels[x, y] = 255
                    
    else:
        # Fallback to RGB mode
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

def detect_content_regions(img, margin=50):
    """Detect regions with actual content (non-transparent areas)"""
    regions = []
    
    if img.mode == 'RGBA':
        # Find bounding boxes of non-transparent content
        pixels = img.load()
        min_x, min_y = img.size
        max_x = max_y = 0
        
        content_found = False
        
        for y in range(img.size[1]):
            for x in range(img.size[0]):
                r, g, b, a = pixels[x, y]
                if a > 128:  # Non-transparent pixel
                    content_found = True
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)
        
        if content_found:
            # Add margin around content
            min_x = max(0, min_x - margin)
            min_y = max(0, min_y - margin)
            max_x = min(img.size[0], max_x + margin)
            max_y = min(img.size[1], max_y + margin)
            
            # Align to 8-pixel boundaries for E-ink
            min_x = (min_x // 8) * 8
            max_x = ((max_x + 7) // 8) * 8
            
            regions.append((min_x, min_y, max_x, max_y))
            print(f"📍 Content region detected: ({min_x},{min_y}) to ({max_x},{max_y})")
    
    return regions

def main():
    print("⚡ PARTIAL REFRESH GHOSTING: True selective updates")
    print("🎯 Using Waveshare display_Partial for real ghosting effects")
    
    try:
        epd = UltraGhostEPD()
        print("Initializing ultra-ghost display...")
        
        # Custom ghost initialization
        epd.init_ghost_mode()
        
        # Single clear at start
        print("Initial clear...")
        epd.Clear()
        
    except Exception as e:
        print(f"Display initialization failed: {e}")
        return
    
    image_count = 0
    previous_black = None
    previous_red = None
    
    try:
        while True:
            images = list_images(IMG_DIR)
            if not images:
                time.sleep(2)
                continue
            
            for img_path in images:
                try:
                    print(f"\\n⚡ Partial Ghost {image_count + 1}: {os.path.basename(img_path)}")
                    
                    img = Image.open(img_path)
                    img = prepare_image(img, WIDTH, HEIGHT)
                    
                    # Detect regions with content for partial refresh
                    content_regions = detect_content_regions(img)
                    
                    if content_regions and image_count > 0:  # Use partial refresh after first image
                        # TRUE PARTIAL REFRESH - only update content regions
                        print(f"🎯 Partial refresh: {len(content_regions)} regions")
                        
                        # Convert the full image for region extraction
                        black_layer, red_layer = convert_to_epaper_layers(img, WIDTH, HEIGHT)
                        
                        # Update only the content regions
                        epd.ghost_display_regions(black_layer, red_layer, content_regions)
                        
                        update_type = "partial"
                        
                    else:
                        # Full display for first image or fallback
                        print("🖼️  Full display (first image or no content detected)")
                        black_layer, red_layer = convert_to_epaper_layers(img, WIDTH, HEIGHT)
                        black_buffer = epd.getbuffer(black_layer)
                        red_buffer = epd.getbuffer(red_layer)
                        epd.display(black_buffer, red_buffer)
                        
                        update_type = "full"
                    
                    image_count += 1
                    print(f"⚡ Ghost {image_count} - {update_type} update")
                    
                    # Emergency clear less frequently for partial mode
                    if image_count % 100 == 0:
                        print("🚨 Reset display after 100 partials")
                        epd.emergency_clear()
                        # Reinit partial mode
                        epd.init_ghost_mode()
                    
                    time.sleep(DELAY_SECONDS)
                    
                except Exception as e:
                    print(f"Error: {e}")
                    continue
                    
    except KeyboardInterrupt:
        print("\\n🛑 Ultra-ghost experiment stopped")
    finally:
        try:
            epd.sleep()
        except:
            pass

if __name__ == "__main__":
    main()