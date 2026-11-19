
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import TimerAction
from launch_ros.actions import Node


def generate_launch_description():

    config_dir = os.path.join(
        get_package_share_directory('sensor_bringup'),
        'config'
    )

    robot1_params = os.path.join(config_dir, 'robot1.yaml')
    robot2_params = os.path.join(config_dir, 'robot2.yaml')

    for params_file in [robot1_params, robot2_params]:
        if not os.path.isfile(params_file):
            raise FileNotFoundError(
                f'Parameter file not found: {params_file}'
            )

    nodes = []

    for robot, params_file in [
        ('robot1', robot1_params),
        ('robot2', robot2_params)
    ]:

        remappings = [
            ('/sensor_data', f'/{robot}/sensor_data'),
            ('/processed_distance', f'/{robot}/processed_distance')
        ]

        # 节点 A：传感器发布
        nodes.append(
            Node(
                package='sensor_nodes',
                executable='sensor_publisher',
                namespace=robot,
                name='sensor_publisher',
                remappings=remappings,
                output='screen'
            )
        )

        # 节点 B：传感器处理
        nodes.append(
            Node(
                package='sensor_nodes',
                executable='sensor_processor',
                namespace=robot,
                name='node_b_filter',
                remappings=remappings,
                output='screen'
            )
        )

        # 节点 C：延迟 3 秒启动
        nodes.append(
            TimerAction(
                period=3.0,
                actions=[
                    Node(
                        package='sensor_nodes',
                        executable='alarm_monitor',
                        namespace=robot,
                        name='alarm_monitor',
                        parameters=[params_file],
                        remappings=remappings,
                        output='screen'
                    )
                ]
            )
        )

    # 报警服务端
    alarm_server = Node(
        package='sensor_nodes',
        executable='alarm_server',
        name='alarm_server',
        output='screen'
    )

    nodes.append(alarm_server)

    return LaunchDescription(nodes)

