# M1-2：双机器人传感器系统启动编排

## 1. 项目简介

本项目基于 ROS 2 Humble，使用 Python Launch 实现双机器人传感器系统的统一启动与管理。

项目在 M1-1 已完成的传感器发布、数据处理和报警功能基础上，进一步实现：

- 使用 Python Launch 文件一键启动整个系统。
- 使用 `robot1` 和 `robot2` 命名空间，实现双机器人节点隔离。
- 使用 YAML 文件分别配置不同机器人的报警阈值。
- 使用 `TimerAction` 延迟启动报警监测节点。
- 启动前检查参数文件是否存在，缺失时给出明确错误提示。

## 2. 项目目录结构

```text
M1-2/
├── src/
│   └── sensor_bringup/
│       ├── config/
│       │   ├── robot1.yaml
│       │   └── robot2.yaml
│       ├── launch/
│       │   └── bringup.launch.py
│       ├── resource/
│       │   └── sensor_bringup
│       ├── package.xml
│       ├── setup.py
│       └── setup.cfg
└── README.md
```

## 3. 系统节点组成

系统包含两组机器人节点和一个共享报警服务端，共计 7 个 ROS 2 节点。

| 节点 | 所属 | 功能 |
|---|---|---|
| sensor_publisher | robot1、robot2 | 发布传感器数据 |
| node_b_filter | robot1、robot2 | 接收传感器数据并进行滤波处理 |
| alarm_monitor | robot1、robot2 | 监测处理后的距离，判断是否触发报警 |
| alarm_server | 共享 | 提供报警服务，处理报警请求 |

两组机器人分别使用独立的命名空间和话题，报警监测节点共用 `/trigger_alarm` 服务。

## 4. 命名空间与话题配置

系统使用 `namespace` 和 `remappings` 区分两组机器人的节点和话题。

| 功能 | robot1 | robot2 |
|---|---|---|
| 传感器数据 | `/robot1/sensor_data` | `/robot2/sensor_data` |
| 处理后数据 | `/robot1/processed_distance` | `/robot2/processed_distance` |
| 发布节点 | `/robot1/sensor_publisher` | `/robot2/sensor_publisher` |
| 处理节点 | `/robot1/node_b_filter` | `/robot2/node_b_filter` |
| 报警节点 | `/robot1/alarm_monitor` | `/robot2/alarm_monitor` |

通过命名空间隔离，可以避免不同机器人之间的节点名称和话题名称发生冲突。

## 5. 参数配置

系统使用 YAML 文件分别配置两个机器人的报警阈值。

### robot1.yaml

```yaml
/**:
  ros__parameters:
    alarm_threshold: 0.3
```

### robot2.yaml

```yaml
/**:
  ros__parameters:
    alarm_threshold: 0.6
```

Launch 文件通过 `parameters` 参数将对应的 YAML 文件加载到报警监测节点。

这种方式将参数配置与程序代码分离，便于针对不同机器人调整运行参数。

## 6. Launch 启动编排

核心启动文件：

```text
launch/bringup.launch.py
```

该文件主要完成以下工作：

1. 获取 `sensor_bringup` 功能包的安装目录。
2. 定位 robot1 和 robot2 对应的 YAML 参数文件。
3. 检查参数文件是否存在，缺失时抛出 `FileNotFoundError`。
4. 分别启动两组机器人的传感器发布节点。
5. 分别启动两组机器人的数据处理节点。
6. 使用 `TimerAction` 设置 3 秒延迟，启动两组报警监测节点。
7. 启动共享的 `alarm_server` 服务端。

其中，3 秒延迟用于让传感器发布和处理节点先启动。这是一种基于时间的启动安排，并非严格的节点就绪检测。

## 7. 编译环境与方法

### 7.1 环境要求

- 操作系统：Ubuntu
- ROS 版本：ROS 2 Humble
- 编程语言：Python 3
- 构建工具：colcon

### 7.2 加载 ROS 2 环境

```bash
source /opt/ros/humble/setup.bash
```

### 7.3 进入 M1-2 工作空间

```bash
cd ~/smartcartest/M1/M1-2
```

### 7.4 编译工作空间

```bash
colcon build
```

## 8. 系统启动方法

由于 M1-2 调用 M1-1 中的传感器节点，需要先加载 ROS 2 和两个工作空间的环境。

```bash
source /opt/ros/humble/setup.bash
source ~/smartcartest/M1/M1-1/install/setup.bash
source ~/smartcartest/M1/M1-2/install/setup.bash
```

启动整个系统：

```bash
ros2 launch sensor_bringup bringup.launch.py
```

停止系统：

```bash
Ctrl + C
```

## 9. 系统验证方法

### 9.1 查看节点列表

在另一个终端加载相同环境后执行：

```bash
ros2 node list
```

预期可以看到以下 7 个节点：

```text
/alarm_server
/robot1/alarm_monitor
/robot1/node_b_filter
/robot1/sensor_publisher
/robot2/alarm_monitor
/robot2/node_b_filter
/robot2/sensor_publisher
```

### 9.2 验证 robot1 参数

```bash
ros2 param get /robot1/alarm_monitor alarm_threshold
```

预期结果：

```text
Double value is: 0.3
```

### 9.3 验证 robot2 参数

```bash
ros2 param get /robot2/alarm_monitor alarm_threshold
```

预期结果：

```text
Double value is: 0.6
```

### 9.4 验证数据处理与报警功能

启动系统后，可以观察终端输出：

- `sensor_publisher` 持续发布传感器距离数据。
- `node_b_filter` 接收数据并输出滤波结果。
- `alarm_monitor` 根据配置的报警阈值判断是否需要报警。
- `alarm_server` 接收报警请求并返回处理结果。

### 9.5 验证参数文件缺失检查

临时移除安装目录中的参数文件：

```bash
cd ~/smartcartest/M1/M1-2

mv install/sensor_bringup/share/sensor_bringup/config/robot1.yaml \
   install/sensor_bringup/share/sensor_bringup/config/robot1.yaml.bak
```

重新启动：

```bash
ros2 launch sensor_bringup bringup.launch.py
```

预期出现：

```text
FileNotFoundError: Parameter file not found
```

测试结束后恢复文件：

```bash
mv install/sensor_bringup/share/sensor_bringup/config/robot1.yaml.bak \
   install/sensor_bringup/share/sensor_bringup/config/robot1.yaml
```

## 10. 主要实现成果

本项目完成了以下功能：

1. 实现 Python Launch 一键启动双机器人传感器系统。
2. 实现两组机器人节点的命名空间隔离。
3. 实现不同机器人的独立话题映射。
4. 实现通过 YAML 文件加载不同报警阈值。
5. 实现报警监测节点延迟启动。
6. 实现参数文件存在性检查和错误提示。
7. 实现两个机器人共用一个报警服务端。

通过以上工作，完成了双机器人传感器系统的启动编排与参数管理。
