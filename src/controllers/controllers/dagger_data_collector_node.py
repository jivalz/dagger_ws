#!/usr/bin/env python3
import os
import math
import numpy as np
import glob

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool

def quat_to_yaw(q):
    siny = 2.0 * (q.w * q.z + q.x * q.y)
    cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny, cosy)

class DaggerDataCollectorNode(Node):
    def __init__(self):
        super().__init__('dagger_data_collector')
        self.declare_parameter('data_dir', '')
        
        ws = os.path.expanduser('~/dagger_ws/src/controllers')
        data_dir = os.path.join(ws, 'data', 'dagger_data')
        os.makedirs(data_dir, exist_ok=True)
        self.data_dir = data_dir

        self.latest_scan = None
        self.latest_odom = None
        self.latest_cmd = Twist()
        self.intervention_active = False

        self.create_subscription(LaserScan, '/scan', self.scan_cb, 10)
        self.create_subscription(Odometry, '/odom', self.odom_cb, 10)
        self.create_subscription(Twist, '/cmd_vel', self.cmd_cb, 10)
        self.create_subscription(Bool, '/intervention_active', self.intervention_cb, 10)

        self.buffer = {
            'timestamps': [], 'scans': [], 'poses': [], 
            'opp_poses': [], 'velocities': [], 'actions': []
        }
        self.interventions_saved = self._count_existing_files()

        self.create_timer(0.05, self.record_tick)

        self.get_logger().info(f'DAgger Data Collector ready. Saving to {self.data_dir}')
        self.get_logger().info(f'Existing interventions: {self.interventions_saved}')

    def _count_existing_files(self):
        return len(glob.glob(os.path.join(self.data_dir, 'intervention_*.npz')))

    def scan_cb(self, msg: LaserScan):
        self.latest_scan = msg

    def odom_cb(self, msg: Odometry):
        self.latest_odom = msg

    def cmd_cb(self, msg: Twist):
        self.latest_cmd = msg

    def intervention_cb(self, msg: Bool):
        was_active = self.intervention_active
        self.intervention_active = msg.data
        
        if was_active and not self.intervention_active:
            self._save_data()

    def record_tick(self):
        if not self.intervention_active:
            return

        if self.latest_scan is None or self.latest_odom is None:
            return

        t = self.get_clock().now().nanoseconds / 1e9
        odom = self.latest_odom

        ranges = np.array(self.latest_scan.ranges, dtype=np.float32)
        if len(ranges) == 360:
            ranges = ranges[::1]  # Downsample 1080 -> 360
        max_r = self.latest_scan.range_max
        ranges = np.where(np.isfinite(ranges), ranges, max_r)

        px = odom.pose.pose.position.x
        py = odom.pose.pose.position.y
        yaw = quat_to_yaw(odom.pose.pose.orientation)
        
        vx = odom.twist.twist.linear.x
        vy = odom.twist.twist.linear.y
        wz = odom.twist.twist.angular.z

        ax = self.latest_cmd.linear.x
        az = self.latest_cmd.angular.z

        self.buffer['timestamps'].append(t)
        self.buffer['scans'].append(ranges)
        self.buffer['poses'].append([px, py, yaw])
        self.buffer['opp_poses'].append([0.0, 0.0, 0.0])
        self.buffer['velocities'].append([vx, vy, wz])
        self.buffer['actions'].append([ax, az])

    def _save_data(self):
        if len(self.buffer['timestamps']) < 10:
            self.get_logger().warn('Too few samples — skipping save')
            self._reset_buffer()
            return

        self.interventions_saved += 1
        fname = os.path.join(self.data_dir, f'intervention_{self.interventions_saved:03d}.npz')
        np.savez_compressed(
            fname,
            timestamps=np.array(self.buffer['timestamps']),
            scans=np.array(self.buffer['scans']),
            poses=np.array(self.buffer['poses']),
            opp_poses=np.array(self.buffer['opp_poses']),
            velocities=np.array(self.buffer['velocities']),
            actions=np.array(self.buffer['actions']),
            lap_time=np.array(0.0),
            expert_id=np.array(999),
        )
        self.get_logger().info(f'💾 Saved {fname} ({len(self.buffer["timestamps"])} samples)')
        self._reset_buffer()

    def _reset_buffer(self):
        for k in self.buffer:
            self.buffer[k] = []

def main(args=None):
    rclpy.init(args=args)
    node = DaggerDataCollectorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.try_shutdown()

if __name__ == '__main__':
    main()
