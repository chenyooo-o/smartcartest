import yaml
import csv
import math

CONFIG_PATH = "config.yaml"

def load_config(config_path): #读懂.yaml配置
    """
    读取并解析 YAML 配置文件。
    
    :param config_path: 配置文件路径
    :return: 配置字典
    :raises FileNotFoundError: 文件不存在
    :raises yaml.YAMLError: YAML 格式错误
    """
    try:
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"错误：找不到配置文件{config_path}")
        
    except yaml.YAMLError as e:
        print(f"错误：解析配置文件失败：{e}")
        raise

def read_data(csv_path,col_x,col_y):#读取.csv数据
    """
    从 CSV 文件中读取指定两列的数据。
    
    :param csv_path: CSV 文件路径
    :param col_x: X 轴列名
    :param col_y: Y 轴列名
    :return: 两个浮点数列表 (xs, ys)
    :raises FileNotFoundError: CSV 文件不存在
    :raises KeyError: 指定的列名不存在
    :raises ValueError: 数据无法转换为浮点数
    """
    xs = []
    ys = []
    try:
        with open(csv_path) as f:
            reader =csv.DictReader(f)
            for row_num,row in reader:
                try:
                    xs.append(float(row[col_x]))
                    ys.append(float(row[col_y]))
                except KeyError as e:
                    print(f"错误：CSV中找不到列名{e}第{row_num}行")
                    raise
                except ValueError:
                    print(f"错误：第{row_num}行数据无法转换为数字")
                    raise
    except FileNotFoundError:
        print(f"错误：找不到数据文件{csv_path}")
        raise
    return xs,ys
    
def calculate(xs,ys):#计算相关系数
    """
    计算相关系数
    公式: r = sum((x-mean_x)*(y-mean_y)) / sqrt(sum((x-mean_x)^2) * sum((y-mean_y)^2))
    
    :param xs: X 轴数据列表
    :param ys: Y 轴数据列表
    :return: n, mean_x, mean_y, r
    :raises ValueError: 数据点少于 2 个，或方差为 0
    """
    n = len(xs)
    if n<2:
        raise ValueError("错误：至少需要两个数据点才能计算相关系数")

    # 1. 计算均值
    sum_x = 0.0
    sum_y = 0.0
    for i in range(n):
        sum_x = sum_x + xs[i]
        sum_y = sum_y + ys[i]

    mean_x = sum_x / n
    mean_y = sum_y / n

    # 2. 计算方差
    dx = 0.0
    dy = 0.0
    prod = 0.0
    for i in range(n):
        a = xs[i] - mean_x
        b = ys[i] - mean_y
        dx = dx + a * a
        dy = dy + b * b
        prod = prod + a * b

    # 3. 除零
    if dx==0.0 or dy==0.0:
        raise ValueError("错误：X或Y列的方差为0,无法计算相关系数")

    # 4. 计算相关系数 
    denom = math.sqrt(dx * dy)
    r = prod / denom
    return n,mean_x,mean_y,r

def main(): #主函数，读取配置->读取数据->计算->打印结果
    try:
        cfg = load_config(CONFIG_PATH)
        csv_path = cfg["input_csv"]
        col_x = cfg["columns"]["x"]
        col_y = cfg["columns"]["y"]

        xs,ys = read_data(csv_path,col_x,col_y)
        n,mean_x,mean_y,r = calculate(xs,ys)

        print("n =", n)
        print("mean_x =", mean_x)
        print("mean_y =", mean_y)
        print("r =", r)
    except Exception as e:
        print(f"程序运行失败：{e}")

if __name__=="__main__":
    main() #启动程序
