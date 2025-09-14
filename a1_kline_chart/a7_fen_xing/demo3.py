import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

# 1. 生成数据
np.random.seed(42)
X = np.random.rand(100, 3)  # 100个样本，3个特征
y = 2.5 + 1.5 * X[:, 0] + 0.8 * X[:, 1] - 0.7 * X[:, 2] + np.random.randn(100) * 0.1

# 2. 划分数据集
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. 创建并训练模型
model = LinearRegression()
model.fit(X_train, y_train)

# 4. 查看模型参数
print("系数:", model.coef_)
print("截距:", model.intercept_)

# 5. 评估模型
train_score = model.score(X_train, y_train)
test_score = model.score(X_test, y_test)
print(f"训练集R²: {train_score:.4f}")
print(f"测试集R²: {test_score:.4f}")

# 6. 预测新数据
new_data = np.array([[0.5, 0.3, 0.2]])
prediction = model.predict(new_data)
print(f"预测结果: {prediction[0]:.4f}")

# 7. 计算均方误差
y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
print(f"均方误差(MSE): {mse:.4f}")