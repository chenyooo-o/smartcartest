import os
import math
import statistics

import yaml
import cv2
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from rclpy.duration import Duration

from sensor_msgs.msg import LaserScan, Image, CameraInfo
from geometry_msgs.msg import TransformStamped
from cv_bridge import CvBridge

from message_filters import Subscriber, ApproximateTimeSynchronizer

import tf2_ros
from tf2_ros import StaticTransformBroadcaster


class SensorProjectionNode(Node):

    def __init__(self):
        super().__init__('sensor_projection')

        # 节点参数
        self.declare_parameter('extrinsics_file', 'extrinsics.yaml')
        self.declare_parameter('output_dir', '.')
        self.declare_parameter('max_images', 3)
        self.declare_parameter('slop', 0.08)

        self.extrinsics_file = self.get_parameter(
            'extrinsics_file'
        ).value
        self.output_dir = self.get_parameter('output_dir').value
        self.max_images = self.get_parameter('max_images').value
        self.slop = self.get_parameter('slop').value

        if self.max_images < 0:
            raise ValueError('max_images must be >= 0')
        if self.slop <= 0:
            raise ValueError('slop must be > 0')

        os.makedirs(self.output_dir, exist_ok=True)

        self.bridge = CvBridge()
        self.saved_images = 0
        self.camera_info_received = False
        self.time_differences = []
        self.pair_count = 0

        # 从 YAML 读取外参和相机内参
        self.load_extrinsics()

        # TF2：发布静态坐标变换，并监听 TF
        self.static_broadcaster = StaticTransformBroadcaster(self)
        self.publish_static_transforms()

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(
            self.tf_buffer, self
        )

        # 输出投影图像
        self.image_publisher = self.create_publisher(
            Image,
            '/projection/debug_image',
            10
        )

        # 接收相机内参话题
        self.camera_info_sub = self.create_subscription(
            CameraInfo,
            '/camera/camera_info',
            self.camera_info_callback,
            10
        )

        # 使用 message_filters 同步激光雷达和相机图像
        self.scan_sub = Subscriber(
            self, LaserScan, '/scan'
        )
        self.image_sub = Subscriber(
            self, Image, '/camera/image_raw'
        )

        self.sync = ApproximateTimeSynchronizer(
            [self.scan_sub, self.image_sub],
            queue_size=100,
            slop=self.slop
        )
        self.sync.registerCallback(self.synchronized_callback)

        self.get_logger().info(
            'Sensor projection node initialized.'
        )
        self.get_logger().info(
            f'ApproximateTimeSynchronizer slop: {self.slop:.3f}s'
        )
        self.get_logger().info(
            f'Camera intrinsics: fx={self.fx}, fy={self.fy}, '
            f'cx={self.cx}, cy={self.cy}'
        )

    def load_extrinsics(self):
        """读取外参文件，禁止在程序中写死传感器安装参数。"""
        if not os.path.isfile(self.extrinsics_file):
            raise FileNotFoundError(
                f'Extrinsics file not found: {self.extrinsics_file}'
            )

        with open(self.extrinsics_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        self.frames = config['frames']
        self.laser_config = config['laser_link']
        self.camera_config = config['camera_link']
        self.camera_intrinsics = config['camera_intrinsics']

        self.fx = float(self.camera_intrinsics['fx'])
        self.fy = float(self.camera_intrinsics['fy'])
        self.cx = float(self.camera_intrinsics['cx'])
        self.cy = float(self.camera_intrinsics['cy'])

        self.image_width = int(self.camera_intrinsics['width'])
        self.image_height = int(self.camera_intrinsics['height'])

        if self.fx <= 0 or self.fy <= 0:
            raise ValueError('Camera focal lengths must be positive')

        self.get_logger().info(
            f'Loaded extrinsics from {self.extrinsics_file}'
        )

    @staticmethod
    def quaternion_from_rpy(roll, pitch, yaw):
        """将欧拉角转换为四元数。"""
        cr = math.cos(roll / 2.0)
        sr = math.sin(roll / 2.0)
        cp = math.cos(pitch / 2.0)
        sp = math.sin(pitch / 2.0)
        cy = math.cos(yaw / 2.0)
        sy = math.sin(yaw / 2.0)

        return (
            sr * cp * cy - cr * sp * sy,
            cr * sp * cy + sr * cp * sy,
            cr * cp * sy - sr * sp * cy,
            cr * cp * cy + sr * sp * sy
        )

    def make_transform(self, parent, child, xyz, rpy):
        """根据 YAML 数据创建一个静态 TF 变换。"""
        transform = TransformStamped()
        transform.header.stamp = self.get_clock().now().to_msg()
        transform.header.frame_id = parent
        transform.child_frame_id = child

        transform.transform.translation.x = float(xyz[0])
        transform.transform.translation.y = float(xyz[1])
        transform.transform.translation.z = float(xyz[2])

        qx, qy, qz, qw = self.quaternion_from_rpy(
            float(rpy[0]),
            float(rpy[1]),
            float(rpy[2])
        )

        transform.transform.rotation.x = qx
        transform.transform.rotation.y = qy
        transform.transform.rotation.z = qz
        transform.transform.rotation.w = qw

        return transform

    def publish_static_transforms(self):
        """建立 map → odom → base_link → 两个传感器的 TF 树。"""
        map_frame = self.frames['map']
        odom_frame = self.frames['odom']
        base_frame = self.frames['base_link']
        laser_frame = self.frames['laser_link']
        camera_frame = self.frames['camera_link']

        transforms = [
            self.make_transform(
                map_frame, odom_frame,
                [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
            ),
            self.make_transform(
                odom_frame, base_frame,
                [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
            ),
            self.make_transform(
                self.laser_config['parent'],
                laser_frame,
                self.laser_config['xyz'],
                self.laser_config['rpy']
            ),
            self.make_transform(
                self.camera_config['parent'],
                camera_frame,
                self.camera_config['xyz'],
                self.camera_config['rpy']
            )
        ]

        self.static_broadcaster.sendTransform(transforms)

        self.get_logger().info(
            'Static TF published: map -> odom -> base_link'
        )
        self.get_logger().info(
            f'{base_frame} -> {laser_frame}'
        )
        self.get_logger().info(
            f'{base_frame} -> {camera_frame}'
        )

    def camera_info_callback(self, msg):
        """接收相机信息，并检查图像尺寸。内参真值仍来自 YAML。"""
        if not self.camera_info_received:
            if (
                msg.width != self.image_width
                or msg.height != self.image_height
            ):
                self.get_logger().warning(
                    'CameraInfo image size differs from extrinsics.yaml'
                )
            else:
                self.get_logger().info(
                    'CameraInfo received; image size verified.'
                )

            self.camera_info_received = True

    @staticmethod
    def quaternion_matrix(q):
        """四元数转换为 3x3 旋转矩阵。"""
        x = q.x
        y = q.y
        z = q.z
        w = q.w

        norm = math.sqrt(x * x + y * y + z * z + w * w)
        if norm == 0:
            raise ValueError('Invalid zero quaternion')

        x /= norm
        y /= norm
        z /= norm
        w /= norm

        return np.array([
            [1 - 2 * (y * y + z * z),
             2 * (x * y - z * w),
             2 * (x * z + y * w)],

            [2 * (x * y + z * w),
             1 - 2 * (x * x + z * z),
             2 * (y * z - x * w)],

            [2 * (x * z - y * w),
             2 * (y * z + x * w),
             1 - 2 * (x * x + y * y)]
        ], dtype=np.float64)

    def synchronized_callback(self, scan_msg, image_msg):
        """同步回调：获取 TF、投影激光点、发布并保存图像。"""
        if not self.camera_info_received:
            self.get_logger().warning(
                'Waiting for /camera/camera_info ...'
            )
            return

        try:
            scan_time = Time.from_msg(
                scan_msg.header.stamp,
                clock_type=self.get_clock().clock_type
            )

            # target 是 camera_link，source 是 laser_link
            transform = self.tf_buffer.lookup_transform(
                self.frames['camera_link'],
                self.frames['laser_link'],
                scan_time,
                timeout=Duration(seconds=1.0)
            )

            image = self.bridge.imgmsg_to_cv2(
                image_msg,
                desired_encoding='rgb8'
            )

            image = np.array(image, copy=True)
            self.project_scan(scan_msg, image, transform)

            # 发布 rgb8 调试图像
            output_msg = self.bridge.cv2_to_imgmsg(
                image,
                encoding='rgb8'
            )
            output_msg.header = image_msg.header
            self.image_publisher.publish(output_msg)

            # 记录两路传感器的时间差
            scan_stamp = (
                scan_msg.header.stamp.sec
                + scan_msg.header.stamp.nanosec * 1e-9
            )
            image_stamp = (
                image_msg.header.stamp.sec
                + image_msg.header.stamp.nanosec * 1e-9
            )

            difference = abs(scan_stamp - image_stamp)
            self.time_differences.append(difference)
            self.pair_count += 1

            if len(self.time_differences) > 500:
                self.time_differences.pop(0)

            if self.pair_count % 10 == 0:
                median_ms = statistics.median(
                    self.time_differences
                ) * 1000.0

                self.get_logger().info(
                    f'Synchronized pairs: {self.pair_count}, '
                    f'median time difference: {median_ms:.2f} ms'
                )

            # 保存投影图片
            if self.saved_images < self.max_images:
                self.saved_images += 1
                filename = os.path.join(
                    self.output_dir,
                    f'projection_{self.saved_images:03d}.png'
                )

                bgr_image = cv2.cvtColor(
                    image, cv2.COLOR_RGB2BGR
                )
                cv2.imwrite(filename, bgr_image)

                self.get_logger().info(
                    f'Saved projection image: {filename}'
                )

        except (
            tf2_ros.LookupException,
            tf2_ros.ConnectivityException,
            tf2_ros.ExtrapolationException
        ) as exc:
            self.get_logger().warning(
                f'TF lookup failed: {exc}'
            )
        except Exception as exc:
            self.get_logger().error(
                f'Projection failed: {exc}'
            )

    def project_scan(self, scan_msg, image, transform):
        """将激光雷达二维点投影到相机光学坐标系和图像平面。"""
        translation = transform.transform.translation
        rotation = transform.transform.rotation

        rotation_matrix = self.quaternion_matrix(rotation)

        translation_vector = np.array([
            translation.x,
            translation.y,
            translation.z
        ], dtype=np.float64)

        angle = scan_msg.angle_min

        for distance in scan_msg.ranges:
            if (
                not math.isfinite(distance)
                or distance < scan_msg.range_min
                or distance > scan_msg.range_max
            ):
                angle += scan_msg.angle_increment
                continue

            # 激光雷达坐标系中的二维点，z=0
            point_laser = np.array([
                distance * math.cos(angle),
                distance * math.sin(angle),
                0.0
            ], dtype=np.float64)

            angle += scan_msg.angle_increment

            # TF2 变换：laser_link -> camera_link
            point_camera = (
                rotation_matrix @ point_laser
                + translation_vector
            )

            # ROS camera_link 转 camera optical frame：
            # optical X 向右，Y 向下，Z 向前
            x_optical = -point_camera[1]
            y_optical = -point_camera[2]
            z_optical = point_camera[0]

            # 只投影相机前方的点
            if z_optical <= 0.01:
                continue

            # 针孔相机模型
            u = self.fx * x_optical / z_optical + self.cx
            v = self.fy * y_optical / z_optical + self.cy

            u = int(round(u))
            v = int(round(v))

            if (
                0 <= u < image.shape[1]
                and 0 <= v < image.shape[0]
            ):
                # 近距离红色，远距离蓝色
                ratio = min(
                    max(
                        (distance - scan_msg.range_min)
                        / (scan_msg.range_max - scan_msg.range_min),
                        0.0
                    ),
                    1.0
                )

                red = int(255 * (1.0 - ratio))
                blue = int(255 * ratio)
                color = (red, 0, blue)

                cv2.circle(
                    image,
                    (u, v),
                    3,
                    color,
                    -1
                )


def main(args=None):
    rclpy.init(args=args)

    node = None
    try:
        node = SensorProjectionNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f'[ERROR] {exc}')
        raise
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
