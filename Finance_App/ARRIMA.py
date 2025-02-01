# -*- coding: utf-8 -*-
"""
Created on Fri Jan 31 12:01:48 2025

@author: andre
"""

import yfinance as yf
import matplotlib.pyplot as plt
import statsmodels.api as sm
from patsy import dmatrices
from datetime import datetime  # ✅ Correct way to use strptime()
from pandas.plotting import autocorrelation_plot
from statsmodels.tsa.arima.model import ARIMA
import pandas as pd
from pandas import DataFrame
from sklearn.metrics import mean_squared_error
from math import sqrt


selected_ticker="MSFT"
dat=yf.Ticker(selected_ticker)
#print(dat.analyst_price_targets)
#csv=yf.download(['MSFT', 'AAPL', 'GOOG'], period='3mo')
stock_data = yf.Ticker(selected_ticker).history(period="5y")
#print(stock_data)
stock_data.reset_index(inplace=True)
#print(stock_data.head())  # Now "Date" is a column
stock_data.index=stock_data['Date'].values
#stock_data.drop(columns=["Date"], inplace=True)  # Remove the duplicate column if needed


# Ensure 'Date' is in string format before parsing
stock_data['Date'] = stock_data['Date'].dt.strftime('%Y-%m')

# Define parser function
def parser(x):
    return datetime.strptime(x, '%Y-%m')

# Apply parser function and merge with 'Close' column
usable_data_final = stock_data.copy()
usable_data_final['Parsed_Date'] = stock_data['Date'].apply(parser)


# Keep only the parsed date and Close price
usable_data_final = usable_data_final[['Parsed_Date', 'Close']]

# Print final DataFrame
#print(usable_data_final)
    
    


# Set 'Parsed_Date' as the index for proper time-series plotting
usable_data_final.set_index('Parsed_Date', inplace=True)
print(usable_data_final)
# Plot the data
#usable_data_final.plot()

# Show the plot
#plt.show()

# #autocorrelation_plot(usable_data_final)..
# Aggregate duplicate dates by taking the mean (or another function)
usable_data_final = usable_data_final.resample('ME').mean()

# Ensure frequency is set
usable_data_final = usable_data_final.asfreq('ME')

X = usable_data_final.values
size = int(len(X) * 0.66)
train, test = X[0:size], X[size:len(X)]
history = [x for x in train]
predictions = list()


# walk-forward validation
for t in range(len(test)):
	model = ARIMA(history, order=(15,1,0))
	model_fit = model.fit()
	output = model_fit.forecast()
	yhat = output[0]
	predictions.append(yhat)
	obs = test[t]
	history.append(obs)
	print('predicted=%f, expected=%f' % (yhat, obs))

        
# evaluate forecasts
rmse = sqrt(mean_squared_error(test, predictions))
print('Test RMSE: %.3f' % rmse)
# Plot forecasts against actual outcomes
plt.figure(figsize=(10,5))  # Set figure size
plt.plot(test, label="Actual", linestyle="-", marker="o", color="blue")
plt.plot(predictions, label="Predicted", linestyle="--", marker="x", color="red")

# Add labels and title
plt.xlabel("Time", fontsize=12)
plt.ylabel("Stock Price", fontsize=12)
plt.title("Autoregressive Integrated Moving-Average Model Forecast vs Actual", fontsize=14)

# Add legend
plt.legend()

# Show the plot
plt.show()


n_predict=1
# Forecast the next 'n_predict' months
forecast = model_fit.forecast(steps=n_predict)
print(forecast)

# Create future date index
last_date = usable_data_final.index[-1]  # Get the last available date
future_dates = [last_date + pd.DateOffset(months=i) for i in range(1, n_predict + 1)]

# Convert to DataFrame
forecast_df = pd.DataFrame({'Date': future_dates, 'Forecast': forecast})
forecast_df.set_index('Date', inplace=True)

# Plot historical data and forecast
plt.figure(figsize=(10, 5))
plt.plot(usable_data_final['Close'], label="Actual Data", color='blue')
plt.plot(forecast_df, label="Forecast", linestyle="--", marker="o", color='red')

# Labels and legend
plt.xlabel("Time")
plt.ylabel("Microsoft Stock Price (USD)")
plt.title(f"Autoregressive Integrated Moving-Average Model Forecast for {n_predict} Months Ahead")
plt.legend()

# Show plot
plt.show()




# fit model
# model = ARIMA(usable_data_final, order=(15,1,0))
# model_fit = model.fit()

# # summary of fit model
# print(model_fit.summary())

# # line plot of residuals
# residuals = DataFrame(model_fit.resid)
# residuals.plot()
# plt.show()
# # density plot of residuals
# residuals.plot(kind='kde')
# plt.show()
# # summary stats of residuals
# print(residuals.describe())

