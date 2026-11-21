# M1-1：ROS 2 传感器数据处理与报警系统

## 1. 项目简介

本项目基于 ROS 2 Humble 开发，实现了一个简单的传感器数据采集、滤波处理与距离报警系统。

项目通过创建自定义 ROS 2 消息接口和服务接口，实现不同节点之间的数据通信与服务调用。

系统主要完成以下功能：

1. 传感器数据定时发布。
2. 传感器数据状态检查与指数滤波处理。
3. 根据距离阈值进行报警监控。
4. 通过 ROS 2 Service 实现报警请求与响应。

本项目采用 Python 编写功能节点，使用 ROS 2 Topic 实现连续数据传输，使用 ROS 2 Service 实现报警服务调用。

## 2. 开发环境

| 项目 | 配置 |
|---|---|
| 操作系统 | Ubuntu |
| ROS 2 版本 | Humble |
| 编程语言 | Python |
| 构建工具 | colcon |
| 通信方式 | ROS 2 Topic、Service |

## 3. 项目目录结构

```text
M1-1/
├── README.md
└── src/
    ├── sensor_interfaces/
    │   ├── msg/
    │   │   └── SensorData.msg
    │   ├── srv/
    │   │   └── TriggerAlarm.srv
    │   ├── CMakeLists.txt
    │   └── package.xml
    │
    └── sensor_nodes/
        ├── sensor_nodes/
        │   ├── __init__.py
        │   ├── sensor_publisher.py
        │   ├── sensor_processor.py
        │   ├── alarm_monitor.py
        │   └── alarm_server.py
        ├── resource/
        ├── test/
        ├── package.xml
        ├── setup.py
        └── setup.cfg
```

## 4. 自定义接口设计

### 4.1 SensorData.msg

文件路径：`sensor_interfaces/msg/SensorData.msg`

用于定义传感器数据的消息结构。

```text
float32 distance
string unit
builtin_interfaces/Time stamp
uint8 status
```

字段说明：

| 字段 | 类型 | 含义 |
|---|---|---|
| distance | float32 | 传感器测量距离 |
| unit | string | 距离单位 |
| stamp | builtin_interfaces/Time | 数据时间戳 |
| status | uint8 | 传感器数据状态 |

通过自定义消息，可以在一次通信中传输距离、单位、时间戳和状态等信息。

### 4.2 TriggerAlarm.srv

文件路径：`sensor_interfaces/srv/TriggerAlarm.srv`

用于定义报警服务的请求与响应格式。

```text
---
bool success
string message
```

其中，`---` 用于分隔请求和响应。

| 字段 | 含义 |
|---|---|
| 请求部分 | 空请求，无需额外参数 |
| success | 表示报警服务是否执行成功 |
| message | 返回服务执行结果信息 |

### 4.3 接口包配置

`CMakeLists.txt` 用于配置自定义消息和服务接口的生成。

`package.xml` 用于声明接口包的基本信息及相关依赖。

## 5. 节点功能设计

系统包含三个主要功能节点和一个辅助报警服务端节点。

### 5.1 传感器数据发布节点

文件：`sensor_publisher.py`

主要功能：

- 定时生成模拟传感器数据。
- 使用自定义消息 `SensorData`。
- 向 `/sensor_data` 话题发布传感器数据。
- 默认距离值为 0.5 m。

### 5.2 传感器数据滤波处理节点

文件：`sensor_processor.py`

主要功能：

- 订阅 `/sensor_data` 话题。
- 检查传感器数据状态。
- 对有效距离数据进行指数滤波。
- 将处理结果发布到 `/processed_distance` 话题。

默认滤波参数：

```text
alpha = 0.3
```

指数滤波公式：

\[
y_t=\alpha x_t+(1-\alpha)y_{t-1}
\]

其中：

- \(x_t\)：当前传感器输入值。
- \(y_{t-1}\)：上一时刻的滤波结果。
- \(y_t\)：当前滤波结果。
- \(\alpha\)：滤波系数。

通过加权计算，降低传感器数据波动，提高数据平滑程度。

### 5.3 报警监控节点

文件：`alarm_monitor.py`

主要功能：

- 订阅 `/processed_distance` 话题。
- 获取滤波后的距离数据。
- 将距离与设定的报警阈值进行比较。
- 当距离小于报警阈值时，调用 `/trigger_alarm` 服务。
- 等待服务端响应，并处理超时情况。

默认参数：

```text
alarm_threshold = 0.3
service_timeout = 1.0
```

报警判断条件：

```text
distance < alarm_threshold
```

### 5.4 报警服务端节点

文件：`alarm_server.py`

主要功能：

- 创建 `/trigger_alarm` 服务。
- 接收报警监控节点发送的请求。
- 执行报警服务处理。
- 返回服务执行状态和结果信息。

该节点作为辅助服务端，与报警监控节点配合完成报警请求与响应。

## 6. 节点通信关系

系统使用 ROS 2 Topic 和 Service 两种通信方式。

### 6.1 Topic 通信

| 话题名称 | 消息类型 | 发布节点 | 订阅节点 |
|---|---|---|---|
| `/sensor_data` | `sensor_interfaces/msg/SensorData` | sensor_publisher | sensor_processor |
| `/processed_distance` | `std_msgs/msg/Float32` | sensor_processor | alarm_monitor |

### 6.2 Service 通信

| 服务名称 | 服务类型 | 客户端 | 服务端 |
|---|---|---|---|
| `/trigger_alarm` | `sensor_interfaces/srv/TriggerAlarm` | alarm_monitor | alarm_server |

### 6.3 系统工作流程

1. `sensor_publisher` 定时生成传感器数据，并发布到 `/sensor_data`。
2. `sensor_processor` 接收原始数据，检查状态并执行指数滤波。
3. `sensor_processor` 将滤波结果发布到 `/processed_distance`。
4. `alarm_monitor` 接收滤波结果，并判断距离是否低于报警阈值。
5. 如果距离过近，`alarm_monitor` 向 `/trigger_alarm` 发送服务请求。
6. `alarm_server` 接收请求并返回执行结果。

## 7. 项目编译

进入 M1-1 工作空间：

```bash
cd ~/smartcartest/M1/M1-1
```

加载 ROS 2 Humble 环境：

```bash
source /opt/ros/humble/setup.bash
```

编译接口包和功能包：

```bash
colcon build --packages-select sensor_interfaces sensor_nodes
```

编译完成后，加载工作空间环境：

```bash
source install/setup.bash
```

## 8. 项目运行

需要打开四个独立终端。

每个终端都需要先执行：

```bash
source /opt/ros/humble/setup.bash
source ~/smartcartest/M1/M1-1/install/setup.bash
```

### 终端一：启动报警服务端

```bash
ros2 run sensor_nodes alarm_server
```

### 终端二：启动传感器数据发布节点

```bash
ros2 run sensor_nodes sensor_publisher
```

### 终端三：启动传感器数据滤波节点

```bash
ros2 run sensor_nodes sensor_processor
```

### 终端四：启动报警监控节点

```bash
ros2 run sensor_nodes alarm_monitor
```

## 9. 功能验证

### 9.1 查看运行节点

```bash
ros2 node list
```

用于查看当前运行的 ROS 2 节点。

### 9.2 验证原始传感器数据

```bash
ros2 topic echo /sensor_data
```

用于查看传感器发布节点输出的数据。

### 9.3 验证滤波结果

```bash
ros2 topic echo /processed_distance
```

用于查看传感器数据处理节点输出的滤波结果。

### 9.4 查看话题信息

```bash
ros2 topic info /sensor_data
ros2 topic info /processed_distance
```

用于查看话题类型以及发布者、订阅者数量。

### 9.5 查看报警服务

```bash
ros2 service list
```

查看服务类型：

```bash
ros2 service type /trigger_alarm
```

### 9.6 手动调用报警服务

```bash
ros2 service call /trigger_alarm sensor_interfaces/srv/TriggerAlarm "{}"
```

用于测试报警服务端能否正常接收请求并返回响应。

### 9.7 验证报警监控功能

默认报警阈值为 0.3 m，传感器默认发布距离为 0.5 m。

可以通过调整报警阈值进行测试：

```bash
ros2 run sensor_nodes alarm_monitor --ros-args -p alarm_threshold:=0.6
```

当滤波后的距离低于 0.6 m 时，报警监控节点将调用报警服务。

## 10. 项目总结

本项目完成了 ROS 2 自定义消息与服务接口的创建，以及传感器数据发布、数据滤波、报警监控和报警服务调用等功能。

通过 Topic 实现节点之间的连续数据传输，通过 Service 实现节点之间的请求与响应，完成了一个基本的传感器数据处理与报警系统。

项目将接口定义与节点功能分离，便于后续维护、调试和功能扩展。

