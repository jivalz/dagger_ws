#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from visualization_msgs.msg import Marker
from geometry_msgs.msg import Point
import math

class LidarVisualizerNode(Node):
    def __init__(self):
        super().__init__('lidar_visualizer_node')
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )
        self.publisher_ = self.create_publisher(Marker, '/scan_rays', 10)
        self.get_logger().info('LiDAR Visualizer Node started. Publishing to /scan_rays')

    def scan_callback(self, msg):
        marker = Marker()
        marker.header.frame_id = msg.header.frame_id
        marker.header.stamp = msg.header.stamp
        marker.ns = "lidar_rays"
        marker.id = 0
        marker.type = Marker.LINE_LIST
        marker.action = Marker.ADD
        
        # Make the lines light blue and semi-transparent
        marker.color.r = 0.4
        marker.color.g = 0.8
        marker.color.b = 1.0
        marker.color.a = 0.3
        
        # Thin lines
        marker.scale.x = 0.005
        
        # No pose offset
        marker.pose.orientation.w = 1.0
        
        angle = msg.angle_min
        for r in msg.ranges:
            if math.isfinite(r) and r >= msg.range_min and r <= msg.range_max:
                # Origin point (sensor location)
                p_start = Point()
                p_start.x = 0.0
                p_start.y = 0.0
                p_start.z = 0.0
                
                # End point (obstacle location)
                p_end = Point()
                p_end.x = r * math.cos(angle)
                p_end.y = r * math.sin(angle)
                p_end.z = 0.0
                
                marker.points.append(p_start)
                marker.points.append(p_end)
            
            angle += msg.angle_increment
            
        self.publisher_.publish(marker)

def main(args=None):
    rclpy.init(args=args)
    node = LidarVisualizerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()
