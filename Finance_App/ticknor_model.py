# -*- coding: utf-8 -*-
"""
Created on Sat Feb  1 01:57:54 2025

@author: andre
"""

# ticknor_model.py
import yfinance as yf
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timedelta
import pandas_market_calendars as mcal
# ✅ Define Ticknor's Neural Network
class TicknorNN(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(TicknorNN, self).__init__()
        self.hidden = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.output = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        x = self.relu(self.hidden(x))
        return self.output(x)


# ✅ List of U.S. Market Holidays (NYSE)
US_MARKET_HOLIDAYS = [
    "2025-01-01",  # New Year's Day
    "2025-01-20",  # Martin Luther King Jr. Day
    "2025-02-17",  # Presidents' Day
    "2025-04-18",  # Good Friday
    "2025-05-26",  # Memorial Day
    "2025-07-04",  # Independence Day
    "2025-09-01",  # Labor Day
    "2025-11-27",  # Thanksgiving Day
    "2025-12-25",  # Christmas Day
]

# ✅ Function to find the next valid trading day manually
def get_next_trading_day(start_date):
    next_day = start_date + timedelta(days=1)  # Start with the next day

    while next_day.weekday() >= 5 or next_day.strftime('%Y-%m-%d') in US_MARKET_HOLIDAYS:
        next_day += timedelta(days=1)  # Skip weekends & holidays

    return next_day.strftime('%A, %B %d, %Y')  # Format as "Day, Month DD, YYYY"



# ✅ Fetch Stock Data
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    df = stock.history(period="5y")  # Use all available data
    df['EMA_5'] = df['Close'].ewm(span=5, adjust=False).mean()
    df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
    df['RSI'] = compute_rsi(df['Close'])
    df['Williams_R'] = compute_williams_r(df)
    df['Stochastic_K'], df['Stochastic_D'] = compute_stochastic(df)
    return df.dropna()

# ✅ Compute RSI
def compute_rsi(series, period=14):
    delta = series.diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ✅ Compute Williams %R
def compute_williams_r(df, period=14):
    high = df['High'].rolling(window=period).max()
    low = df['Low'].rolling(window=period).min()
    return ((high - df['Close']) / (high - low)) * -100

# ✅ Compute Stochastic Oscillator %K and %D
def compute_stochastic(df, period=14):
    low_min = df['Low'].rolling(window=period).min()
    high_max = df['High'].rolling(window=period).max()
    stoch_k = 100 * ((df['Close'] - low_min) / (high_max - low_min))
    stoch_d = stoch_k.rolling(window=3).mean()
    return stoch_k, stoch_d

# ✅ Train Ticknor Model Optimally
def train_ticknor_model(X_train, y_train, input_size):
    model = TicknorNN(input_size, hidden_size=50, output_size=1)
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    loss_function = nn.MSELoss()

    X_train_torch = torch.tensor(X_train, dtype=torch.float32)
    y_train_torch = torch.tensor(y_train, dtype=torch.float32)

    for epoch in range(20):  # Optimized training
        optimizer.zero_grad()
        output = model(X_train_torch)
        loss = loss_function(output, y_train_torch)
        loss.backward()
        optimizer.step()

    return model

# ✅ Predict Using Ticknor Model
def predict_with_ticknor(ticker):
    df = get_stock_data(ticker)

    # ✅ Define feature columns
    feature_columns = ['Low', 'High', 'Open', 'EMA_5', 'EMA_10', 'RSI', 'Williams_R', 'Stochastic_K', 'Stochastic_D']
    target_column = ['Close']

    # ✅ Fit scalers properly
    feature_scaler = MinMaxScaler(feature_range=(-1, 1))
    target_scaler = MinMaxScaler(feature_range=(-1, 1))

    # ✅ Fit feature scaler on all feature columns
    X_train = df[feature_columns]
    feature_scaler.fit(X_train)

    # ✅ Fit target scaler on 'Close' column separately
    y_train = df[target_column]
    target_scaler.fit(y_train)

    # ✅ Scale training data correctly
    X_train_scaled = feature_scaler.transform(X_train)
    y_train_scaled = target_scaler.transform(y_train)

    # ✅ Train the model
    model = train_ticknor_model(X_train_scaled, y_train_scaled, input_size=9)

    # ✅ Prepare the latest data for prediction
    latest_data = df[feature_columns].iloc[-1].values.reshape(1, -1)

    # ✅ Scale latest data correctly
    latest_scaled = feature_scaler.transform(latest_data)

    # ✅ Convert to tensor and predict
    X_latest_torch = torch.tensor(latest_scaled, dtype=torch.float32)
    with torch.no_grad():
        predicted_scaled = model(X_latest_torch).numpy()[0][0]

    # ✅ Denormalize the prediction using target scaler
    predicted_price = target_scaler.inverse_transform([[predicted_scaled]])[0][0]

    # ✅ Determine the next trading day
    today = datetime.today()
    next_trading_day = get_next_trading_day(today + timedelta(days=1))

    return predicted_price, next_trading_day
