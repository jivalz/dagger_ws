import os
import sys
import numpy as np
import torch

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool

sys.path.insert(0, os.path.expanduser('~/dagger_ws/src/controllers'))
from scripts.policy_network import PolicyNetwork


class DaggerInferenceNode(Node):
    def __init__(self):
        super().__init__('dagger_inference')
        self.declare_parameter('weights_path', '')
        self.declare_parameter('max_range', 3.5)
        self.declare_parameter('rate', 20.0)

        weights = self.get_parameter('weights_path').value
        if not weights:
            weights = os.path.expanduser(
                '~/dagger_ws/src/controllers/weights/dagger_policy.pt'
            )
        self.max_range = self.get_parameter('max_range').value

        self.model = PolicyNetwork(input_dim=360, output_dim=2)
        if os.path.exists(weights):
            self.model.load_state_dict(torch.load(weights, map_location='cpu'))
            self.model.eval()
            self.get_logger().info(f'Loaded dagger policy: {weights}')
        else:
            self.get_logger().error(f'No weights at {weights}')
            return

        self.latest_scan = None
        self.done = False
        self.create_subscription(LaserScan, '/scan', self.scan_cb, 10)
        self.create_subscription(Bool, '/done', self._done_cb, 10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        rate = self.get_parameter('rate').value
        self.create_timer(1.0 / rate, self.infer_tick)
        self.get_logger().info(f'Dagger inference running at {rate}Hz')

    def scan_cb(self, msg: LaserScan):
        self.latest_scan = msg

    def _done_cb(self, msg: Bool):
        if msg.data:
            self.done = True

    def infer_tick(self):
        if self.done:
            self.cmd_pub.publish(Twist())
            return
        if self.latest_scan is None:
            return

        ranges = np.array(self.latest_scan.ranges, dtype=np.float32)
        if len(ranges) == 360:
            ranges = ranges[::1]  # Downsample from 1080 to 360
        ranges = np.where(np.isfinite(ranges), ranges, self.max_range)
        ranges = np.clip(ranges / self.max_range, 0.0, 1.0)

        action = self.model.predict(ranges)

        cmd = Twist()
        cmd.linear.x = float(action[0])
        cmd.angular.z = float(action[1])
        self.cmd_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = DaggerInferenceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
