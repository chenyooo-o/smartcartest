import unittest
import numpy as np  # 截图要求允许引入 numpy 进行验证

# 从你的主文件导入要测试的核心函数
from legacy_corr import calculate

class TestCorrelation(unittest.TestCase):

    # 1. 正常情况：完美正相关
    def test_perfect_positive_correlation(self):
        """测试 [1,2,3] 与 [2,4,6] 的相关系数应为 1.0"""
        xs = [1.0, 2.0, 3.0]
        ys = [2.0, 4.0, 6.0]
        
        n, mean_x, mean_y, r = calculate(xs, ys)
        
        # 验证手写算法的结果
        self.assertAlmostEqual(r, 1.0)
        # 与 numpy 对比验证（符合题目要求：允许用 numpy 验证）
        np_r = np.corrcoef(xs, ys)[0, 1]
        self.assertAlmostEqual(r, np_r)

    # 2. 正常情况：完美负相关
    def test_perfect_negative_correlation(self):
        """测试 [1,2,3] 与 [6,4,2] 的相关系数应为 -1.0"""
        xs = [1.0, 2.0, 3.0]
        ys = [6.0, 4.0, 2.0]
        
        n, mean_x, mean_y, r = calculate(xs, ys)
        
        self.assertAlmostEqual(r, -1.0)
        np_r = np.corrcoef(xs, ys)[0, 1]
        self.assertAlmostEqual(r, np_r)

    # 3. 异常情况：数据点不足（除零边界）
    def test_insufficient_data(self):
        """测试数据点少于2个时，应抛出 ValueError"""
        xs = [1.0]
        ys = [2.0]
        
        # 使用 assertRaises 来断言这里必定会抛出异常
        with self.assertRaises(ValueError) as context:
            calculate(xs, ys)
        
        # 顺便验证报错信息是否符合预期
        self.assertIn("至少需要两个数据点", str(context.exception))

    # 4. 异常情况：方差为 0（除零边界）
    def test_zero_variance(self):
        """测试某一列值完全相同时（方差为0），应抛出 ValueError"""
        xs = [1.0, 1.0, 1.0]  # 方差为0
        ys = [1.0, 2.0, 3.0]
        
        with self.assertRaises(ValueError) as context:
            calculate(xs, ys)
        
        self.assertIn("方差为0", str(context.exception))

# 测试入口
if __name__ == "__main__":
    unittest.main()