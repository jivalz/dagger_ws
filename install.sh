#!/bin/bash
set -e

echo "================================================="
echo "   Installing ROS 2 Humble & Dependencies"
echo "================================================="

# 1. Setup Locale
sudo apt update && sudo apt install locales -y
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# 2. Add ROS 2 repository
if [ ! -f /etc/apt/sources.list.d/ros2.list ]; then
    sudo apt install software-properties-common -y
    sudo add-apt-repository universe -y
    sudo apt update && sudo apt install curl -y
    sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
else
    echo "ROS 2 repository already exists. Skipping repository setup."
fi

# 3. Install ROS 2 and Build Tools
sudo apt update
sudo apt install ros-humble-desktop python3-colcon-common-extensions -y

# 4. Add ROS 2 sourcing to bashrc
if ! grep -q "source /opt/ros/humble/setup.bash" ~/.bashrc; then
    echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
    echo "Added ROS 2 to ~/.bashrc"
fi

echo "================================================="
echo "   Installing Gazebo Classic"
echo "================================================="

sudo apt install gazebo ros-humble-gazebo-ros-pkgs -y

if ! grep -q "source /usr/share/gazebo/setup.sh" ~/.bashrc; then
    echo "source /usr/share/gazebo/setup.sh" >> ~/.bashrc
    echo "Added Gazebo to ~/.bashrc"
fi

# 5. Install Python Dependencies
echo "================================================="
echo "   Installing Python Dependencies"
echo "================================================="

sudo apt install python3-pip python3-venv -y

echo "It is recommended to use a virtual environment for heavy Python packages like PyTorch."
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Active virtual environment detected ($VIRTUAL_ENV)."
    read -p "Do you want to install PyTorch and other dependencies in this venv? (y/n): " INSTALL_PYTHON_DEPS
    if [[ "$INSTALL_PYTHON_DEPS" =~ ^[Yy]$ ]]; then
        pip install torch torchvision torchaudio numpy matplotlib
    else
        echo "Skipping Python dependencies installation."
    fi
else
    read -p "Do you want to install PyTorch and other dependencies system-wide? This may take a while. (y/n): " INSTALL_PYTHON_DEPS
    if [[ "$INSTALL_PYTHON_DEPS" =~ ^[Yy]$ ]]; then
        pip3 install torch torchvision torchaudio numpy matplotlib
    else
        echo "Skipping Python dependencies installation."
        echo "You can install them later inside a venv using: pip install torch torchvision torchaudio numpy matplotlib"
    fi
fi

echo "================================================="
echo "   Cloning the Workspace"
echo "================================================="

cd ~
if [ ! -d "dagger_ws" ]; then
    git clone https://github.com/jivalz/dagger_ws.git
    echo "Repository cloned successfully into ~/dagger_ws"
else
    echo "Directory ~/dagger_ws already exists! Skipping clone."
fi

echo "================================================="
echo "   Installation Complete!"
echo "   Please close this terminal and open a new one,"
echo "   then navigate to ~/dagger_ws and run:"
echo "   colcon build"
echo "================================================="
