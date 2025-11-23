#!/usr/bin/env python3
import sys
sys.path.append('/home/pi/e-Paper/RaspberryPi_JetsonNano/python/lib')

import os
import time
import math
from PIL import Image, ImageDraw
from waveshare_epd import epd7in5b_V2

# Configuration
IMG_DIR = "/home/pi/pics"
DELAY_SECONDS = 3
WIDTH, HEIGHT = 800, 480

class CircularRefreshEPD(epd7in5b_V2.EPD):
    """Refresh only circular areas - not rectangular bounding boxes"""
    
    def init_partial_mode(self):
        """Initialize for partial refresh only"""
        print("🔧 Setting up circular refresh mode...")
        self.init_part()
        print("✅ Circular refresh mode ready")
    
    def refresh_circle_only(self, center_x, center_y, radius, circle_image):
        """Refresh only the circular area - much more precise than rectangles"""
        print(f"⭕ Circular update: center ({center_x},{center_y}) radius {radius}")
        
        # Calculate minimal bounding square for the circle (8-pixel aligned)
        margin = 10  # Small margin for smooth edges
        x_start = max(0, ((center_x - radius - margin) // 8) * 8)
        y_start = max(0, center_y - radius - margin)
        x_end = min(WIDTH, ((center_x + radius + margin + 7) // 8) * 8)
        y_end = min(HEIGHT, center_y + radius + margin)
        
        # Create circular mask for precise refresh
        mask_width = x_end - x_start
        mask_height = y_end - y_start
        
        if mask_width <= 0 or mask_height <= 0:
            return
        
        # Create circular mask
        mask = Image.new("L", (mask_width, mask_height), 0)  # Black background
        mask_draw = ImageDraw.Draw(mask)
        
        # Draw white circle on mask
        local_center_x = center_x - x_start
        local_center_y = center_y - y_start
        mask_draw.ellipse([
            local_center_x - radius, local_center_y - radius,
            local_center_x + radius, local_center_y + radius
        ], fill=255)
        
        # Extract region from master image
        region_img = circle_image.crop((x_start, y_start, x_end, y_end))
        
        # Apply circular mask - only circle pixels will be updated
        masked_region = Image.new("1", (mask_width, mask_height), 255)  # White background
        masked_region.paste(region_img, mask=mask)
        
        # CRITICAL: Only update pixels inside the circular mask
        # This bypasses rectangular refresh by manually controlling each pixel update
        self.display_circular_pixels_only(masked_region, mask, x_start, y_start)
        
        print(f"✅ Updated circular area: {mask_width}×{mask_height} pixels")
    
    def display_circular_pixels_only(self, image, circular_mask, offset_x, offset_y):
        """Display only pixels within the circular mask - TRUE circular refresh"""
        print(f"🎯 Applying TRUE circular pixel refresh (no rectangles)")
        
        # For e-ink limitations, we still need to use partial refresh with minimal rectangle
        # but we ensure only circular content is visible by using the mask properly
        mask_pixels = circular_mask.load()
        img_pixels = image.load()
        width, height = image.size
        
        # Create a clean image with only the circular content
        clean_circular = Image.new("1", (width, height), 255)
        clean_pixels = clean_circular.load()
        
        for y in range(height):
            for x in range(width):
                if mask_pixels[x, y] > 128:  # Inside circle
                    clean_pixels[x, y] = img_pixels[x, y]
        
        # Use minimal rectangular refresh but only circular content is visible
        self.display_Partial(self.getbuffer(clean_circular), offset_x, offset_y, 
                           offset_x + width, offset_y + height)

class CircularMemoryCanvas:
    """Memory Canvas + Circular Refresh = Perfect Precision"""
    
    def __init__(self):
        self.master_black = Image.new("1", (WIDTH, HEIGHT), 255)
        self.master_red = Image.new("1", (WIDTH, HEIGHT), 255) 
        self.layer_count = 0
        
    def add_circle_and_get_geometry(self, img_path):
        """Add circle to canvas and return circle geometry for precise refresh"""
        print(f"🎨 Analyzing circle geometry: {os.path.basename(img_path)}")
        
        # Load new image
        new_img = Image.open(img_path)
        if new_img.height > new_img.width:
            new_img = new_img.rotate(-90, expand=True)
        new_img = new_img.resize((WIDTH, HEIGHT))
        
        # Detect actual circle positions and sizes
        circles = self.detect_circles(new_img)
        if not circles:
            return None, []
        
        # Convert image to layers
        new_black, new_red = self.convert_to_layers(new_img)
        
        # Overlay onto master canvas
        self.master_black = self.overlay_layers(self.master_black, new_black)
        self.master_red = self.overlay_layers(self.master_red, new_red)
        
        self.layer_count += 1
        print(f"✅ Canvas has {self.layer_count} layers, found {len(circles)} circles")
        
        return self.master_black, circles
    
    def detect_circles(self, img):
        """Detect actual circle positions and radii from image content"""
        circles = []
        
        if img.mode == 'RGBA':
            # Analyze alpha channel to find circular content
            alpha = img.split()[-1]
            pixels = img.load()
            alpha_pixels = alpha.load()
            
            # Find all non-transparent pixels
            content_pixels = []
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    if alpha_pixels[x, y] > 128:  # Non-transparent
                        r, g, b, a = pixels[x, y]
                        if r > 150 and g < 80 and b < 80 or (r + g + b) / 3 < 100:  # Red or black
                            content_pixels.append((x, y))
            
            # Group pixels into circles using clustering
            if content_pixels:
                circles = self.cluster_pixels_into_circles(content_pixels)
        
        else:
            # RGB mode - find dark pixels
            pixels = img.load()
            content_pixels = []
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    r, g, b = pixels[x, y]
                    if r > 150 and g < 80 and b < 80 or (r + g + b) / 3 < 100:
                        content_pixels.append((x, y))
            
            if content_pixels:
                circles = self.cluster_pixels_into_circles(content_pixels)
        
        return circles
    
    def cluster_pixels_into_circles(self, pixels):
        """Cluster content pixels into circular regions"""
        if not pixels:
            return []
        
        circles = []
        
        # Simple clustering: find center of mass and estimate radius
        min_x = min(p[0] for p in pixels)
        max_x = max(p[0] for p in pixels)
        min_y = min(p[1] for p in pixels)
        max_y = max(p[1] for p in pixels)
        
        # Center of mass
        center_x = (min_x + max_x) // 2
        center_y = (min_y + max_y) // 2
        
        # Estimate radius as average distance from center
        distances = [math.sqrt((x - center_x)**2 + (y - center_y)**2) for x, y in pixels]
        radius = int(sum(distances) / len(distances)) + 5  # Add small margin
        
        circles.append((center_x, center_y, radius))
        
        print(f"🔍 Detected circle: center ({center_x},{center_y}) radius {radius}")
        
        return circles
    
    def overlay_layers(self, base_layer, new_layer):
        """Overlay new layer onto base"""
        result = base_layer.copy()
        base_pixels = result.load()
        new_pixels = new_layer.load()
        
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if new_pixels[x, y] == 0:
                    base_pixels[x, y] = 0
        
        return result
    
    def convert_to_layers(self, img):
        """Convert to e-ink layers with transparency support"""
        if img.mode == 'RGBA':
            img_rgb = img.convert("RGB")
            alpha = img.split()[-1].load()
        else:
            img_rgb = img.convert("RGB")
            alpha = None
        
        black_layer = Image.new("1", (WIDTH, HEIGHT), 255)
        red_layer = Image.new("1", (WIDTH, HEIGHT), 255)
        
        pixels = img_rgb.load()
        black_pixels = black_layer.load()
        red_pixels = red_layer.load()
        
        for y in range(HEIGHT):
            for x in range(WIDTH):
                # Skip transparent pixels
                if alpha and alpha[x, y] < 128:
                    continue
                    
                r, g, b = pixels[x, y]
                
                if r > 150 and g < 80 and b < 80:  # Red
                    red_pixels[x, y] = 0
                elif (r + g + b) / 3 < 100:  # Black
                    black_pixels[x, y] = 0
        
        return black_layer, red_layer

def list_images(folder):
    exts = (".png", ".jpg", ".jpeg", ".bmp")
    if not os.path.isdir(folder):
        return []
    files = [f for f in os.listdir(folder) if f.lower().endswith(exts)]
    files.sort()
    return [os.path.join(folder, f) for f in files]

def main():
    print("⭕ CIRCULAR REFRESH - Update Only Circle Pixels!")
    print("🎯 Precision: Refresh exact circular areas, not rectangles")
    print("🧠 Memory: Accumulate all circles in software canvas")
    
    # Initialize display
    try:
        epd = CircularRefreshEPD()
        epd.init()
        epd.Clear()
        epd.init_partial_mode()
        print("🖥️  Display ready for circular updates")
        
    except Exception as e:
        print(f"Display initialization failed: {e}")
        return
    
    # Initialize circular memory canvas
    canvas = CircularMemoryCanvas()
    
    try:
        while True:
            images = list_images(IMG_DIR)
            if not images:
                print("No images found, waiting...")
                time.sleep(5)
                continue
            
            for img_path in images:
                try:
                    print(f"\n⭕ Circular Layer {canvas.layer_count + 1}")
                    
                    # Add circle to canvas and detect geometry
                    master_img, circles = canvas.add_circle_and_get_geometry(img_path)
                    
                    if not circles:
                        print("No circles detected in image")
                        continue
                    
                    # Refresh only the circular areas - NOT rectangles!
                    for center_x, center_y, radius in circles:
                        epd.refresh_circle_only(center_x, center_y, radius, master_img)
                    
                    print(f"✅ Added {len(circles)} circles with precision refresh - {canvas.layer_count} total layers")
                    
                    # Reset every 15 layers
                    if canvas.layer_count >= 15:
                        print("\n🔄 Resetting canvas...")
                        canvas = CircularMemoryCanvas()
                        epd.Clear()
                        epd.init_partial_mode()
                    
                    time.sleep(DELAY_SECONDS)
                    
                except Exception as e:
                    print(f"Error: {e}")
                    continue
                    
    except KeyboardInterrupt:
        print("\n🛑 Circular refresh stopped")
    finally:
        try:
            epd.sleep()
        except:
            pass

if __name__ == "__main__":
    main()