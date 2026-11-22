import csv
import time
from pathlib import Path

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image


class P95Sampler(Node):
    def __init__(self):
        super().__init__('p95_sampler')

        self.samples = []
        self.start_time = time.monotonic()
        self.finished = False

        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1000,
            reliability=ReliabilityPolicy.RELIABLE,
        )

        self.subscription = self.create_subscription(
            Image,
            '/perception/result',
            self.callback,
            qos,
        )

        self.timer = self.create_timer(1.0, self.check_timeout)

        self.get_logger().info(
            'P95 sampler started. Target: 600 frames, timeout: 60 seconds.'
        )

    def callback(self, msg):
        if self.finished:
            return

        receive_ns = self.get_clock().now().nanoseconds
        stamp_ns = (
            msg.header.stamp.sec * 1_000_000_000
            + msg.header.stamp.nanosec
        )

        latency_ms = (receive_ns - stamp_ns) / 1_000_000

        self.samples.append({
            'seq': len(self.samples) + 1,
            'stamp_ns': stamp_ns,
            'receive_ns': receive_ns,
            'latency_ms': latency_ms,
        })

        if len(self.samples) % 100 == 0:
            print(f'采样进度：{len(self.samples)}/600 帧', flush=True)

        if len(self.samples) >= 600:
            self.finish('已采集到600帧')

    def check_timeout(self):
        if time.monotonic() - self.start_time >= 60:
            self.finish('达到60秒采集时间上限')

    def finish(self, reason):
        if self.finished:
            return

        self.finished = True
        self.timer.cancel()

        output = Path('measurements/p95_samples_retry.csv')

        with output.open('w', newline='') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    'seq',
                    'stamp_ns',
                    'receive_ns',
                    'latency_ms',
                ],
            )
            writer.writeheader()
            writer.writerows(self.samples)

        print('\n========== P95 测量结果 ==========')
        print('结束原因:', reason)
        print('样本数量:', len(self.samples))
        print('CSV保存路径:', output)

        if self.samples:
            values = np.array(
                [item['latency_ms'] for item in self.samples]
            )

            print(f'平均延迟: {np.mean(values):.3f} ms')
            print(f'P95延迟: {np.percentile(values, 95):.3f} ms')
            print(f'最大延迟: {np.max(values):.3f} ms')
            print(f'最小延迟: {np.min(values):.3f} ms')
            print('负延迟样本数:', int(np.sum(values < 0)))
        else:
            print('没有收到图像样本，无法计算延迟。')

        print('==================================')


def main():
    rclpy.init()
    node = P95Sampler()

    try:
        while rclpy.ok() and not node.finished:
            rclpy.spin_once(node, timeout_sec=0.2)
            if time.monotonic() - node.start_time >= 60:
                node.finish("达到60秒采集时间上限")
    except KeyboardInterrupt:
        print('用户中断采集。')
    finally:
        if rclpy.ok():
            rclpy.shutdown()
        node.destroy_node()


if __name__ == '__main__':
    main()
