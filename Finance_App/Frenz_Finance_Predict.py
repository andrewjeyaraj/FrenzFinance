# -*- coding: utf-8 -*-
"""
Created on Fri Jan 31 16:44:46 2025

@author: andre
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from math import sqrt
from sklearn.metrics import mean_squared_error
import json
import os

# Streamlit App Title
st.title("Stock Price Prediction App")

st.markdown("""
### Welcome to the Stock Price Predictor! 🚀  
This app allows you to **forecast stock prices** using various models such as Auto-regressive Integrated Moving Average (ARIMA).  
Simply select a **stock ticker**, choose a **prediction model**, and enter the number of months to forecast.
""")

# Add a Disclaimer at the Top
st.caption("⚠️ **Disclaimer:** This app is for educational purposes only and does not provide financial advice.")


# Sidebar Information
st.sidebar.markdown("## About This App")
st.sidebar.write("""
This application uses **historical stock data** from Yahoo Finance to predict future stock prices.  
Predictions are based on statistical models and **should not be used for trading decisions**.
""")

st.sidebar.markdown("## 📌 How to Use")
st.sidebar.write("""
1. **Select a stock ticker** from the dropdown.
2. **Choose a prediction model** (e.g., ARIMA).
3. **Enter the number of months to forecast**.
4. **Click 'Predict' to generate future stock prices**.
""")

st.sidebar.markdown("---")  # Divider
# Select Stock Ticker
# Determine the correct file path (works locally & on Streamlit Cloud)
file_path = os.path.join(os.path.dirname(__file__), "company_tickers.json")

# Load ticker data safely
try:
    with open(file_path, "r") as file:
        tickers_data = json.load(file)

    # Extract tickers & company names
    tickers_list = [f"{data['ticker']} - {data['title']}" for data in tickers_data.values()]

# Improved Dropdown with Searchable List
    selected_ticker = st.selectbox("Select a Stock Ticker:", tickers_list)


# Extract the ticker symbol from selection
    ticker_symbol = selected_ticker.split(" - ")[0]
    st.write(f"✅ You selected: **{ticker_symbol}**")
#tickers = ["MSFT", "AAPL", "GOOG", "AMZN", "TSLA"]
#selected_ticker = st.selectbox("Select Ticker:", tickers)
except FileNotFoundError:
    st.error("Ticker file not found! Please contact admin.")
# Select Prediction Model
models = ["ARIMA", "SARIMA(Coming Soon)", "LSTM (Coming Soon)"]
selected_model = st.selectbox("Select Model:", models)

# Fetch Stock Data
st.subheader("Price History")
dat = yf.Ticker(ticker_symbol)
stock_data = dat.history(period="5y")

# Plot Historical Data
fig, ax = plt.subplots()
ax.plot(stock_data.index, stock_data['Close'], label='Close Price', color='blue')
ax.set_xlabel("Time")
ax.set_ylabel("Price")
ax.set_title(f"{selected_ticker} Closing Price History")
ax.legend()
st.pyplot(fig)

# Enter number of months to predict
n_predict = st.number_input("Enter No. of Months to Predict:", min_value=1, max_value=60, value=6, step=1)

# Checkbox to apply RMS Margin
apply_rms = st.checkbox("Apply RMS Margin")


# Add Explanation Before Prediction
st.markdown("""
## How Does This Work? 🤔  
- The model is trained using historical stock prices.
- It learns trends & patterns to estimate future prices.
- The **RMS margin option** helps account for uncertainty meaning that you can add ...
the average error in prediction found while training the model to the final price estimate
""")

# Predict button
if st.button("Predict"):
    
    # Train ARIMA model on full dataset
    model = ARIMA(stock_data['Close'], order=(15,1,0))
    model_fit = model.fit()
    
    # Forecast future prices
    forecast = model_fit.forecast(steps=n_predict)
    
    # Compute RMS if enabled
    if apply_rms:
        train_data = stock_data['Close'][:-n_predict]
        test_data = stock_data['Close'][-n_predict:]
        test_pred = model_fit.forecast(steps=len(test_data))
        rmse = sqrt(mean_squared_error(test_data, test_pred))
        forecast += rmse  # Apply RMSE margin
    
    # Generate future dates
    last_date = stock_data.index[-1]
    future_dates = [last_date + pd.DateOffset(months=i) for i in range(1, n_predict + 1)]
    
    # Convert forecast to DataFrame
    forecast_df = pd.DataFrame({'Date': future_dates, 'Forecast': forecast})
    forecast_df.set_index('Date', inplace=True)
    
    
    
    # Plot predictions
    st.subheader("Predicted Price")
    fig2, ax2 = plt.subplots()
    ax2.plot(stock_data.index, stock_data['Close'], label='Actual Data', color='blue')
    ax2.plot(forecast_df.index, forecast_df['Forecast'], label='Predicted Data', linestyle='--', marker='o', color='red')
    ax2.set_xlabel("Time")
    ax2.set_ylabel("Price")
    ax2.set_title(f"{selected_ticker} Predicted Closing Price")
    ax2.legend()
    st.pyplot(fig2)
    
    # After Showing the Prediction, Add an Interpretation Guide
    st.markdown("## 📊 Interpreting the Results")
    st.write("""
    - **The blue line** represents historical prices.
    - **The red dashed line** represents the predicted prices.
    - The **last predicted value** is the estimated closing price at the forecast horizon.
    """)
    
    # Display estimated closing price at the end of period
    st.markdown("""
    ### 📢 **Estimated Closing Price at End of Period**  
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="font-size:24px; font-weight:bold; color:green;">
        ${forecast_df['Forecast'].iloc[-1]:,.2f} USD
    </div>
    """, unsafe_allow_html=True)
    # Final Disclaimer at the Bottom
    st.caption("🚨 **This prediction is not financial advice. Always conduct your own research before investing.**")
    
    
# Clear button
if st.button("Clear"):
    st.rerun()
