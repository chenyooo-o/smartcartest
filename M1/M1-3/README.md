# M1-3：多传感器数据融合与图像投影

## 一、项目简介

本项目基于 ROS 2 Humble，实现激光雷达与相机数据的时间同步、坐标变换和图像投影。

系统订阅激光雷达扫描数据、相机图像和相机内参，通过 ApproximateTimeSynchronizer 对多传感器数据进行近似时间同步，利用 TF2 获取传感器之间的坐标变换，再根据相机针孔模型将激光雷达点投影到相机图像中，生成可视化结果。

## 二、项目结构

```text
M1-3/
├── extrinsics.yaml
├── extrinsics_nondefault.yaml
├── make_bag.py
├── sample_bag/
├── sample_bag_nondefault/
├── projection_default/
│   ├── projection_001.png
│   ├── projection_002.png
│   └── projection_003.png
├── projection_nondefault/
│   ├── projection_001.png
│   ├── projection_002.png
│   └── projection_003.png
└── sensor_projection/
    ├── package.xml
    ├── setup.py
    └── sensor_projection/
        └── projection_node.py
```

主要文件说明：

| 文件或目录 | 功能 |
|---|---|
| `projection_node.py` | 多传感器同步、TF 坐标变换和图像投影节点 |
| `extrinsics.yaml` | 默认传感器外参和相机内参 |
| `extrinsics_nondefault.yaml` | 非默认参数配置，用于验证参数可配置性 |
| `make_bag.py` | 生成测试用 rosbag 数据 |
| `sample_bag/` | 默认配置测试使用的 rosbag |
| `sample_bag_nondefault/` | 非默认配置测试使用的 rosbag |
| `projection_default/` | 默认配置生成的投影图片 |
| `projection_nondefault/` | 非默认配置生成的投影图片 |

## 三、系统接口

### 1. 订阅话题

| 话题 | 消息类型 | 功能 |
|---|---|---|
| `/scan` | `sensor_msgs/msg/LaserScan` | 激光雷达扫描数据 |
| `/camera/image_raw` | `sensor_msgs/msg/Image` | 相机原始图像 |
| `/camera/camera_info` | `sensor_msgs/msg/CameraInfo` | 相机内参信息 |

### 2. 发布话题

| 话题 | 消息类型 | 功能 |
|---|---|---|
| `/projection/debug_image` | `sensor_msgs/msg/Image` | 激光雷达点投影后的调试图像，编码为 rgb8 |

### 3. 主要参数

| 参数 | 默认值 | 功能 |
|---|---|---|
| `use_sim_time` | `false` | 是否使用仿真时间 |
| `extrinsics_file` | `extrinsics.yaml` | 外参配置文件 |
| `output_dir` | `.` | 投影图片保存目录 |
| `max_images` | `3` | 最多保存的图片数量 |
| `slop` | `0.08` | 近似时间同步允许的时间差，单位为秒 |

## 四、坐标变换与投影原理

系统使用 TF2 管理传感器坐标系之间的关系，并通过静态 TF 发布传感器外参。

默认配置中：

- `base_link` 为机器人基坐标系。
- `laser_link` 为激光雷达坐标系。
- `camera_link` 为相机坐标系。

默认外参：

| 子坐标系 | 父坐标系 | 平移 x | 平移 y | 平移 z |
|---|---|---:|---:|---:|
| `laser_link` | `base_link` | 0.15 m | 0.00 m | 0.20 m |
| `camera_link` | `base_link` | 0.10 m | 0.00 m | 0.30 m |

相机内参：

- `fx = 500`
- `fy = 500`
- `cx = 320`
- `cy = 240`

完成坐标变换后，使用针孔相机模型计算像素坐标：

\[
u = f_x \frac{X}{Z} + c_x
\]

\[
v = f_y \frac{Y}{Z} + c_y
\]

其中，\(X\)、\(Y\)、\(Z\) 是点在相机光学坐标系中的坐标，\(u\)、\(v\) 是图像中的像素坐标。

## 五、编译与运行

### 1. 编译功能包

```bash
source /opt/ros/humble/setup.bash
cd ~/smartcartest/M1/M1-3
colcon build --packages-select sensor_projection
```

### 2. 加载工作空间

```bash
source /opt/ros/humble/setup.bash
source ~/smartcartest/M1/M1-3/install/setup.bash
```

### 3. 启动投影节点

```bash
ros2 run sensor_projection sensor_projection --ros-args \
  -p extrinsics_file:=/home/yyo/smartcartest/M1/M1-3/extrinsics.yaml \
  -p output_dir:=/home/yyo/smartcartest/M1/M1-3/projection_output \
  -p use_sim_time:=false
```

### 4. 播放测试数据

另开一个终端：

```bash
source /opt/ros/humble/setup.bash
cd ~/smartcartest/M1/M1-3
ros2 bag play sample_bag
```

节点接收同步后的传感器数据，生成投影图像并保存到指定目录。

### 5. 查看输出话题

```bash
ros2 topic list
ros2 topic info /projection/debug_image
```

## 六、时间同步实验

本项目使用 `ApproximateTimeSynchronizer` 对激光雷达、相机图像和相机内参进行近似时间同步。

同步队列大小设置为 100，并通过调整 `slop` 参数进行实验。`slop` 表示允许参与匹配的消息之间存在的最大时间差。

在仿真时间模式下，使用相同的测试数据进行不同 `slop` 参数实验，结果如下：

| Slop | 匹配帧数 | 中位时间差 | 最小时间差 | 最大时间差 |
|---|---:|---:|---:|---:|
| 0.02 s | 31 | 9.14 ms | 0.52 ms | 18.41 ms |
| 0.05 s | 40 | 31.21 ms | 14.97 ms | 49.77 ms |
| 0.08 s | 21 | 33.19 ms | 14.97 ms | 51.53 ms |
| 0.10 s | 40 | 31.21 ms | 0.52 ms | 53.90 ms |
| 0.15 s | 32 | 32.65 ms | 11.65 ms | 58.39 ms |

实验结果表明，不同 `slop` 设置会影响消息匹配数量和匹配时间差。由于近似同步器的匹配策略、消息到达顺序等因素，匹配数量和时间差不一定随 `slop` 增大而单调变化。

## 七、仿真时间实验

项目分别测试了普通时间模式和仿真时间模式。

### 1. 普通时间模式

节点设置：

```bash
-p use_sim_time:=false
```

播放 rosbag：

```bash
ros2 bag play sample_bag
```

实验结果：

- 成功匹配 40 帧。
- 时间差中位数约为 35.38 ms。
- 成功保存 3 张投影图片。

### 2. 仿真时间模式

节点设置：

```bash
-p use_sim_time:=true
```

播放 rosbag：

```bash
ros2 bag play sample_bag --clock
```

实验结果：

- 成功匹配 40 帧。
- 时间差中位数约为 35.74 ms。
- 成功保存 3 张投影图片。

### 3. 实验对比

两种模式下均能正常完成消息同步和图像投影。实验中时间差中位数较为接近，说明节点能够在普通时间和仿真时间环境下运行。

## 八、非默认外参验证

为了验证程序对不同外参和相机内参的适应能力，使用 `extrinsics_nondefault.yaml` 进行测试。

非默认配置：

| 参数 | 默认配置 | 非默认配置 |
|---|---:|---:|
| 激光雷达 z 平移 | 0.20 m | 0.45 m |
| 相机 z 平移 | 0.30 m | 0.75 m |
| fx | 500 | 420 |
| fy | 500 | 500 |
| cx | 320 | 320 |
| cy | 240 | 240 |

测试时加载非默认配置文件，节点成功读取新的外参和相机内参，并完成投影，


保存了 3 张结果图片。

## 九、实验结果

项目完成了以下功能验证：

1. 成功订阅激光雷达、相机图像和相机内参话题。
2. 成功使用 ApproximateTimeSynchronizer 完成多传感器数据同步。
3. 成功使用 TF2 获取传感器坐标变换。
4. 成功根据相机针孔模型完成激光雷达点的图像投影。
5. 成功发布 `/projection/debug_image` 调试图像。
6. 默认配置下成功保存 3 张投影图片。
7. 非默认外参配置下成功保存 3 张投影图片。
8. 完成不同 `slop` 参数的时间同步实验。
9. 完成普通时间与仿真时间模式的对比实验。
