import yfinance as yf
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import MinMaxScaler
from scipy.optimize import least_squares
import matplotlib.pyplot as plt
from tqdm import tqdm

# ✅ Define Bayesian Regularized Neural Network
class BayesianFNN(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(BayesianFNN, self).__init__()
        self.hidden = nn.Linear(input_size, hidden_size)
        self.output = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        x = torch.tanh(self.hidden(x))  # Activation function
        return self.output(x)

# ✅ Compute Technical Indicators
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

# ✅ Train the Model
def train_model(model, X_train, y_train, epochs=50):
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    loss_function = nn.MSELoss()

    for epoch in range(epochs):
        optimizer.zero_grad()
        pred = model(X_train)
        loss = loss_function(pred, y_train)
        loss.backward()
        optimizer.step()

    return model

# ✅ Perform Backtesting
def backtest_stock(ticker):
    stock = yf.Ticker(ticker)
    df = stock.history(period="2y")  # Get 2 years of data
    df = add_technical_indicators(df)

    # Initialize lists for actual vs predicted prices
    actual_prices = []
    predicted_prices = []
    mape_values = []

    # Iterate through each day, train until that day, and predict the next day
    dates = df.index[df.index >= "2024-01-01"]  # Start from Jan 1st
    for i in tqdm(range(len(dates) - 1), desc=f"Backtesting {ticker}"):
        train_data = df[df.index < dates[i]]  # Train up to this day
        test_data = df.loc[dates[i + 1]]  # Predict this day

        # ✅ Use Separate Scalers for Features and Target
        feature_scaler = MinMaxScaler(feature_range=(-1, 1))  # For inputs
        target_scaler = MinMaxScaler(feature_range=(-1, 1))  # For close price

        # ✅ Fit feature scaler on input features
        X_train = train_data[['Low', 'High', 'Open', 'EMA_5', 'EMA_10', 'RSI', 'Williams_R', 'Stochastic_K', 'Stochastic_D']]
        feature_scaler.fit(X_train)

        # ✅ Fit target scaler only on 'Close' column
        y_train = train_data[['Close']]
        target_scaler.fit(y_train)

        # ✅ Transform input and target using their respective scalers
        X_train_scaled = feature_scaler.transform(X_train)
        y_train_scaled = target_scaler.transform(y_train)

        X_train_torch = torch.tensor(X_train_scaled, dtype=torch.float32)
        y_train_torch = torch.tensor(y_train_scaled, dtype=torch.float32)

        # ✅ Train model
        model = BayesianFNN(input_size=9, hidden_size=20, output_size=1)
        model = train_model(model, X_train_torch, y_train_torch)

        # ✅ Prepare test data correctly
        latest_data = test_data[['Low', 'High', 'Open', 'EMA_5', 'EMA_10', 'RSI', 'Williams_R', 'Stochastic_K', 'Stochastic_D']].values.reshape(1, -1)
        latest_data_scaled = feature_scaler.transform(latest_data)  # Apply correct feature scaler
        input_tensor = torch.tensor(latest_data_scaled, dtype=torch.float32)

        # ✅ Predict next day's closing price
        with torch.no_grad():
            predicted_scaled = model(input_tensor).numpy()[0][0]

        # ✅ Denormalize prediction using target scaler
        predicted_price = target_scaler.inverse_transform([[predicted_scaled]])[0][0]

        # ✅ Store results
        actual_prices.append(test_data['Close'])
        predicted_prices.append(predicted_price)

        # ✅ Compute individual MAPE
        mape = 100 * np.abs((test_data['Close'] - predicted_price) / test_data['Close'])
        mape_values.append(mape)

    # ✅ Compute final MAPE for this stock
    final_mape = np.mean(mape_values)

    return actual_prices, predicted_prices, mape_values, final_mape

# ✅ Run Backtest for Multiple Stocks
tickers = ["AAPL", "MSFT", "BA", "BMO", "NVDA", "XOM", "HD"]
results = {}

for ticker in tickers:
    actual, predicted, individual_mape, final_mape = backtest_stock(ticker)
    results[ticker] = {"actual": actual, "predicted": predicted, "mape": final_mape}

    print(f"📊 {ticker} - Final MAPE: {final_mape:.2f}%")
    
    
    
# ✅ Compute average actual & predicted prices for each stock
stock_names = list(results.keys())
avg_actual = [np.mean(results[t]["actual"]) for t in stock_names]
avg_predicted = [np.mean(results[t]["predicted"]) for t in stock_names]

# ✅ Create a bar chart to compare averages
x = np.arange(len(stock_names))  # Label locations
width = 0.4  # Bar width

fig, ax = plt.subplots(figsize=(10, 6))
bars1 = ax.bar(x - width/2, avg_actual, width, label="Average Actual Price", color="blue", alpha=0.7)
bars2 = ax.bar(x + width/2, avg_predicted, width, label="Average Predicted Price", color="red", alpha=0.7)

# ✅ Labeling
ax.set_xlabel("Stock Ticker")
ax.set_ylabel("Average Stock Price")
ax.set_title("Comparison of Actual vs Predicted Stock Prices")
ax.set_xticks(x)
ax.set_xticklabels(stock_names)
ax.legend()

# ✅ Add values on top of bars
for bar in bars1 + bars2:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, height, f"{height:.2f}", ha='center', va='bottom')

# ✅ Show plot
plt.show()

# # ✅ Plot Histogram of Actual vs Predicted Prices
# plt.figure(figsize=(10, 5))
# all_actual = np.concatenate([results[t]["actual"] for t in tickers])
# all_predicted = np.concatenate([results[t]["predicted"] for t in tickers])

# plt.hist(all_actual, bins=20, alpha=0.5, label="Actual Prices", color="blue")
# plt.hist(all_predicted, bins=20, alpha=0.5, label="Predicted Prices", color="red")
# plt.xlabel("Stock Price")
# plt.ylabel("Frequency")
# plt.title("Histogram of Actual vs Predicted Prices (All Stocks)")
# plt.legend()
# plt.show()
