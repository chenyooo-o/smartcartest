import yaml
import csv
import math

CONFIG_PATH = "config.yaml"

def load_config(config_path): #读懂.yaml配置
    try:
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"错误：找不到配置文件{config_path}")
        
    except yaml.YAMLError as e:
        print(f"错误：解析配置文件失败：{e}")
        raise

def read_data(csv_path,col_x,col_y):#读取.csv数据
    
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
    n = len(xs)
    if n<2:
        raise ValueError("错误：至少需要两个数据点才能计算相关系数")
    
    sum_x = 0.0
    sum_y = 0.0
    for i in range(n):
        sum_x = sum_x + xs[i]
        sum_y = sum_y + ys[i]

    mean_x = sum_x / n
    mean_y = sum_y / n

    dx = 0.0
    dy = 0.0
    prod = 0.0
    for i in range(n):
        a = xs[i] - mean_x
        b = ys[i] - mean_y
        dx = dx + a * a
        dy = dy + b * b
        prod = prod + a * b

    if dx==0.0 or dy==0.0:
        raise ValueError("错误：X或Y列的方差为0,无法计算相关系数")
    
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
