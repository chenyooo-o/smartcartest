import rclpy
from rclpy.node import Node

from sensor_interfaces.msg import SensorData


class SensorPublisher(Node):

    def __init__(self):
        super().__init__('sensor_publisher')

        self.publisher_ = self.create_publisher(
            SensorData,
            '/sensor_data',
            10
        )

        # 每 0.1 秒发布一次数据，即 10 Hz
        self.timer = self.create_timer(
            0.1,
            self.publish_sensor_data
        )

        self.get_logger().info('Sensor publisher node started')

    def publish_sensor_data(self):
        msg = SensorData()

        msg.distance = 0.5
        msg.unit = 'm'
        msg.stamp = self.get_clock().now().to_msg()
        msg.status = 0

        self.publisher_.publish(msg)

        self.get_logger().info(
            f'Published distance: {msg.distance:.2f} {msg.unit}'
        )


def main(args=None):
    rclpy.init(args=args)

    node = SensorPublisher()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
