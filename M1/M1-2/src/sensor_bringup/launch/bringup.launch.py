from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    sensor_publisher = Node(
        package='sensor_nodes',
        executable='sensor_publisher',
        name='sensor_publisher',
        output='screen'
    )

    return LaunchDescription([
        sensor_publisher
    ])
