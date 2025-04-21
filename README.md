# 🎶 Now-playing

**Now-playing** is a Python application for the Raspberry Pi that listens for background music, identifies the
song, and displays the song information on an e-ink display.

> This project was born out of a personal need: I love listening to vinyl, but since it's analog, I could never see what
> track was playing. The same goes for films—I'd often reach for my phone to Shazam a song. Now, I just glance at my
> display. Simple.

## 🚀 Features

- Detects music using a
  local [YAMNet](https://www.kaggle.com/models/google/yamnet/tensorFlow2/yamnet/1?tfhub-redirect=true) ML model
- When music is detected, identifies the song with [ShazamIO](https://github.com/shazamio/ShazamIO)
- Displays song title, artist, and album cover on an e-ink display
- Pressing Button A on the e-ink display adds the current song to a Spotify playlist
  with [Spotipy](https://spotipy.readthedocs.io/en/2.25.1/)
- When no music is detected for a while, the display switches to a screensaver mode that shows the weather

## ✨ What's New?

This project builds on and refactors several previous works (see [LICENSE](./LICENSE)):

- [spotipi-eink (original)](https://github.com/ryanwa18/spotipi-eink)
- [spotipi-eink (fork)](https://github.com/Gabbajoe/spotipi-eink)
- [shazampi-eink (fork)](https://github.com/ravi72munde/shazampi-eink)

All credits for the original idea go to them. While they laid the groundwork, this version focuses on clean code,
modularity, and extensibility.

### Improvements

- Simplified, readable logic with meaningful function names
- Clear separation of concerns with dedicated services (e.g., `DisplayService` has all logic concerning the e-ink
  display)
- Application state is handled via a centralized `StateManager`
- Type hints added for better clarity and IDE support
- Configurations via YAML (no more messy INI files)
- Cleaned up setup script for smoother installation
- Singleton pattern for `Logging` and `Config`
- Threaded button control for responsiveness
- Many more...

## 📦 Installation & Setup

### 🔧 Required Hardware

- [Raspberry Pi Zero 2 W](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/) *(or newer)*
- [MicroSD card](https://www.raspberrypi.com/products/sd-cards/)
- Power supply
- Pimoroni Inky Impression e-ink display
    - [Pimoroni Inky Impression 4"](https://shop.pimoroni.com/products/inky-impression-4?variant=39599238807635)
    - [Pimoroni Inky Impression 5.7"](https://shop.pimoroni.com/products/inky-impression-5-7?variant=32298701324371)
    - [Pimoroni Inky Impression 7.3"](https://shop.pimoroni.com/products/inky-impression-7-3?variant=55186435244411)
- [USB microphone](https://www.amazon.com.be/microphone-portable-enregistrement-vid%C3%A9oconf%C3%A9rences-n%C3%A9cessaire/dp/B09PVPPRF2?source=ps-sl-shoppingads-lpcontext&ref_=fplfs&ref_=fplfs&psc=1&smid=A3HYZLWFA5CWB0&gQT=1)
  *(min. 16kHz sample rate)*
- Optional: [3D printed case](https://github.com/scripsi/inky-impression-case)

### 🥧 Raspberry Pi OS

1. Flash Raspberry Pi OS Lite to your microSD card
   using [Raspberry Pi Imager](https://www.raspberrypi.com/documentation/computers/getting-started.html#installing-the-operating-system)
2. Enable Wi-Fi and SSH (to allow remote access as the OS is headless) in the setup wizard

### 🔐 Required Credentials

#### 🌦️ OpenWeatherMap API

1. Sign up at [OpenWeatherMap](https://openweathermap.org/)
2. Generate your API key
3. Safely store it
4. Go to [Google Maps](https://www.google.com/maps) → Search your location → Right-click → Copy coordinates

#### 🎵 Spotify API

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click 'Create App' and fill out the form:
    1. App name
    2. App description
    3. Redirect URI = http://localhost:8888/callback
    4. Check 'Web API'
    5. Check the 'Terms of Service'
3. Click on 'Save'
4. Safely store your Client ID and Client Secret
5. [Copy the Playlist ID](https://clients.caster.fm/knowledgebase/110/How-to-find-Spotify-playlist-ID.html#:~:text=To%20find%20the%20Spotify%20playlist,Link%22%20under%20the%20Share%20menu.&text=The%20playlist%20id%20is%20the,after%20playlist%2F%20as%20marked%20above.)
   of the playlist you want your songs to be added to

#### 🎟 Spotify Access Token

Since Raspberry Pi OS Lite is headless (no browser), you must authorize Spotify once from a computer:

1. On your PC or Mac, clone this repo:

```bash 
  git clone https://github.com/maurocastermans/now-playing
  cd now-playing
```

2. Fill in your `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` in `spotify_auth_helper.py`
3. Run:

```bash
  python3 spotify_auth_helper.py
```

4. Follow the browser prompt and allow access to your Spotify account. This will generate a .cache file locally
   containing a Spotify access token.

### ⚙️ Installation Script

#### 📥 Download and Run

```bash
  wget https://raw.githubusercontent.com/maurocastermans/now-playing/main/setup.sh
  chmod +x setup.sh
  bash ./setup.sh
```

Afterwards, copy the .cache file to your Raspberry Pi project root. Spotipy will refresh the token automatically using
the stored refresh token—no need to do this again unless you change accounts.

Should you encounter any issues, check [Known Issues](#-known-issues)

#### 🧙 What the Script Does

- Enables SPI and I2C
- Updates the system and installs dependencies
- Sets up a Python virtual environment and installs Python packages
- Creates config, log, and resources directories
- Prompts for credentials, your e-ink display size and generates config.yaml
- Copies and configures a systemd service to autostart on boot
- Starts the now-playing service

#### 📂 Resulting Config Structure

```yaml
display:
  width: 600 # or 640 (4"), or 800 (7.3")
  height: 448 # or 400 (4"), or 480 (7.3")
  small_album_cover: true
  small_album_cover_px: 250 # or 200 (4"), or 300 (7.3")
  screensaver_image: "resources/default.jpg"
  font_path: "resources/CircularStd-Bold.otf"
  font_size_title: 45
  font_size_subtitle: 35
  offset_left_px: 20
  offset_right_px: 20
  offset_top_px: 0
  offset_bottom_px: 20
  offset_text_shadow_px: 4

weather:
  openweathermap_api_key: "YOUR_API_KEY"
  geo_coordinates: "LAT,LON"

spotify:
  client_id: "YOUR_SPOTIFY_CLIENT_ID"
  client_secret: "YOUR_SPOTIFY_CLIENT_SECRET"
  playlist_id: "YOUR_SPOTIFY_PLAYLIST_ID"

log:
  log_file_path: "log/now_playing.log"
```

## 🛠 Useful Commands

### 📝 Edit Configuration

To update your configuration after installation:

```bash
  nano config/config.yaml
```

After editing, restart the service to apply changes:

```bash
  sudo systemctl restart now-playing.service
```

### 🔁 Systemd Service

- Check status:

```bash
  sudo systemctl status now-playing.service
```

- Start/Stop:

```bash
  sudo systemctl stop now-playing.service
  sudo systemctl start now-playing.service
```

- Logs:

```bash
  journalctl -u now-playing.service
  journalctl -u now-playing.service --follow
  journalctl -u now-playing.service --since today
  journalctl -u now-playing.service -b
```

### 🧪 Manual Python Execution

Now-playing runs in a Python virtual environment (using venv). If you want to run Python code manually:

```bash
  sudo systemctl stop now-playing.service
  source venv/bin/activate
  python3 src/now_playing.py
```

To leave the virtual environment:

```bash
  deactivate
```

## 🐛 Known Issues

### Low USB Microphone Gain

Some USB microphones have very low default input gain, meaning they only pick up sound when your audio device is
extremely close to the mic. This can cause issues with audio detection.

To boost your microphone’s gain:

1. Open the audio mixer:

```bash
    alsamixer
```

2. Select your USB microphone:
    1. Press F6 to open the sound card list
    2. Use the arrow keys to select your USB microphone device
3. Adjust the input gain:
    1. Press F4 to switch to Capture controls
    2. Increase the gain using the ↑ arrow key until it reaches an appropriate level
4. Save the gain settings (so they persist after reboot):

```bash
  sudo alsactl store
```

### GPIO Chip Conflict

If you see:

```
Woah there, some pins we need are in use!
     Chip Select: (line 8, GPIO8) currently claimed by spi0 CS0
```

Just recently (16/08/2024), the GPIO Kernel Module in Raspberry PI OS changed

➡️ Check https://github.com/pimoroni/inky?tab=readme-ov-file#chip-select-line-8-gpio8-currently-claimed-by-spi0-cs0 and
follow the instructions




