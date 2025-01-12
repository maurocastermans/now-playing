#!/bin/bash

# Ensure the script is not run as root
if [[ $EUID -eq 0 ]]; then
  echo "Error: This script must NOT be run as root. Please run it as a regular user." >&2
  exit 1
fi

# Check if SPI is enabled on the Raspberry Pi
echo "==> Checking if SPI interface is enabled..."
if [[ -e /dev/spidev0.0 ]] || [[ -e /dev/spidev0.1 ]]; then
    echo "✔ SPI is enabled."
else
    echo "✘ SPI is not enabled. Please enable SPI using raspi-config and try again." >&2
    exit 1
fi

# Add deadsnakes to be able to get older Python versions
echo "==> Adding deadsnakes repository..."
sudo apt-get install python3-launchpadlib
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y

# Update package lists to ensure the system has the latest repository information
echo "==> Updating package lists..."
sudo apt update && echo "✔ Package lists updated successfully."
echo

# Upgrade all packages to the latest versions
echo "==> Upgrading system packages to the latest versions..."
sudo apt upgrade -y && echo "✔ System packages upgraded successfully."
echo

echo "==> Installing python3.10..."
sudo apt-get install python3.10
echo

# Install required system dependencies
echo "==> Installing required system dependencies..."
sudo apt-get install python3.10-venv python3.10-distutils python3-numpy git libopenjp2-7 libportaudio2 -y \
  && echo "✔ System dependencies installed successfully."
echo

# Remove any existing installation of the now-playing project
if [ -d "now-playing" ]; then
    echo "==> Found an existing installation of now-playing. Removing it..."
    sudo rm -rf now-playing && echo "✔ Old installation removed."
fi
echo

# Clone the now-playing project from GitHub
echo "==> Cloning the now-playing project from GitHub..."
git clone https://github.com/maurocastermans/now-playing && echo "✔ Project cloned successfully."
echo "Switching to the installation directory."
cd now-playing || exit
install_path=$(pwd)
echo "✔ Current working directory: ${install_path}"
echo

# Set up a Python virtual environment for the project
echo "==> Setting up a Python virtual environment..."
python3.10 -m venv --system-site-packages venv && echo "✔ Python virtual environment created."
echo "Activating the virtual environment..."
source ${install_path}/venv/bin/activate && echo "✔ Virtual environment activated."

# Upgrade pip explicitly for Python 3.10
echo "==> Upgrading pip in the virtual environment..."
pip install --upgrade pip && echo "✔ Pip upgraded successfully."

# Install the required Python packages from the project's requirements file
echo "==> Installing required Python packages..."
pip3 install -r requirements.txt --upgrade && echo "✔ Python packages installed successfully."
echo

# Create required directories for configuration and resources
echo "==> Setting up configuration and resources directories..."
if ! [ -d "${install_path}/config" ]; then
    echo "Creating config directory..."
    mkdir -p "${install_path}/config" && echo "✔ Config directory created."
fi
if ! [ -d "${install_path}/resources" ]; then
    echo "Creating resources directory..."
    mkdir -p "${install_path}/resources" && echo "✔ Resources directory created."
fi
echo

# Configure e-ink display settings
echo "==> Configuring display settings..."
echo "[DEFAULT]" >> ${install_path}/config/eink_options.ini
echo "width = 600" >> ${install_path}/config/eink_options.ini
echo "height = 448" >> ${install_path}/config/eink_options.ini
echo "album_cover_small_px = 250" >> ${install_path}/config/eink_options.ini
echo "model = inky" >> ${install_path}/config/eink_options.ini
echo "✔ Display configured for Pimoroni Inky Impression 5.7 (600x448)."
echo

# Add default configuration entries
echo "==> Adding default configuration entries..."
echo "; disable smaller album cover set to False" >> ${install_path}/config/eink_options.ini
echo "; if disabled top offset is still calculated like as the following:" >> ${install_path}/config/eink_options.ini
echo "; offset_px_top + album_cover_small_px" >> ${install_path}/config/eink_options.ini
echo "album_cover_small = True" >> ${install_path}/config/eink_options.ini
echo "; cleans the display every 20 picture" >> ${install_path}/config/eink_options.ini
echo "; this takes ~60 seconds" >> ${install_path}/config/eink_options.ini
echo "display_refresh_counter = 20" >> ${install_path}/config/eink_options.ini
echo "now_playing_log = ${install_path}/log/now_playing.log" >> ${install_path}/config/eink_options.ini
echo "no_song_cover = ${install_path}/resources/default.jpg" >> ${install_path}/config/eink_options.ini
echo "font_path = ${install_path}/resources/CircularStd-Bold.otf" >> ${install_path}/config/eink_options.ini
echo "font_size_title = 45" >> ${install_path}/config/eink_options.ini
echo "font_size_artist = 35" >> ${install_path}/config/eink_options.ini
echo "offset_px_left = 20" >> ${install_path}/config/eink_options.ini
echo "offset_px_right = 20" >> ${install_path}/config/eink_options.ini
echo "offset_px_top = 0" >> ${install_path}/config/eink_options.ini
echo "offset_px_bottom = 20" >> ${install_path}/config/eink_options.ini
echo "offset_text_px_shadow = 4" >> ${install_path}/config/eink_options.ini
echo "; text_direction possible values: top-down or bottom-up" >> ${install_path}/config/eink_options.ini
echo "text_direction = bottom-up" >> ${install_path}/config/eink_options.ini
echo "; possible modes are fit or repeat" >> ${install_path}/config/eink_options.ini
echo "background_mode = fit" >> ${install_path}/config/eink_options.ini
echo "✔ Default configuration added to eink_options.ini."
echo

# Prompt the user to set up the weather API
echo "==> Setting up the Weather API..."
echo "Please enter your OpenWeatherMap API key:"
read openweathermap_api_key
echo "Enter your location coordinates in the 'latitude,longitude' format:"
read geo_coordinates
echo "openweathermap_api_key = ${openweathermap_api_key}" >> ${install_path}/config/eink_options.ini
echo "geo_coordinates = ${geo_coordinates}" >> ${install_path}/config/eink_options.ini
echo "units = metric"  >> ${install_path}/config/eink_options.ini
echo "✔ Weather API configuration completed."
echo

# Set up the log directory
echo "==> Ensuring the log directory exists..."
if ! [ -d "${install_path}/log" ]; then
    mkdir "${install_path}/log" && echo "✔ Log directory created."
else
    echo "✔ Log directory already exists."
fi
echo

# Install and configure the now-playing-display systemd service
echo "==> Setting up the now-playing-display service..."
if [ -f "/etc/systemd/system/now-playing-display.service" ]; then
    echo "Removing old now-playing-display service..."
    sudo systemctl stop now-playing-display
    sudo systemctl disable now-playing-display
    sudo rm -rf /etc/systemd/system/now-playing-display.*
    sudo systemctl daemon-reload
    echo "✔ Old service removed."
fi
# Add new service
UID_TO_USE=$(id -u)
GID_TO_USE=$(id -g)
sudo cp "${install_path}/setup/service_template/now-playing-display.service" /etc/systemd/system/
sudo sed -i -e "/\[Service\]/a ExecStart=${install_path}/venv/bin/python3 ${install_path}/python/now_playing.py" /etc/systemd/system/now-playing-display.service
sudo sed -i -e "/ExecStart/a WorkingDirectory=${install_path}" /etc/systemd/system/now-playing-display.service
sudo sed -i -e "/EnvironmentFile/a User=${UID_TO_USE}" /etc/systemd/system/now-playing-display.service
sudo sed -i -e "/User/a Group=${GID_TO_USE}" /etc/systemd/system/now-playing-display.service
sudo mkdir -p /etc/systemd/system/now-playing-display.service.d
now_playing_env_path=/etc/systemd/system/now-playing-display.service.d/now-playing-display_env.conf
sudo touch $now_playing_env_path
echo "[Service]" | sudo tee -a $now_playing_env_path > /dev/null
sudo systemctl daemon-reload
sudo systemctl start now-playing-display
sudo systemctl enable now-playing-display
echo "✔ now-playing-display service installed and started."
echo

echo "🎉 Setup is complete! Your now-playing display is configured."
