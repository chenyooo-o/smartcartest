# M0-2 

## 1. 如何运行

创建uv虚拟环境 uv venv
激活虚拟环境source .venv/bin/activate
初始化uv项目配置文件uv init
添加依赖uv add numpy pyyaml
终端中进入目录python3 legacy_corr.py --config config.yaml

## 2.输入格式
1. YAML 配置文件 (config.yaml)
包含以下内容：
input_csv: 指定输入的 CSV 文件名（支持相对路径）。
columns: 一个字典，包含需要计算的两列的列名。
x: X 轴的列名（如 "sensor_a"）。
y: Y 轴的列名（如 "sensor_b"）。

利用 os.path.abspath 进行了优化。若 input_csv 填写的是相对路径，程序会以 YAML 配置文件所在的目录为基准去寻找 CSV 文件，确保在跨目录调用时不会迷路。

2. CSV 数据文件
文件必须包含表头。
表头中必须包含 YAML 中 x 和 y 所指定的列名，且列名大小写、拼写必须完全一致。
指定的列中必须全是能够转换为浮点数的数据格式，不能包含字母或乱码。

## 3.输出含义
1. 
n = <数值>：参与计算的样本数量（数据行数）。
mean_x = <数值>：X 轴数据的算术平均值。
mean_y = <数值>：Y 轴数据的算术平均值。
r = <数值>：皮尔逊相关系数（Pearson Correlation Coefficient）。

2. 
关于相关系数 r 的解读：
取值范围：-1.0 ≤ r ≤ 1.0
r > 0：正相关。越接近 1.0，正相关性越强。
r < 0：负相关。越接近 -1.0，负相关性越强。
r ≈ 0：无明显线性相关关系。

## 4.ai使用情况
1. ai 提供了 try-except 的范式，在此基础上，我补充了 exit(1) 逻辑，确保不抛出 Traceback。
2. 尝试运行是报错：找不到config.yaml文件，问了ai，是因为程序以终端当前目录去找csv文件，提示我加上os.path.abspath