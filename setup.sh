#!/bin/bash

if [[ $EUID -eq 0 ]]; then
  echo "Error: This script must NOT be run as root. Please run it as a regular user." >&2
  exit 1
fi

echo "==> Enabling SPI..."
sudo raspi-config nonint do_spi 0 && echo "✔ SPI is enabled."

echo "==> Enabling I2C..."
sudo raspi-config nonint do_i2c 0 && echo "✔ I2C is enabled."

echo "==> Updating package lists..."
sudo apt update && echo "✔ Package lists updated successfully."

echo "==> Upgrading system packages to the latest versions..."
sudo apt upgrade -y && echo "✔ System packages upgraded successfully."

# WORKAROUND: Install Python version 3.9
# Necessary because the inky pip package depends on a version of Rumba for which Python <3.11 is only supported
# We can't use apt repository ppa:deadsnakes/ppa to install Python because we're on a Raspberry Pi
# Can take an hour or so to install
echo "==> Checking if Python 3.9 is already installed..."
if python3.9 --version &>/dev/null; then
    echo "✔ Python 3.9 is already installed."
else
    echo "==> Installing Python3.9..."
    sudo apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev
    wget https://www.python.org/ftp/python/3.9.19/Python-3.9.19.tgz
    sudo tar zxf Python-3.9.19.tgz
    cd Python-3.9.19 || exit 1
    sudo ./configure --enable-optimizations
    sudo make -j 4
    sudo make altinstall
    echo "✔ Python 3.9 installed successfully."
fi

echo "==> Installing required system dependencies..."
sudo apt-get install python3-numpy git libopenjp2-7 libportaudio2 -y \
  && echo "✔ System dependencies installed successfully."

if [ -d "now-playing" ]; then
    echo "==> Found an existing installation of now-playing. Removing it..."
    sudo rm -rf now-playing && echo "✔ Old installation removed."
fi

echo "==> Cloning the now-playing project from GitHub..."
git clone https://github.com/maurocastermans/now-playing && echo "✔ Project cloned successfully."
echo "Switching to the installation directory."
cd now-playing || exit
install_path=$(pwd)

echo "==> Setting up a Python virtual environment..."
python3.9 -m venv --system-site-packages venv && echo "✔ Python virtual environment created."
echo "Activating the virtual environment..."
source "${install_path}/venv/bin/activate" && echo "✔ Virtual environment activated."

echo "==> Upgrading pip in the virtual environment..."
pip install --upgrade pip && echo "✔ Pip upgraded successfully."

echo "==> Installing required Python packages..."
pip3 install -r requirements.txt --upgrade && echo "✔ Python packages installed successfully."

echo "==> Setting up configuration, resources and log directories..."
if ! [ -d "${install_path}/config" ]; then
    echo "Creating config directory..."
    mkdir -p "${install_path}/config" && echo "✔ Config directory created."
fi
if ! [ -d "${install_path}/resources" ]; then
    echo "Creating resources directory..."
    mkdir -p "${install_path}/resources" && echo "✔ Resources directory created."
fi
if ! [ -d "${install_path}/log" ]; then
    echo "Creating log directory..."
    mkdir -p "${install_path}/log" && echo "✔ Log directory created."
fi

echo "==> Setting up the Weather API..."
echo "Please enter your OpenWeatherMap API key:"
read -r openweathermap_api_key
echo "Enter your location coordinates in the 'latitude,longitude' format:"
read -r geo_coordinates

echo "==> Setting up the Spotify API..."
echo "Please enter your Spotify client ID:"
read -r spotify_client_id
echo "Please enter your Spotify client secret:"
read -r spotify_client_secret
echo "Please enter your Spotify playlist ID:"
read -r spotify_playlist_id

echo "==> Setting up the configuration in config.yaml..."
echo "Select your Inky Impression display size:"
echo "1) 4.0 inch"
echo "2) 5.7 inch"
echo "3) 7.3 inch"
read -r -p "Enter choice (1/2/3): " display_size_choice

case $display_size_choice in
  1)
    display_width=640
    display_height=400
    album_cover_size=200
    ;;
  2)
    display_width=600
    display_height=448
    album_cover_size=250
    ;;
  3)
    display_width=800
    display_height=480
    album_cover_size=300
    ;;
  *)
    echo "Invalid choice. Defaulting to 5.7 inch settings."
    display_width=600
    display_height=448
    album_cover_size=250
    ;;
esac

cat <<EOF > "${install_path}/config/config.yaml"
display:
  width: $display_width
  height: $display_height
  small_album_cover: true
  small_album_cover_px: $album_cover_size
  screensaver_image: "${install_path}/resources/default.jpg"
  font_path: "${install_path}/resources/CircularStd-Bold.otf"
  font_size_title: 45
  font_size_subtitle: 35
  offset_left_px: 20
  offset_right_px: 20
  offset_top_px: 0
  offset_bottom_px: 20
  offset_text_shadow_px: 4

weather:
  openweathermap_api_key: "${openweathermap_api_key}"
  geo_coordinates: "${geo_coordinates}"

spotify:
  client_id: "${spotify_client_id}"
  client_secret: "${spotify_client_secret}"
  playlist_id: ${spotify_playlist_id}

log:
  log_file_path: "${install_path}/log/now_playing.log"

EOF
echo "✔ Configuration file created at ${install_path}/config/config.yaml."

echo "==> Setting up the now-playing systemd service..."
if [ -f "/etc/systemd/system/now-playing.service" ]; then
    echo "Removing old now-playing systemd service..."
    sudo systemctl stop now-playing
    sudo systemctl disable now-playing
    sudo rm -rf /etc/systemd/system/now-playing.*
    sudo systemctl daemon-reload
    echo "✔ Old now-playing systemd service removed."
fi
sudo cp "${install_path}/now-playing.service" /etc/systemd/system/
sudo sed -i -e "/\[Service\]/a ExecStart=${install_path}/venv/bin/python3 ${install_path}/src/now_playing.py" /etc/systemd/system/now-playing.service
sudo sed -i -e "/ExecStart/a WorkingDirectory=${install_path}" /etc/systemd/system/now-playing.service
sudo sed -i -e "/RestartSec/a User=$(id -u)" /etc/systemd/system/now-playing.service
sudo sed -i -e "/User/a Group=$(id -g)" /etc/systemd/system/now-playing.service

sudo systemctl daemon-reload
sudo systemctl start now-playing
sudo systemctl enable now-playing
echo "✔ now-playing systemd service installed and started."

echo "🎉 Setup is complete! Your now-playing display is configured."
