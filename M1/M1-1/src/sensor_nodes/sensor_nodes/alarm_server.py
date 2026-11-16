import rclpy
from rclpy.node import Node

from sensor_interfaces.srv import TriggerAlarm


class AlarmServer(Node):

    def __init__(self):
        super().__init__('alarm_server')

        # 创建报警服务端
        self.service = self.create_service(
            TriggerAlarm,
            '/trigger_alarm',
            self.trigger_alarm_callback
        )

        self.get_logger().info(
            'Alarm server started, waiting for requests...'
        )

    def trigger_alarm_callback(self, request, response):
        # 处理报警请求
        response.success = True
        response.message = 'Alarm triggered successfully!'

        self.get_logger().warning(
            '[ALARM SERVER] Alarm request received!'
        )

        return response


def main(args=None):
    rclpy.init(args=args)

    node = AlarmServer()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
