# Cards on E-Ink Pi

This project turns a Raspberry Pi + Waveshare **7.5" E-Paper HAT (B)**  
(black/white/red, 800×480) into an auto-running tri-color image frame.

- Loads images from `/home/pi/pics`
- Auto-rotates portrait images to fit a horizontal screen
- Converts full-color images into **black / white / red** layers
- Can auto-start on boot via `systemd`

---

## Hardware

- Raspberry Pi (with WiFi + SPI)
- Waveshare 7.5" E-Paper HAT (B) – tri-color (red/black/white)
- 40-pin GPIO connection
- Power supply for the Pi

---

## Software Components

- `slideshow.py` – main slideshow script
- `systemd/epaper-frame.service` – systemd unit to auto-run the slideshow
- `requirements.txt` – Python dependencies (Pillow)
- Waveshare e-Paper driver from their repo (not included in this repo):
  - https://github.com/waveshare/e-Paper

On the Pi, the driver is expected at:

```text
/home/pi/e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd
