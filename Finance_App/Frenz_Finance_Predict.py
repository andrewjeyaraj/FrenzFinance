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
import plotly.express as px
import plotly.graph_objects as go
from ticknor_model import predict_with_ticknor
from datetime import datetime, timedelta
import pandas_market_calendars as mcal

# Streamlit App Title
st.title("Stock Price Prediction App")

st.markdown("""
### Welcome to the Stock Price Predictor! 🚀  
This app allows you to **forecast stock prices** using various models such as Auto-regressive Integrated Moving Average (ARIMA).  
Simply select a **stock ticker**, choose a **prediction model**, and enter the number of months to forecast.
""")

# Add a Disclaimer at the Top
st.caption("⚠️ **Disclaimer:** This app is for educational purposes only and does not provide financial advice.")



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
models = ["ARIMA", "Ticknor (2013)", "SARIMA(Coming Soon)", "LSTM (Coming Soon)"]
selected_model = st.selectbox("Select Model:", models)


if selected_model=="ARIMA":
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
    

    # Fetch Stock Data
    st.subheader("Price History")
    dat = yf.Ticker(ticker_symbol)
    stock_data = dat.history(period="5y")
    
    # Plot Historical Data
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=stock_data.index, 
        y=stock_data['Close'], 
        mode='lines',
        name='Close Price',
        line=dict(color='blue'),
        hovertemplate="Date: %{x}<br>Price: %{y:.2f} USD"
    ))
    
    # Update layout to match original Matplotlib style
    fig.update_layout(
        title=f"{selected_ticker} Closing Price History",
        xaxis_title="Time",
        yaxis_title="Price",
        hovermode="x unified",
        template="plotly_white"
    )
    
    # Show in Streamlit
    st.plotly_chart(fig, use_container_width=True)
    # fig, ax = plt.subplots()
    # ax.plot(stock_data.index, stock_data['Close'], label='Close Price', color='blue')
    # ax.set_xlabel("Time")
    # ax.set_ylabel("Price")
    # ax.set_title(f"{selected_ticker} Closing Price History")
    # ax.legend()
    # st.pyplot(fig)
    
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
        with st.status("⏳ Computing... This can take up to a minute", expanded=False):
        
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
            
            
            # Create Interactive Plot for Predicted Prices
            fig2 = go.Figure()
            
            # Add Historical Data
            fig2.add_trace(go.Scatter(
                x=stock_data.index, 
                y=stock_data['Close'], 
                mode='lines',
                name='Actual Data',
                line=dict(color='blue'),
                hovertemplate="Date: %{x}<br>Actual Price: %{y:.2f} USD"
            ))
        # Once done, continue with the rest of the app
        st.success("✅ Prediction complete!")
        
        # Add Forecast Data
        fig2.add_trace(go.Scatter(
            x=forecast_df.index, 
            y=forecast_df['Forecast'], 
            mode='lines+markers',
            name='Predicted Data',
            line=dict(dash='dot', color='red'),
            marker=dict(size=6),
            hovertemplate="Date: %{x}<br>Predicted Price: %{y:.2f} USD"
        ))
        
        # Update layout to match Matplotlib-style structure
        fig2.update_layout(
            title=f"{selected_ticker} Predicted Closing Price",
            xaxis_title="Time",
            yaxis_title="Stock Price",
            hovermode="x unified",
            template="plotly_white"
        )
    
    # Show in Streamlit
        st.plotly_chart(fig2, use_container_width=True)
        # # Plot predictions
        # st.subheader("Predicted Price")
        # fig2, ax2 = plt.subplots()
        # ax2.plot(stock_data.index, stock_data['Close'], label='Actual Data', color='blue')
        # ax2.plot(forecast_df.index, forecast_df['Forecast'], label='Predicted Data', linestyle='--', marker='o', color='red')
        # ax2.set_xlabel("Time")
        # ax2.set_ylabel("Price")
        # ax2.set_title(f"{selected_ticker} Predicted Closing Price")
        # ax2.legend()
        # st.pyplot(fig2)
        
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
    
elif selected_model == "Ticknor (2013)":
    st.markdown("## Ticknor's Approach 📈")

    # ✅ Sidebar explanation for Ticknor
    st.sidebar.write("""
- **Ticknor's model** utilizes a **Bayesian-regularized artificial neural network** to predict stock prices.
- The model consists of a **three-layer feedforward neural network** trained with **Bayesian regularization**, reducing overfitting and improving generalization.
- **9 input features** are used, including **daily stock price data (low, high, open)** and **six technical indicators**:
  - Exponential Moving Averages (5-day & 10-day)
  - Relative Strength Index (RSI)
  - Williams %R
  - Stochastic %K and %D
- The network is optimized using the **Levenberg–Marquardt algorithm**, which approximates the Hessian matrix for efficient training.
- The model predicts **next-day closing prices** and evaluates performance using **Mean Absolute Percentage Error (MAPE)**.
- Unlike conventional ANN models, Bayesian regularization **assigns probabilities to network weights**, preventing excessive complexity and improving robustness.

📄 **Read their full paper:** [Ticknor (2013) - A Bayesian Regularized ANN for Stock Prediction](https://www.sciencedirect.com/science/article/abs/pii/S0957417413002509)
""")


    # ✅ Predict button for Ticknor's model
    if st.button("Predict with Ticknor"):
        with st.status("⏳ Computing... This can take a few seconds", expanded=False):
            predicted_price, next_trading_day = predict_with_ticknor(ticker_symbol)

        # ✅ Display Prediction
        st.success("✅ Ticknor Prediction complete!")
        
        # ✅ Check if the next available trading day is different from the next day
        today = datetime.today()
        next_day = today + timedelta(days=1)
        next_day_str = next_day.strftime('%A, %B %d, %Y')  # Format as "Day, Month DD, YYYY"

        if next_trading_day != next_day_str:
            st.warning(f"⚠️ The next available trading day is **{next_trading_day}**. Markets may be closed due to weekends or holidays.")
            st.markdown(f"### 📊 The stock price at close on **{next_trading_day}** is predicted to be **${predicted_price:.2f}**")
            st.caption("🚨 Please proceed with caution as market closure affects training data availability.")
        else:
            st.markdown(f"### 📊 The predicted price at close for end of day **({next_trading_day})** is **${predicted_price:.2f} USD**")

        # ✅ Show MEP if needed
        st.sidebar.write("###  Model Mean Error Percentage (MEP)")
        st.sidebar.write("MEP will vary basd on the chosen stock. An MEP 0f 2.8 was obtained for AAPL during testing")

    
    # Add Two Vertical Spaces
    st.markdown("<br>", unsafe_allow_html=True)
# Clear button
if st.button("Clear"):
    st.rerun()
    #Add Two Vertical Spaces
st.markdown("<br><br>", unsafe_allow_html=True)

    
    
    
st.markdown("""
## ☕ Want More?  
If you like this app and want to support further improvements, consider buying me a coffee!  
""", unsafe_allow_html=True)




# Buy Me a Coffee Button (Replace with Your Link)
st.markdown("""
<a href="https://www.buymeacoffee.com/andyj" target="_blank">
    <img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=&slug=YOURUSERNAME&button_colour=FFDD00&font_colour=000000&font_family=Arial&outline_colour=000000&coffee_colour=ffffff" width="200">
</a>
""", unsafe_allow_html=True)
    
    
    
    
# # Clear button
# if st.button("Clear"):
#     st.rerun()
#     #Add Two Vertical Spaces
# st.markdown("<br><br>", unsafe_allow_html=True)

    
