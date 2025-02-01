# -*- coding: utf-8 -*-
"""
Created on Sat Feb  1 01:08:00 2025

@author: andre
"""

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from scipy.optimize import least_squares
import matplotlib.pyplot as plt

# 1️⃣ Fetch Stock Data
def get_stock_data(ticker, period="5y"):
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)
    return df[['Open', 'High', 'Low', 'Close']]

# 2️⃣ Compute Technical Indicators
def add_technical_indicators(df):
    df['EMA_5'] = df['Close'].ewm(span=5, adjust=False).mean()
    df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
    df['RSI'] = compute_rsi(df['Close'])
    df['Williams_R'] = compute_williams_r(df)
    df['Stochastic_K'], df['Stochastic_D'] = compute_stochastic(df)
    return df.dropna()

# Compute RSI
def compute_rsi(series, period=14):
    delta = series.diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Compute Williams %R
def compute_williams_r(df, period=14):
    high = df['High'].rolling(window=period).max()
    low = df['Low'].rolling(window=period).min()
    return ((high - df['Close']) / (high - low)) * -100

# Compute Stochastic Oscillator %K and %D
def compute_stochastic(df, period=14):
    low_min = df['Low'].rolling(window=period).min()
    high_max = df['High'].rolling(window=period).max()
    stoch_k = 100 * ((df['Close'] - low_min) / (high_max - low_min))
    stoch_d = stoch_k.rolling(window=3).mean()
    return stoch_k, stoch_d

# 3️⃣ Prepare Data
df = get_stock_data("MSFT")  # Microsoft stock data
df = add_technical_indicators(df)

# Normalize Data
scaler = MinMaxScaler(feature_range=(-1, 1))
df_scaled = pd.DataFrame(scaler.fit_transform(df), columns=df.columns, index=df.index)

# Prepare input (X) and output (y)
X = df_scaled[['Low', 'High', 'Open', 'EMA_5', 'EMA_10', 'RSI', 'Williams_R', 'Stochastic_K', 'Stochastic_D']]
y = df_scaled[['Close']].shift(-1).dropna()  # Predict next day's close price
X = X.iloc[:-1]  # Align with y

# Split into training & testing
train_size = int(len(X) * 0.8)
X_train, X_test = X[:train_size], X[train_size:]
y_train, y_test = y[:train_size], y[train_size:]

# Convert to Torch Tensors
X_train_torch = torch.Tensor(X_train.values)
y_train_torch = torch.Tensor(y_train.values)
X_test_torch = torch.Tensor(X_test.values)
y_test_torch = torch.Tensor(y_test.values)

# 4️⃣ Define Bayesian Regularized Neural Network
class BayesianFNN(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(BayesianFNN, self).__init__()
        self.hidden = nn.Linear(input_size, hidden_size)
        self.output = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        x = torch.tanh(self.hidden(x))  # Activation function
        return self.output(x)

# ✅ Initialize Model & Optimizer
input_size = X_train.shape[1]
hidden_size = 15
output_size = 1

model = BayesianFNN(input_size, hidden_size, output_size)
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

# 5️⃣ Define Bayesian Loss Function with Dynamic Regularization
def bayesian_loss(pred, target, model, alpha, beta):
    mse_loss = torch.mean((pred - target) ** 2)  # Standard loss
    weight_penalty = sum(torch.sum(param ** 2) for param in model.parameters())  # Regularization
    return beta * mse_loss + alpha * weight_penalty

def compute_hessian(X, y, model):
    """Compute Gauss-Newton approximation of Hessian matrix."""
    pred = model(X)
    residuals = (pred - y).detach().numpy().flatten()
    
    def residual_function(weights):
        """Convert weights into tensor and compute residuals."""
        w = weights.copy()  # Copy weights array
        
        with torch.no_grad():
            for param in model.parameters():
                param_size = np.prod(param.shape)
                param_data = w[:param_size].reshape(param.shape)
                param.data = torch.tensor(param_data, dtype=torch.float32)
                w = w[param_size:]  # Update weight array
        
            return (model(X) - y).detach().numpy().flatten()

    initial_weights = np.concatenate([param.detach().numpy().flatten() for param in model.parameters()])

    # Define bounds to prevent "initial guess outside bounds" errors
    lower_bounds = np.full_like(initial_weights, -10.0)
    upper_bounds = np.full_like(initial_weights, 10.0)

    # Apply bounds in Levenberg-Marquardt
    result = least_squares(residual_function, initial_weights, method='lm')


    return result


# 7️⃣ Train Model with Levenberg-Marquardt Optimization
def train_model(model, X, y, epochs=100):
    alpha, beta = 0.01, 1.0  # Initial regularization parameters
    for epoch in range(epochs):
        optimizer.zero_grad()
        pred = model(X)
        loss = bayesian_loss(pred, y, model, alpha, beta)
        loss.backward()
        optimizer.step()

        # Compute Hessian
        hessian_result = compute_hessian(X, y, model)
        hessian_matrix = hessian_result.jac.T @ hessian_result.jac
        hessian_matrix += np.eye(hessian_matrix.shape[0]) * 1e-6  # Regularize Hessian

        # Compute gamma safely
        H_inv_trace = np.trace(np.linalg.inv(hessian_matrix))
        gamma = max(1e-6, min(X.shape[1], X.shape[1] - 2 * alpha * H_inv_trace))

        # Update α and β safely
        alpha = gamma / (2 * (sum(torch.sum(param ** 2).item() for param in model.parameters()) + 1e-6))
        beta = (X.shape[0] - gamma) / (2 * (loss.item() + 1e-6))
        
        # Prevent extreme values
        alpha = max(1e-6, min(alpha, 1e6))
        beta = max(1e-6, min(beta, 1e6))

        print(f"Epoch {epoch+1}/{epochs}, Loss: {loss.item():.5f}, α: {alpha:.5f}, β: {beta:.5f}")

    return model

# Train Model
train_model(model, X_train_torch, y_train_torch)

# 8️⃣ Predict & Compute MAPE
y_pred_torch = model(X_test_torch).detach().numpy()

# Reverse normalization
y_pred_actual = scaler.inverse_transform(
    np.column_stack([X_test, y_pred_torch]))[:, -1]
y_test_actual = scaler.inverse_transform(
    np.column_stack([X_test, y_test]))[:, -1]

# Compute Mean Absolute Percentage Error (MAPE)
mape = np.mean(100 * np.abs((y_test_actual - y_pred_actual) / y_test_actual))
print(f"📊 MAPE: {mape:.2f}%")

# 9️⃣ Visualize Predictions
plt.figure(figsize=(10, 5))
plt.plot(y_test_actual, label="Actual", color="blue")
plt.plot(y_pred_actual, label="Predicted", color="red", linestyle="--")
plt.xlabel("Sample")
plt.ylabel("Stock Price")
plt.title("Bayesian Regularized ANN Stock Prediction")
plt.legend()
plt.show()
