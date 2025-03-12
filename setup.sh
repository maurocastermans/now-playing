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

# Install Python 3.9 if not already installed
# This step is necessary because the inky pip package depends on a version of Rumba for which Python <3.11 is required
# Although their documentation says the package is Python 3.11 supported...
# Can take an hour or so to install
# Can't use apt repository ppa:deadsnakes/ppa because we're on a Raspberry Pi
echo "==> Checking if Python 3.9 is already installed..."
if python3.9 --version &>/dev/null; then
    echo "✔ Python 3.9 is already installed."
else
    echo "==> Installing Python3.9..."
    sudo apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev
    cd ~/Downloads
    wget https://www.python.org/ftp/python/3.9.19/Python-3.9.19.tgz
    sudo tar zxf Python-3.9.19.tgz
    cd Python-3.9.19
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
echo "✔ Current working directory: ${install_path}"

echo "==> Setting up a Python virtual environment..."
python3.9 -m venv --system-site-packages venv && echo "✔ Python virtual environment created."
echo "Activating the virtual environment..."
source ${install_path}/venv/bin/activate && echo "✔ Virtual environment activated."

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
read openweathermap_api_key
echo "Enter your location coordinates in the 'latitude,longitude' format:"
read geo_coordinates

echo "==> Setting up the configuration in config.yaml..."
cat <<EOF > ${install_path}/config/config.yaml
display:
  width: 600
  height: 448
  album_cover_small_px: 250
  album_cover_small: true
  display_refresh_counter: 20
  no_song_cover: "${install_path}/resources/default.jpg"
  font_path: "${install_path}/resources/CircularStd-Bold.otf"
  font_size_title: 45
  font_size_artist: 35
  offset_px_left: 20
  offset_px_right: 20
  offset_px_top: 0
  offset_px_bottom: 20
  offset_text_px_shadow: 4
  text_direction: "bottom-up"
  background_mode: "fit"

weather:
  openweathermap_api_key: "${openweathermap_api_key}"
  geo_coordinates: "${geo_coordinates}"

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
    echo "✔ Old systemd service removed."
fi
UID_TO_USE=$(id -u)
GID_TO_USE=$(id -g)

sudo cp "${install_path}/now-playing.service" /etc/systemd/system/
sudo sed -i -e "/\[Service\]/a ExecStart=${install_path}/venv/bin/python3 ${install_path}/src/now_playing.py" /etc/systemd/system/now-playing.service
sudo sed -i -e "/ExecStart/a WorkingDirectory=${install_path}" /etc/systemd/system/now-playing.service
sudo sed -i -e "/RestartSec/a User=${UID_TO_USE}" /etc/systemd/system/now-playing.service
sudo sed -i -e "/User/a Group=${GID_TO_USE}" /etc/systemd/system/now-playing.service

sudo systemctl daemon-reload
sudo systemctl start now-playing-display
sudo systemctl enable now-playing-display
echo "✔ now-playing-display systemd service installed and started."

echo "🎉 Setup is complete! Your now-playing display is configured."
