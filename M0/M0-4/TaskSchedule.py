#导入依赖与颜色定义
import argparse
import yaml
import json
import time
import random
import sys

# 定义控制台彩色输出的 ANSI 转义码
# 绿/红/黄/蓝/重置
COLOR_GREEN = '\033[92m'
COLOR_RED = '\033[91m'
COLOR_YELLOW = '\033[93m'
COLOR_BLUE = '\033[94m'
COLOR_RESET = '\033[0m'


#彩色打印函数
def print_colored(text, color):
    """
    彩色打印函数。
    考核点：彩色输出注意在非 TTY 环境（如重定向到文件）降级，否则全是乱码
    """
    # 如果不是终端环境（如重定向到文件），就普通打印，不输出颜色代码
    if not sys.stdout.isatty():
        print(text)
        return
    # 终端环境，输出带颜色的文本
    print(f"{color}{text}{COLOR_RESET}")


#命令行参数解析
def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="命令行任务调度模拟器")
    # --config 必填项，指定任务的配置文件路径
    parser.add_argument("--config", required=True, help="任务配置文件 (.yaml/.yml/.json)")
    # --timeout 选填项，用于覆盖配置文件里的全局超时时间
    parser.add_argument("--timeout", type=float, help="全局超时时间，覆盖配置文件")
    # --report 选填项，默认输出为 report.json
    parser.add_argument("--report", default="report.json", help="报告输出路径，默认 report.json")
    # --seed 选填项，设置随机种子以保证结果可复现
    parser.add_argument("--seed", type=int, help="随机种子，便于复现结果")
    return parser.parse_args()


#配置文件加载和异常拦截
def load_config(config_path):
    """加载并解析配置文件，拦截文件不存在和语法错误"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            # 判断是 json 还是 yaml 格式，分别调用对应的解析函数
            if config_path.endswith('.json'):
                return json.load(f)
            else:
                return yaml.safe_load(f)
    except FileNotFoundError:
        # 考核点：给出可读错误提示并以非 0 退出
        print(f"错误：找不到文件 {config_path}")
        sys.exit(1)
    except Exception as e:
        # 捕获语法错误等异常
        print(f"错误：配置文件解析失败 ({e})")
        sys.exit(1)


#配置合法性检验
def validate_config(config_data):
    """校验配置合法性（异常输入拦截）"""
    # 检查配置是否为空或缺少 tasks 字段
    if not config_data or "tasks" not in config_data:
        print("错误：配置文件格式错误，缺少 tasks 字段")
        sys.exit(1)
        
    tasks = config_data["tasks"]
    # 检查任务列表是否为空
    if not tasks:
        print("错误：任务列表为空")
        sys.exit(1)
        
    task_names = set() #创建一个空集合，备用
    for t in tasks:
        name = t.get("name")
        # 检查任务是否有名字
        if not name:
            print("错误：存在没有 name 的任务")
            sys.exit(1)
        # 检查任务名是否唯一
        if name in task_names:
            print(f"错误：任务名重复 ({name})")
            sys.exit(1)
        task_names.add(name)
        
        # 检查 success_rate 是否在 0~1 之间
        rate = t.get("success_rate", 1.0) #若无success_rate，默认值给1.0
        if not (0.0 <= rate <= 1.0):
            print(f"错误：任务 {name} 的 success_rate 越界")
            sys.exit(1)
            
    # 检查依赖的任务是否存在
    for t in tasks:
        for dep in t.get("dependencies", []):
            if dep not in task_names:
                print(f"错误：任务 {t['name']} 依赖了不存在的任务 {dep}")
                sys.exit(1)
                
    # 依赖关系初步校验完毕后，调用拓扑排序来检测是否有依赖环
    get_topological_order(tasks)


#拓扑排序与环检测
def get_topological_order(tasks):
    """利用拓扑排序（Kahn算法）获取执行顺序，并检测依赖环"""
    # 1. 新建空字典
    in_degree = {} #我依赖谁
    graph = {} #谁依赖我

    # 2. 循环所有任务，初始化两个字典（代替 {t["name"]:0 for t in tasks}）
    for t in tasks:
        task_name = t["name"]
        in_degree[task_name] = 0    # 每个任务初始入度=0
        graph[task_name] = []       # 每个任务对应的空列表

    # 3. 构建图、统计入度
    for t in tasks:
        task_name = t["name"]
        # 获取当前任务的依赖列表，没有dependencies就用空列表
        dep_list = t.get("dependencies", []) #在t里面找dependencies这个key，如果没有，就给一个空列表
        # 循环每一个前置依赖dep
        for dep in dep_list:
            # dep做完之后才能做task_name，所以dep指向task_name
            graph[dep].append(task_name) #例：graph["A"].append("B")，A做完之后可以跑B
            # 当前任务的入度 +1（多了一个前置依赖）
            in_degree[task_name] = in_degree[task_name] + 1
            
    # 找出所有入度为 0 的节点（也就是没有前置依赖的任务），加入队列
    queue = []   # 新建空队列，放现在就能直接跑的任务
    for name, deg in in_degree.items():
        # name：任务名字，deg：这个任务的入度（还有几个前置没做完）
        if deg == 0:
            # 入度=0，代表没有前置依赖，可以立刻执行
            queue.append(name)
    order = []
    
    # 开始 BFS 式的拓扑排序
    while queue: #只要队列quene里面还有任务，就一直循环
        current = queue.pop(0) #取出队列最前面第1个元素，并且把它从 queue 里删掉，存到current变量（正在处理的任务名字）
        order.append(current) # 加入执行顺序列表
        
        # 将依赖当前任务的后续任务的入度减 1
        for neighbor in graph[current]: #挨个取出current的每一个后继任务，放到变量neighbor
            in_degree[neighbor] -= 1
            # 如果减到 0，说明该任务的前置都做完了，可以加入队列
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
                
    # 如果排出来的顺序数量不等于总任务数，说明剩下的事互相依赖，形成了环
    if len(order) != len(tasks):
        print("错误：检测到依赖环，无法执行调度")
        sys.exit(1)
        
    return order


#核心调度逻辑
def run_scheduler(tasks, task_order, timeout, seed):
    """核心调度逻辑"""
    if seed is not None:
        random.seed(seed) # 设置随机种子，便于复现结果
        
    task_dict = {}  # 创建空字典
    for t in tasks:
        task_name = t["name"]
        task_dict[task_name] = t
    results = {}
    total_duration = 0.0
    is_timeout = False #未超时
    
    # 初始化所有任务的状态为 PENDING
    for t in tasks:
        results[t["name"]] = {
            "name": t["name"],
            "status": "PENDING",
            "attempts": 0,
            "duration": 0.0,
            "started_at": None,
            "ended_at": None
        }

    # 按照拓扑排序的顺序依次执行任务
    for name in task_order:
        task = task_dict[name]
        
        # 1. 检查依赖的传播规则：如果任一前置任务是 FAILED/SKIPPED/TIMEOUT，则当前任务标记为 SKIPPED
        dep_failed = False
        dep_list = task.get("dependencies", []) #当前任务的所有前置依赖任务清单
        for dep in dep_list: #逐个取出每一个前置任务
            status = results[dep]["status"]
            if status == "FAILED" or status == "SKIPPED" or status == "TIMEOUT":
                dep_failed = True
                break
        if dep_failed:
            results[name]["status"] = "SKIPPED"
            print_colored(f"[SKIPPED] {name} (前置任务失败)", COLOR_BLUE)
            continue

            
        # 2. 超时判定（执行前检查一次）
        if total_duration >= timeout:
            is_timeout = True
            results[name]["status"] = "TIMEOUT"
            print_colored(f"[TIMEOUT] {name}", COLOR_BLUE)
            continue
            
        # 3. 任务执行与重试逻辑（最多 3 次尝试）
        max_attempts = 3
        success = False
        
        for attempt in range(1, max_attempts + 1):
            # 重试前也要检查超时
            if total_duration >= timeout:
                is_timeout = True
                break
                
            results[name]["attempts"] = attempt
            # 第一次尝试不打印 RETRY，第 2、3 次尝试打印黄色提示
            if attempt > 1:
                print_colored(f"[RETRY] {name} (第 {attempt} 次尝试)", COLOR_YELLOW)
                
            results[name]["started_at"] = time.time()
            
            # 模拟耗时（题目要求 sleep(duration)）
            time.sleep(task["duration"])
            task_time = task["duration"]
            total_duration += task_time
            results[name]["duration"] += task_time
            results[name]["ended_at"] = time.time()
            
            # 判定成败：随机数与成功率比较
            if random.random() < task["success_rate"]:
                success = True
                break
                
        # 4. 更新最终状态
        if is_timeout:
            # 如果因为超时打破了重试循环
            results[name]["status"] = "TIMEOUT"
            print_colored(f"[TIMEOUT] {name}", COLOR_RED)
        elif success:
            results[name]["status"] = "SUCCESS"
            print_colored(f"[SUCCESS] {name} (尝试 {results[name]['attempts']} 次)", COLOR_GREEN)
        else:
            results[name]["status"] = "FAILED"
            print_colored(f"[FAILED] {name} (尝试 {results[name]['attempts']} 次后仍失败)", COLOR_RED)
            
        # 如果触发超时，立即终止所有任务，跳出主循环
        if is_timeout:
            break
            
    # 如果超时了，把后面还没执行（状态还是 PENDING）的任务全部标记为 TIMEOUT
    if is_timeout:
        for name in task_order:
            if results[name]["status"] == "PENDING":
                results[name]["status"] = "TIMEOUT"
                print_colored(f"[TIMEOUT] {name} (全局超时未执行)", COLOR_BLUE)
                
    return results, total_duration, is_timeout


#生成运行报告
def generate_report(report_path, original_tasks, results, total_duration, is_timeout):
    """生成结构完整的 report.json"""
    report_tasks = []
    # 考核点：tasks 中必须包含配置文件里的每一个任务
    # 注意这里遍历 original_tasks（原始配置顺序），而不是拓扑排序后的顺序
    for t in original_tasks:
        report_tasks.append(results[t["name"]])
        
    # 构造最终的报告字典
    report_data = {
        "timeout": is_timeout,          # 是否超时
        "total_duration": round(total_duration, 2), # 总耗时（保留两位小数）
        "tasks": report_tasks           # 所有任务的状态信息
    }
    
    try:
        # 写入 JSON 文件
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        print(f"\n报告已生成：{report_path}")
    except Exception as e:
        print(f"写入报告失败：{e}")


#主程序
def main():
    """主程序入口"""
    # 1. 解析命令行参数
    args = parse_args()
    
    # 2. 加载与校验配置（里面包含了异常处理、合法性校验、拓扑排序检测环）
    config = load_config(args.config)
    validate_config(config)
    
    tasks = config["tasks"]
    
    # 3. 确定超时时间
    # 优先级：命令行 --timeout 传入的值 > 配置文件里的 timeout > 默认无穷大
    timeout = args.timeout if args.timeout is not None else config.get("timeout", float('inf'))
    
    # 4. 获取执行顺序（拓扑排序）
    task_order = get_topological_order(tasks)
    
    # 5. 运行调度器（核心逻辑）
    results, total_duration, is_timeout = run_scheduler(tasks, task_order, timeout, args.seed)
    
    # 6. 生成报告
    generate_report(args.report, tasks, results, total_duration, is_timeout)

# Python 标准入口保护
if __name__ == "__main__":
    main()  