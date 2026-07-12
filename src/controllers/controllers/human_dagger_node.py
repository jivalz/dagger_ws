#!/usr/bin/env python3
import os
import math
import numpy as np
import torch
import tkinter as tk
import sys
import glob

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool

sys.path.insert(0, os.path.expanduser('~/dagger_ws/src/controllers'))
from scripts.policy_network import PolicyNetwork

def quat_to_yaw(q):
    siny = 2.0 * (q.w * q.z + q.x * q.y)
    cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny, cosy)

class HumanDaggerNode(Node):
    def __init__(self):
        super().__init__('human_dagger_node')
        self.declare_parameter('weights_path', '')
        self.declare_parameter('max_range', 3.5)
        self.declare_parameter('rate', 20.0)
        self.declare_parameter('data_dir', '')

        weights = self.get_parameter('weights_path').value
        if not weights:
            weights = os.path.expanduser('~/dagger_ws/src/controllers/weights/bc_policy.pt')
        self.max_range = self.get_parameter('max_range').value

        ws = os.path.expanduser('~/dagger_ws/src/controllers')
        data_dir = os.path.join(ws, 'data', 'dagger_data')
        os.makedirs(data_dir, exist_ok=True)
        self.data_dir = data_dir

        self.model = PolicyNetwork(input_dim=360, output_dim=2)
        if os.path.exists(weights):
            self.model.load_state_dict(torch.load(weights, map_location='cpu'))
            self.model.eval()
            self.get_logger().info(f'Loaded BC policy: {weights}')
        else:
            self.get_logger().error(f'No weights at {weights}')
            sys.exit(1)

        self.latest_scan = None
        self.latest_odom = None

        self.create_subscription(LaserScan, '/scan', self.scan_cb, 10)
        self.create_subscription(Odometry, '/odom', self.odom_cb, 10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.intervention_pub = self.create_publisher(Bool, '/intervention_active', 10)

        self.speed = 3.0
        self.turn = 1.5
        
        self.pressed = {'w': False, 'a': False, 's': False, 'd': False}
        self.intervention_mode = False

        self.root = tk.Tk()
        self.root.title("Human DAgger")
        self.root.geometry("400x250")
        
        self.lbl_mode = tk.Label(self.root, text="Mode: POLICY", fg="green", font=("Helvetica", 16, "bold"))
        self.lbl_mode.pack(pady=10)
        
        msg = "Press SPACE to toggle Intervention.\nUse W/A/S/D to drive during Intervention."
        tk.Label(self.root, text=msg, font=("Courier", 10)).pack(pady=10)

        self.root.bind('<KeyPress>', self.on_press)
        self.root.bind('<KeyRelease>', self.on_release)
        
        rate = self.get_parameter('rate').value
        self.create_timer(1.0 / rate, self.timer_callback)
        self.get_logger().info("Tkinter window opened. Click to focus!")

    def scan_cb(self, msg: LaserScan):
        self.latest_scan = msg

    def odom_cb(self, msg: Odometry):
        self.latest_odom = msg

    def on_press(self, event):
        if event.keysym != 'space':
            char = event.keysym.lower()
            if char in self.pressed:
                self.pressed[char] = True

    def on_release(self, event):
        if event.keysym == 'space':
            self.intervention_mode = not self.intervention_mode
            
            msg = Bool()
            msg.data = self.intervention_mode
            self.intervention_pub.publish(msg)

            if self.intervention_mode:
                self.lbl_mode.config(text="Mode: INTERVENTION", fg="red")
                self.get_logger().info("Intervention STARTED.")
            else:
                self.lbl_mode.config(text="Mode: POLICY", fg="green")
                self.get_logger().info("Intervention ENDED.")
                
        else:
            char = event.keysym.lower()
            if char in self.pressed:
                self.pressed[char] = False

    def timer_callback(self):
        if self.latest_scan is None or self.latest_odom is None:
            return

        ranges = np.array(self.latest_scan.ranges, dtype=np.float32)
        if len(ranges) == 360:
            ranges = ranges[::1]  # Downsample 1080 -> 360
        max_r = self.latest_scan.range_max
        ranges = np.where(np.isfinite(ranges), ranges, max_r)
        
        cmd = Twist()
        action_x = 0.0
        action_z = 0.0

        if self.intervention_mode:
            # Human control
            if self.pressed['w']: action_x = 1.0 * self.speed
            elif self.pressed['s']: action_x = -1.0 * self.speed
                
            if self.pressed['a']: action_z = 1.0 * self.turn
            elif self.pressed['d']: action_z = -1.0 * self.turn
            
            cmd.linear.x = float(action_x)
            cmd.angular.z = float(action_z)
            self.cmd_pub.publish(cmd)
            
        else:
            # Policy control
            ranges_norm = np.clip(ranges / self.max_range, 0.0, 1.0)
            action = self.model.predict(ranges_norm)
            cmd.linear.x = float(action[0])
            cmd.angular.z = float(action[1])
            self.cmd_pub.publish(cmd)

def main(args=None):
    rclpy.init(args=args)
    node = HumanDaggerNode()
    try:
        while rclpy.ok():
            try:
                node.root.update()
            except tk.TclError:
                break # Window closed
            rclpy.spin_once(node, timeout_sec=0.01)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()
