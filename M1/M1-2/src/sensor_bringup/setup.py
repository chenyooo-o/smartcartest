from setuptools import setup

package_name = 'sensor_bringup'

setup(
    name=package_name,
    version='0.0.0',
    packages=[],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/bringup.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='yyo',
    maintainer_email='chen_yyo@qq.com',
    description='Launch files and configuration for the sensor system',
    license='Apache-2.0',
)
