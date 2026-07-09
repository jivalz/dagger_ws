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
sudo apt install software-properties-common -y
sudo add-apt-repository universe -y
sudo apt update && sudo apt install curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

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

echo "================================================="
echo "   Installing Python Dependencies"
echo "================================================="

sudo apt install python3-pip -y
pip3 install torch torchvision torchaudio numpy matplotlib

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
