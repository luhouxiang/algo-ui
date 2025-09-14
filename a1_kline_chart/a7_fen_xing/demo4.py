import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import talib
# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


# 生成单变量数据
np.random.seed(42)
X = np.random.rand(50, 1) * 10  # 单个特征
y = 2.5 * X.ravel() + 1.2 + np.random.randn(50) * 2  # 添加噪声

# 训练模型
model = LinearRegression()
model.fit(X, y)

# 预测值
X_fit = np.linspace(0, 10, 100).reshape(-1, 1)
y_fit = model.predict(X_fit)

# 绘制图形
plt.figure(figsize=(10, 6))
plt.scatter(X, y, color='blue', label='实际数据')
plt.plot(X_fit, y_fit, color='red', linewidth=2, label='回归线')
plt.title('单变量线性回归可视化', fontsize=15)
plt.xlabel('特征X', fontsize=12)
plt.ylabel('目标y', fontsize=12)
plt.legend(fontsize=12)

# 显示回归方程
equation = f'y = {model.coef_[0]:.2f}x + {model.intercept_:.2f}'
plt.text(0.5, 25, equation, fontsize=14, bbox=dict(facecolor='white', alpha=0.8))

plt.grid(True)
plt.show()