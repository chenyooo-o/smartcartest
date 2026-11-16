import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32
from sensor_interfaces.srv import TriggerAlarm


class AlarmMonitor(Node):

    def __init__(self):
        super().__init__('alarm_monitor')

        # 声明报警阈值参数
        self.declare_parameter('alarm_threshold', 0.3)

        # 声明服务超时时间参数
        self.declare_parameter('service_timeout', 1.0)

        # 读取参数
        self.alarm_threshold = self.get_parameter(
            'alarm_threshold'
        ).value

        self.service_timeout = self.get_parameter(
            'service_timeout'
        ).value
        # 保存正在等待响应的服务请求
        self.pending_requests = []

        # 每 0.1 秒检查一次服务请求是否超时
        self.timeout_timer = self.create_timer(
            0.1,
            self.check_service_timeout
        )

        # 创建处理结果订阅器
        self.subscription = self.create_subscription(
            Float32,
            '/processed_distance',
            self.distance_callback,
            10
        )
        # 创建报警服务客户端
        self.client = self.create_client(
            TriggerAlarm,
            '/trigger_alarm'
        )

        self.get_logger().info(
            f'Alarm monitor started, '
            f'threshold={self.alarm_threshold}, '
            f'timeout={self.service_timeout}'
        )

    def distance_callback(self, msg):
        # 判断距离是否低于报警阈值
        if msg.data < self.alarm_threshold:

            self.get_logger().warning(
                f'Distance too close: {msg.data:.3f} m'
            )


            # 创建服务请求
            request = TriggerAlarm.Request()

            # 异步调用报警服务，不阻塞当前回调
            future = self.client.call_async(request)

            # 记录请求及其开始时间
            self.pending_requests.append({
                'future': future,
                'start_time': self.get_clock().now(),
                'timed_out': False
            })

            # 注册服务完成回调
            future.add_done_callback(
                self.alarm_response_callback
            )

    def alarm_response_callback(self, future):
        # 查找当前服务请求
        item = next(
            (
                request for request in self.pending_requests
                if request['future'] is future
            ),
            None
        )

        # 如果请求已经超时，不再处理迟到的响应
        if item is None or item['timed_out']:
            return

        try:
            response = future.result()

            if response.success:
                self.get_logger().info(
                    f'[ALARM] {response.message}'
                )
            else:
                self.get_logger().warning(
                    f'Alarm failed: {response.message}'
                )

        except Exception as e:
            self.get_logger().error(
                f'Alarm service call failed: {e}'
            )
        finally:
            # 服务响应完成后，清理对应请求
            if item in self.pending_requests:
                self.pending_requests.remove(item)

    def check_service_timeout(self):
        # 获取当前时间
        current_time = self.get_clock().now()

        # 检查所有等待响应的请求
        for item in self.pending_requests[:]:
            future = item['future']
            start_time = item['start_time']

            # 计算已经等待的时间
            elapsed = (current_time - start_time).nanoseconds / 1e9

            # 如果服务已经返回，移除请求
            if future.done():
                continue

            # 如果等待时间超过设定值，打印警告
            elif elapsed >= self.service_timeout:
                # 标记请求已经超时
                item['timed_out'] = True

                self.get_logger().warning(
                    '[WARN] Alarm service response timeout'
                )

                # 从等待列表中移除
                self.pending_requests.remove(item)

def main(args=None):
    rclpy.init(args=args)

    node = AlarmMonitor()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()