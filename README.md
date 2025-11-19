# Cards on E-Ink Pi

This project turns a Raspberry Pi + Waveshare **7.5" E-Paper HAT (B)**  
(black/white/red, 800×480) into an auto-running **generative art frame** that creates dynamic 3D cube scenes with dithered gradients.

## Features

🎨 **Generative 3D Art** - Creates random 3D cube scenes with spheres  
⚡ **Fast Generation** - 100-200ms generation time using optimized Canvas rendering  
🌈 **Rich Gradients** - White highlights, red lighting, black shadows with smooth transitions  
🔲 **Dithering Effects** - Bayer matrix dithering converts gradients to beautiful stippled patterns  
🔄 **Auto-Cycling** - New scenes every 30 seconds via systemd service  
📱 **Remote Generation** - Generate new art via SSH or locally on Pi  

## Quick Start

1. **Clone and setup:**
```bash
git clone https://github.com/icooon/cards_on_E-ink_Pi.git
cd cards_on_E-ink_Pi
```

2. **Generate art locally:**
```bash
npm install
npm run generate-simple    # Fast generation
npm run dev-simple         # Generate + deploy to Pi
```

3. **Or generate directly on Pi:**
```bash
ssh pi@YOUR_PI_IP
node generate-rich-3d.js   # Rich 3D gradients
```

---

## Hardware

- Raspberry Pi (with WiFi + SPI)
- Waveshare 7.5" E-Paper HAT (B) – tri-color (red/black/white)
- 40-pin GPIO connection
- Power supply for the Pi

---

## Software Components

### Core Files
- `slideshow-fast-dither.py` – main slideshow with Bayer matrix dithering
- `generate-rich-3d.js` – Node.js 3D scene generator (Pi-optimized)
- `generate-simple.js` – Local development generator  
- `systemd/epaper-frame.service` – systemd unit to auto-run the slideshow
- `package.json` - Node.js dependencies for visual generation
- `requirements.txt` – Python dependencies (Pillow, numpy)

### Generation Scripts
- `generate-rich-3d.js` - Rich 3D scenes with deep gradients (for Pi)
- `generate-simple.js` - Fast local generation (for development)
- `generate.js` - Original Puppeteer-based generator (slower)

### Display Scripts  
- `slideshow-fast-dither.py` - Fast Bayer matrix dithering (recommended)
- `slideshow-floyd.py` - Floyd-Steinberg dithering (slower, higher quality)
- `slideshow.py` - Original basic conversion

### External Dependencies
- Waveshare e-Paper driver from their repo (not included in this repo):
  - https://github.com/waveshare/e-Paper

On the Pi, the driver is expected at:

```text
/home/pi/e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd
```

---

## Installation

### On Raspberry Pi

1. **Install Waveshare e-Paper library:**
```bash
cd ~
git clone https://github.com/waveshare/e-Paper
```

2. **Install system dependencies:**
```bash
sudo apt update
sudo apt install python3-pip nodejs npm
pip3 install Pillow numpy
```

3. **Clone this project:**
```bash
git clone https://github.com/icooon/cards_on_E-ink_Pi.git
cd cards_on_E-ink_Pi
```

4. **Install Node.js dependencies:**
```bash
npm install canvas jsdom
```

5. **Set up systemd service:**
```bash
sudo cp systemd/epaper-frame.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable epaper-frame.service
```

### Local Development

1. **Clone and install:**
```bash
git clone https://github.com/icooon/cards_on_E-ink_Pi.git
cd cards_on_E-ink_Pi
npm install
```

2. **Update Pi IP in deploy.js:**
```javascript
const PI_IP = 'YOUR_PI_IP_ADDRESS';
```

---

## Usage

### Generate Art

**On Pi (recommended for best quality):**
```bash
ssh pi@YOUR_PI_IP
cd cards_on_E-ink_Pi
node generate-rich-3d.js    # Single rich 3D scene
```

**Locally with deployment:**
```bash
npm run generate-simple     # Generate locally
npm run deploy              # Deploy to Pi  
npm run dev-simple          # Generate + deploy
```

### Control Display

**Start/stop slideshow:**
```bash
sudo systemctl start epaper-frame.service   # Start
sudo systemctl stop epaper-frame.service    # Stop
sudo systemctl status epaper-frame.service  # Check status
```

**View logs:**
```bash
sudo journalctl -u epaper-frame.service -f  # Follow logs
```

### Configuration

- **Image directory:** `/home/pi/pics`
- **Display interval:** 30 seconds (configurable in slideshow scripts)
- **Dithering algorithm:** Bayer 4x4 matrix (fast) or Floyd-Steinberg (slower)

---

## Generated Art Examples

The system creates:
- **3D cube compositions** with random sizes, positions, and rotations
- **Spherical objects** with radial gradients  
- **Complex lighting** - red directional light + white top light
- **Rich gradients** - White highlights → Red lighting → Black shadows
- **Dithered conversion** - Smooth gradients become beautiful stippled patterns

Each image is unique with 5-35 objects arranged in 3D space.

---

## Performance

- **Generation time:** 100-200ms per image (Pi 4)
- **Dithering conversion:** ~2-3 seconds per image  
- **Memory usage:** ~50MB during generation
- **Storage:** ~50-100KB per generated PNG

---

## Technical Details

### Dithering Algorithms

1. **Bayer Matrix (default)** - Fast ordered dithering using 4x4 pattern
2. **Floyd-Steinberg** - Higher quality error diffusion (slower)

### Color Conversion

Input gradients → 3-color palette (Black: #000000, White: #FFFFFF, Red: #FF0000) → Dithering patterns

### 3D Rendering

- **Canvas 2D API** for fast software rendering
- **Gradient lighting simulation** with multiple color stops  
- **3D cube projection** with separate face gradients
- **Depth sorting** for proper overlapping
