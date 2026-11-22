#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""图像处理与控制节点 —— 终端2 运行

订阅:
    /camera/image_raw    640x480, 目标 30Hz（接受 bgr8 / mono8）
发布:
    /perception/result   640x480 mono8
    /control/cmd         Twist, 20Hz

运行:
    python3 image_proc.py

观测:
    ros2 topic hz    /perception/result
    ros2 topic hz    /control/cmd
    ros2 topic delay /perception/result
"""

import cv2
import numpy as np
import rclpy
import time
from cv_bridge import CvBridge
from geometry_msgs.msg import Twist
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image

IMAGE_IN = "/camera/image_raw"
IMAGE_OUT = "/perception/result"
CMD_OUT = "/control/cmd"

IMAGE_WIDTH = 640
IMAGE_HEIGHT = 480
WORK_WIDTH = 1280
WORK_HEIGHT = 720
CONTROL_HZ = 20.0


def make_sub_qos(depth=30):
    """创建图像链路 QoS；depth 表示历史消息缓存深度。"""
    return QoSProfile(
        depth=depth,
        reliability=ReliabilityPolicy.RELIABLE,
        history=HistoryPolicy.KEEP_LAST,
    )


class ImageProc(Node):
    def __init__(self):
        super().__init__("image_proc")
        self.sub = self.create_subscription(
            Image, IMAGE_IN, self.on_image, make_sub_qos(depth=1)
        )
        self.pub = self.create_publisher(Image, IMAGE_OUT, make_sub_qos())
        self.bridge = CvBridge()

        self.input_count = 0
        self.output_count = 0
        self.last_input_count = 0
        self.last_output_count = 0
        self.last_report_time = time.monotonic()
        self.report_timer = self.create_timer(3.0, self.report_stats)

    def report_stats(self):
        now = time.monotonic()
        elapsed = now - self.last_report_time
        if elapsed <= 0:
            return

        input_rate = (self.input_count - self.last_input_count) / elapsed
        output_rate = (self.output_count - self.last_output_count) / elapsed

        self.get_logger().info(
            "[IMAGE_PROC] 输入: %d 帧, 输出: %d 帧, "
            "输入频率: %.2f Hz, 输出频率: %.2f Hz"
            % (
                self.input_count,
                self.output_count,
                input_rate,
                output_rate
            )
        )

        self.last_input_count = self.input_count
        self.last_output_count = self.output_count
        self.last_report_time = now

    def on_image(self, msg):
        self.input_count += 1
        # 将输入图像转换为灰度图
        gray = self.bridge.imgmsg_to_cv2(
            msg, desired_encoding="mono8"
        )

        # NumPy 向量化处理：亮度增加20
        brightened = np.clip(
            gray.astype(np.int16) + 20,
            0,
            255
        )

        # NumPy 向量化处理：对比度增强
        contrasted = np.clip(
            ((brightened - 128) * 3) // 2 + 128,
            0,
            255
        ).astype(np.uint8)

        # 转换为 ROS Image 消息
        out = self.bridge.cv2_to_imgmsg(
            contrasted, encoding="mono8"
        )

        # 保留输入图像时间戳和坐标系
        out.header.stamp = msg.header.stamp
        out.header.frame_id = msg.header.frame_id

        self.pub.publish(out)
        self.output_count += 1


class ControlLoop(Node):
    def __init__(self):
        super().__init__("control_loop")
        self.pub = self.create_publisher(Twist, CMD_OUT, make_sub_qos())
        self.timer = self.create_timer(1.0 / CONTROL_HZ, self.on_timer)

    def on_timer(self):
        cmd = Twist()
        cmd.linear.x = 0.10
        cmd.angular.z = 0.05
        self.pub.publish(cmd)


def main():
    rclpy.init()
    nodes = [ImageProc(), ControlLoop()]
    executor = SingleThreadedExecutor()
    for node in nodes:
        executor.add_node(node)
    try:
        executor.spin()
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        executor.shutdown()
        for node in nodes:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
