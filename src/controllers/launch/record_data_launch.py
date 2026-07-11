import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    controllers_pkg = get_package_share_directory('controllers')
    car_pkg = get_package_share_directory('car_description')
    
    world = os.path.join(controllers_pkg, 'worlds', '2lane_track.world')
    car_sdf = os.path.join(car_pkg, 'models', 'car', 'model.sdf')
    
    model_path = ':'.join([
        os.path.join(car_pkg, 'models'),
        os.environ.get('GAZEBO_MODEL_PATH', ''),
    ])
    
    # Car spawn
    car_x, car_y, car_yaw = -8.0, 0.0, -1.57
    
    ld = [
        # Gazebo
        ExecuteProcess(
            cmd=[
                'gazebo', '--verbose', world,
                '-s', 'libgazebo_ros_init.so',
                '-s', 'libgazebo_ros_factory.so',
            ],
            additional_env={'GAZEBO_MODEL_PATH': model_path},
            output='screen',
        ),
        
        # Spawn car
        TimerAction(
            period=3.0,
            actions=[
                Node(
                    package='gazebo_ros',
                    executable='spawn_entity.py',
                    name='spawn_car',
                    output='screen',
                    arguments=[
                        '-entity', 'car',
                        '-file', car_sdf,
                        '-x', str(car_x),
                        '-y', str(car_y),
                        '-z', '0.01',
                        '-Y', str(car_yaw),
                    ],
                ),
            ],
        ),
        
        # Data Collector Node
        TimerAction(
            period=5.0,
            actions=[
                Node(
                    package='controllers',
                    executable='data_collector_node',
                    name='data_collector',
                    output='screen',
                    parameters=[{
                        'expert_id': 0,
                        'save_folder': 'bc_data',
                        'workspace': os.path.expanduser('~/dagger_ws/src/controllers'),
                        'gate_x': -8.0,
                        'gate_y': 0.0,
                        'gate_yaw': -1.57,
                        'record': True,
                    }],
                    remappings=[
                        ('/scan', '/scan'),
                        ('/odom', '/odom'),
                        ('/cmd_vel', '/cmd_vel'),
                    ],
                ),
            ],
        ),
        
        # RViz2 Node for visualization
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', os.path.join(controllers_pkg, 'rviz', 'config.rviz')],
        ),
    ]
    return LaunchDescription(ld)
