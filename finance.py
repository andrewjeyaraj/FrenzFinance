# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 15:18:06 2024

@author: andre
"""

# Import required libraries
import streamlit as st
import numpy as np

# Function to calculate compound interest
def compound_interest(principal, rate, years):
    return principal * (1 + rate) ** years

# Function to calculate depreciation factor
def depreciation_factor(rate, years):
    return (1 - rate) ** years

# Dashboard title
st.title("Investment & Depreciation Calculator")

# Input: Initial Investment
investment_inr = st.number_input("Initial Investment (INR)", value=2000)
initial_inr_to_cad = st.slider("Initial INR to CAD Exchange Rate", 50.0, 100.0, 60.0)
investment_cad = investment_inr / initial_inr_to_cad

# Input: INR Depreciation Rate (0% to 10%)
depreciation_rate = st.slider("INR Depreciation Rate (per year)", 0.00, 0.10, 0.03)

# Input: USD to CAD exchange rate ranges
usd_to_cad = st.slider("Initial USD to CAD Exchange Rate", 0.65, 0.85, 0.73)

# Input: Return Rate (in INR and CAD)
return_rate_inr = st.slider("Return Rate in INR (per year)", 0.00, 0.20, 0.15)
mer_inr = st.slider("Management Expense Ratio for INR investment", 0.00, 0.05, 0.007)
return_rate_inr_adjusted = return_rate_inr - mer_inr

return_rate_cad = st.slider("Return Rate in CAD (per year)", 0.00, 0.10, 0.076)
mer_cad = st.slider("Management Expense Ratio for CAD investment", 0.00, 0.05, 0.007)
return_rate_cad_adjusted = return_rate_cad - mer_cad

# Input: Investment Duration (Years)
years = st.slider("Investment Duration (Years)", 1, 30, 10)

# Calculate final values in INR and CAD
final_inr_value = compound_interest(investment_inr, return_rate_inr_adjusted, years)
final_cad_value = compound_interest(investment_cad, return_rate_cad_adjusted, years)

# Calculate depreciation factor and future exchange rates
future_inr_to_cad = initial_inr_to_cad / depreciation_factor(depreciation_rate, years)

# Convert final CAD value back to INR using future exchange rate
final_inr_after_cad_conversion = final_cad_value * future_inr_to_cad

# Display results
st.write(f"Final Value in INR after {years} years: {final_inr_value:.2f} INR")
st.write(f"Final Value in CAD after {years} years: {final_cad_value:.2f} CAD")
st.write(f"Future Exchange Rate (INR to CAD) after depreciation: {future_inr_to_cad:.2f}")
st.write(f"Final INR value if converted from CAD after {years} years: {final_inr_after_cad_conversion:.2f} INR")

# Profit or Loss
profit_inr = final_inr_value - investment_inr
profit_cad = final_cad_value * future_inr_to_cad - investment_inr

st.write(f"Profit or Loss in INR: {profit_inr:.2f} INR")
st.write(f"Profit or Loss if converted from CAD: {profit_cad:.2f} INR")

# Minimum return required to match CAD investment in INR
min_return_inr = (final_cad_value / investment_inr) ** (1 / years) - 1
st.write(f"Minimum Annual Return in INR required to match CAD: {min_return_inr * 100:.2f}%")

# Minimum return required to match INR investment in CAD
min_return_cad = (final_inr_value / investment_cad) ** (1 / years) - 1
st.write(f"Minimum Annual Return in CAD required to match INR: {min_return_cad * 100:.2f}%")
