# Interactive Imitation Learning (DAgger) Tutorial

Welcome to the Interactive Imitation Learning tutorial! In this repository, you will learn how to train a self-driving robot using Behavioral Cloning (BC) and subsequently improve it using Dataset Aggregation (DAgger).

## 1. Prerequisites & Setup

This tutorial assumes you already have **ROS 2 Humble** installed on your system. 

First, install Gazebo Classic and the necessary ROS 2 integration packages:
```bash
sudo apt update
sudo apt install gazebo ros-humble-gazebo-ros-pkgs
```

To ensure Gazebo works smoothly and can find its models, add the Gazebo setup script to your `.bashrc`:
```bash
echo "source /usr/share/gazebo/setup.sh" >> ~/.bashrc
source ~/.bashrc
```

## 2. Build the Workspace

Navigate to the workspace and build the packages:
```bash
cd ~/dagger_ws
colcon build
source install/setup.bash
```

---

## 3. Workflow: Behavioral Cloning (BC)

### Step 1: Collect Expert Data
We will first record a baseline dataset of an expert (you!) driving the car around the track.

**Open Terminal 1** (Launch the simulator and data collector):
```bash
cd ~/dagger_ws
source install/setup.bash
ros2 launch controllers record_data_launch.py
```

**Open Terminal 2** (Run the Teleop Keyboard to drive the car):
```bash
cd ~/dagger_ws
source install/setup.bash
ros2 run controllers teleop_keyboard
```
*Use the `W/A/S/D` keys to drive the car around the track safely. The data collector will automatically save `.npz` files in `src/controllers/data/bc_data/`.*

### Step 2: Train the BC Policy
Once you have collected a few laps of good driving data, train the baseline policy using a neural network:
```bash
cd ~/dagger_ws
python3 src/controllers/scripts/train_bc.py
```
*This script will generate `bc_policy.pt` in the `weights` directory.*

### Step 3: Test the BC Policy
Let's see how well your baseline policy performs on its own!
```bash
cd ~/dagger_ws
source install/setup.bash
ros2 launch controllers bc_inference_launch.py
```
*The car will run for a maximum of 3 laps. Notice where it makes mistakes or drives off the track!*

---

## 4. Workflow: DAgger (Dataset Aggregation)

Behavioral Cloning often fails when the car drifts into unfamiliar territory (covariate shift). We will use **DAgger** to interactively intervene and teach the robot how to recover from mistakes.

### Step 4: Collect DAgger Interventions
Launch the interactive DAgger environment:
```bash
cd ~/dagger_ws
source install/setup.bash
ros2 launch controllers dagger_launch.py
```
- A **Tkinter window** will pop up. Make sure to click on it so it has focus!
- The car will begin driving itself using your `bc_policy.pt`. 
- **Intervention**: When you see the car making a mistake, press the **Spacebar**. The mode will switch to `INTERVENTION` (Red). 
- Use the **W/A/S/D** keys to safely steer the car back to the center of the lane.
- Press **Spacebar** again to return control to the AI.
- *Every time you intervene, the corrections are recorded and saved as `intervention_*.npz` files in `src/controllers/data/dagger_data/`.*

### Step 5: Train the DAgger Policy
After collecting several interventions, fine-tune your policy with the new data:
```bash
cd ~/dagger_ws
python3 src/controllers/scripts/train_dagger.py
```
*This will load your existing BC policy and update it using only the intervention data, saving the result as `dagger_policy.pt`.*

### Step 6: Test the Final DAgger Policy
Finally, test your newly improved DAgger policy to see if it learned to recover!
```bash
cd ~/dagger_ws
source install/setup.bash
ros2 launch controllers dagger_inference_launch.py
```
*The car will run for a maximum of 3 laps. You should notice a significant improvement in its ability to stay on the track!*
