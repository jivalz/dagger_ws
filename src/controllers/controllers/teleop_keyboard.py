import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import tkinter as tk

msg = """
Reading from the keyboard and Publishing to Twist!
---------------------------
IMPORTANT: Click on this window to focus it!
Then, use standard WASD keys.
You CAN hold multiple keys at once.

W/S : move forward/backward
A/D : turn left/right

Close this window or CTRL-C in terminal to quit.
"""

class TeleopKeyboard(Node):
    def __init__(self):
        super().__init__('teleop_keyboard')
        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)
        self.speed = 3.0
        self.turn = 1.5
        
        self.pressed = {
            'w': False,
            'a': False,
            's': False,
            'd': False
        }

        self.root = tk.Tk()
        self.root.title("Teleop WASD")
        self.root.geometry("350x200")
        
        label = tk.Label(self.root, text=msg, justify=tk.LEFT, font=("Courier", 10))
        label.pack(padx=10, pady=10)

        self.root.bind('<KeyPress>', self.on_press)
        self.root.bind('<KeyRelease>', self.on_release)
        
        self.timer = self.create_timer(0.05, self.timer_callback)
        self.get_logger().info("Tkinter window opened. Click it to focus!")

    def on_press(self, event):
        char = event.keysym.lower()
        if char in self.pressed:
            self.pressed[char] = True

    def on_release(self, event):
        char = event.keysym.lower()
        if char in self.pressed:
            self.pressed[char] = False

    def timer_callback(self):
        x = 0.0
        th = 0.0

        if self.pressed['w']:
            x = 1.0
        elif self.pressed['s']:
            x = -1.0
            
        if self.pressed['a']:
            th = 1.0
        elif self.pressed['d']:
            th = -1.0
            
        twist = Twist()
        twist.linear.x = x * self.speed
        twist.linear.y = 0.0
        twist.linear.z = 0.0
        twist.angular.x = 0.0
        twist.angular.y = 0.0
        twist.angular.z = th * self.turn
        self.publisher_.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    node = TeleopKeyboard()
    try:
        while rclpy.ok():
            try:
                node.root.update()
            except tk.TclError:
                break # Window was closed
            rclpy.spin_once(node, timeout_sec=0.01)
    except KeyboardInterrupt:
        pass
    finally:
        # Publish stop message before quitting
        twist = Twist()
        twist.linear.x = 0.0
        twist.angular.z = 0.0
        node.publisher_.publish(twist)
        
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()
