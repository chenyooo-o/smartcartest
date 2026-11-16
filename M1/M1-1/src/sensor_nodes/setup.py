from setuptools import find_packages, setup

package_name = 'sensor_nodes'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='yyo',
    maintainer_email='chen_yyo@qq.com',
    description='ROS 2 sensor processing and alarm nodes',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'sensor_publisher = sensor_nodes.sensor_publisher:main',
            'sensor_processor = sensor_nodes.sensor_processor:main',
            'alarm_monitor = sensor_nodes.alarm_monitor:main',
            'alarm_server = sensor_nodes.alarm_server:main',
        ],
    },
)

