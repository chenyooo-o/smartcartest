#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sensor_analyzer.py  —— 上一届学长留下的"能用"的脚本

注释（学长原话）：
    "处理一下传感器数据就能用"

原本意图：
    1. 读取 sensor_data.csv（列：time, value）
    2. 计算 value 的平均值、标准差
    3. 剔除离群值（|value - mean| > 2 * std）
    4. 把清洗后的数据保存为 cleaned_data.csv
    5. 打印一份统计摘要

现状：跑不通 / 跑出来数不对。就交给你了。
"""

import csv
import os
import math

INPUT_FILE = "sensor_data.csv"
OUTPUT_FILE = "cleaned_data.csv"
OUTPUT_DIR = "out"  # 输出目录

data = []
times = []
cleaned_values = []
cleaned_times = []

print("=== 传感器数据分析 ===")

# --- 读取数据 ---
if not os.path.exists(INPUT_FILE):
    print(f"错误：{INPUT_FILE}不存在")

reader = csv.DictReader(open(INPUT_FILE, "r"))
if "time" not in reader.fieldnames or "value" not in reader.fieldnames:
    print("列名不符，需包含time和value列")
    return

for row in reader:
    t = float(row["time"])
    v = float(row["value"])
    times.append(t)
    data.append(v)

    if ValueError:
        print("错误：第{row_num}行含非数值内容")


if not data:
    print("错误：该文件为空文件")
    return

print("共读取 %d 条数据" % len(data))

# --- 计算平均值 ---
total = 0
for v in data:
    total += v
mean = total / len(data)

# --- 计算标准差 ---
acc = 0
for v in data:
    acc += (v - mean)**2
var = acc / len(data)
std = math.sqrt(var)

# --- 剔除离群值 ---   原代码中for循环按下标遍历，后续元素前移，可能遗漏离群值
for v,t in zip(data,times):
    if abs(v-mean) <= 2*std:
        cleaned_values.append(v)
        cleaned_times.append(t)
        
# --- 输出清洗后的数据 --- 
os.makedirs(OUTPUT_DIR,exist_ok=True) #新建文件夹，若文件夹已存在，不报错，继续往下运行代码
output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
f = open(output_path, "w")
writer = csv.writer(f)
writer.writerow(["time", "value"])
for t,v in zip(cleaned_times,cleaned_values):
    writer.writerow([t,v])

print("均值 mean = %.4f" % mean)
print("标准差 std = %.4f" % std)
print("清洗后剩余 %d 条" % len(cleaned_values))
print("已保存到 %s" % output_path)
