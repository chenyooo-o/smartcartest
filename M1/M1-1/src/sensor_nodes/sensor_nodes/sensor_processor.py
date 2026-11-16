import rclpy
from rclpy.node import Node

from sensor_interfaces.msg import SensorData
from std_msgs.msg import Float32


class SensorProcessor(Node):

    def __init__(self):
        super().__init__('node_b_filter')

        # 声明低通滤波参数
        self.declare_parameter('alpha', 0.3)
        self.alpha = self.get_parameter('alpha').value
        self.add_on_set_parameters_callback(
            self.parameter_callback
        )

        # 保存上一次滤波结果
        self.filtered_distance = None

        # 创建传感器数据订阅器
        self.subscription = self.create_subscription(
            SensorData,
            '/sensor_data',
            self.sensor_callback,
            10
        )

        # 创建处理结果发布器
        self.publisher_ = self.create_publisher(
            Float32,
            '/processed_distance',
            10
        )

        self.get_logger().info(
            f'Sensor processor started, alpha={self.alpha}'
        )

    def parameter_callback(self, params):
        from rcl_interfaces.msg import SetParametersResult

        for param in params:
            if param.name == 'alpha':
                if param.type_ != param.Type.DOUBLE:
                    return SetParametersResult(
                        successful=False,
                        reason='alpha must be a floating-point number'
                    )

                if not 0.0 < param.value <= 1.0:
                    return SetParametersResult(
                        successful=False,
                        reason='alpha must be greater than 0 and no more than 1'
                    )

                self.alpha = param.value
                self.get_logger().info(
                    f'Alpha updated to {self.alpha}'
                )

        return SetParametersResult(successful=True)

    def sensor_callback(self, msg):

        # 检查传感器数据状态
        if msg.status != 0:
            self.get_logger().warning(
                f'Invalid sensor data, status={msg.status}. Skipping.'
            )
            return

        # 获取当前传感器距离
        current_distance = msg.distance

        # 第一次接收数据时直接使用当前值
        if self.filtered_distance is None:
            self.filtered_distance = current_distance
        else:
            # 低通滤波计算
            self.filtered_distance = (
                self.alpha * current_distance
                + (1.0 - self.alpha) * self.filtered_distance
            )

        # 创建 Float32 消息
        output_msg = Float32()
        output_msg.data = float(self.filtered_distance)

        # 发布滤波结果
        self.publisher_.publish(output_msg)

        self.get_logger().info(
            f'Filtered distance: {self.filtered_distance:.3f} m'
        )


def main(args=None):
    rclpy.init(args=args)

    node = SensorProcessor()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
