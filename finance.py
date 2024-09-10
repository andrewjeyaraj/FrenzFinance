# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 15:18:06 2024

@author: andre
"""

# Import required libraries
import streamlit as st
import numpy as np
import pandas as pd

# Function to calculate compound interest
def compound_interest(principal, rate, years):
    return principal * (1 + rate) ** years

# Function to calculate depreciation factor
def depreciation_factor(rate, years):
    return (1 - rate) ** years

# Dashboard title
st.title(" CAD & INR Investment & Depreciation Calculator")

# Input: Initial Investment
investment_inr = st.number_input("Initial Investment (INR)", value=2000)
initial_inr_to_cad = st.slider("Initial CAD to INR Exchange Rate", 50.0, 100.0, 60.0)
investment_cad = investment_inr / initial_inr_to_cad
# Show the fixed depreciation slider
depreciation_rate = st.slider("INR Depreciation Rate (per year)", 0.00, 0.10, 0.03)
# Input: USD to CAD exchange rate ranges
usd_to_cad = st.slider("Initial USD to CAD Exchange Rate", 0.65, 1.0, 0.73)

# Input: Return Rate (in INR and CAD)
return_rate_inr = st.slider("Return Rate in INR (per year)", 0.00, 0.20, 0.15)
mer_inr = st.slider("Management Expense Ratio for INR investment", 0.00, 0.05, 0.007)
return_rate_inr_adjusted = return_rate_inr - mer_inr

return_rate_cad = st.slider("Return Rate in CAD (per year)", 0.00, 0.10, 0.076)
mer_cad = st.slider("Management Expense Ratio for CAD investment", 0.00, 0.05, 0.007)
return_rate_cad_adjusted = return_rate_cad - mer_cad

# Input: Investment Duration (Years)
years = st.slider("Investment Duration (Years)", 1, 30, 10)

depreciation_mode = st.radio(
    "Choose Depreciation Type",
    ('Fixed Depreciation', 'Variable Depreciation')
)

if depreciation_mode == 'Fixed Depreciation':
    

    # Calculate final values in INR and CAD
    final_inr_value = compound_interest(investment_inr, return_rate_inr_adjusted, years)
    final_cad_value = compound_interest(investment_cad, return_rate_cad_adjusted, years)

    # Calculate depreciation factor and future exchange rates
    future_inr_to_cad = initial_inr_to_cad / depreciation_factor(depreciation_rate, years)

    # Convert final CAD value back to INR using future exchange rate
    final_inr_after_cad_conversion = final_cad_value * future_inr_to_cad
    final_cad_after_inr_conversion = final_inr_value * (1/future_inr_to_cad)
    
    # Custom CSS for the box styling
    box_css = """
    <style>
        .box {
            background-color: #4682B4;
            color: white;
            font-size: 18px;
            padding: 40px;
            border-radius: 10px;
            text-align: center;
            height: 150px;
        }
    </style>
    """

    # Inject the custom CSS into the Streamlit app
    st.markdown(box_css, unsafe_allow_html=True)

    # Create a 2x2 layout using Streamlit columns
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    # First column (top-left): Investment in Canada
    with col1:
        st.markdown(f"""
        <div class="box">
            <p>This is your "Principal+ Return" if you invest your money in Canada</p>
            <p><b>{final_cad_value} CAD</b></p>
        </div>
        """, unsafe_allow_html=True)

    # Second column (top-right): Investment in India
    with col2:
        st.markdown(f"""
        <div class="box">
            <p>This is your "Principal+Return" if you invest your money in India</p>
            <p><b>{final_inr_value} INR</b></p>
        </div>
        """, unsafe_allow_html=True)

    # Third column (bottom-left): Investment in India, converted to CAD
    with col3:
        st.markdown(f"""
        <div class="box">
            <p>This is your "Principal +Return" if you invest your money in India and convert to CAD</p>
            <p><b>{final_inr_after_cad_conversion} CAD</b></p>
        </div>
        """, unsafe_allow_html=True)

    # Fourth column (bottom-right): Investment in Canada, converted to INR
    with col4:
        st.markdown(f"""
        <div class="box">
            <p>This is your 'Principal + Return" if you invest your money in Canada and convert to INR</p>
            <p><b>{final_cad_after_inr_conversion} INR</b></p>
        </div>
        """, unsafe_allow_html=True)

    # Conditional logic for minimum return calculations based on your logic
    if final_inr_after_cad_conversion < final_cad_value:
        min_return_inr = (final_cad_value / final_inr_value) ** (1 / 10) - 1  # Example 10-year calculation
        st.write(f"Minimum Annual Return in INR required to match CAD: {min_return_inr * 100:.2f}%")
    else:


        min_return_cad = (final_inr_value / final_cad_value) ** (1 / 10) - 1  # Example 10-year calculation
        st.write(f"Minimum Annual Return in CAD required to match INR: {min_return_cad * 100:.2f}%")
        
elif depreciation_mode == 'Variable Depreciation':
    # Show input boxes for low, medium, and high depreciation
    low_depreciation = st.number_input("Low Depreciation Rate (per year)", min_value=0.00, max_value=0.10, value=0.02)
    medium_depreciation = st.number_input("Medium Depreciation Rate (per year)", min_value=0.00, max_value=0.10, value=0.03)
    high_depreciation = st.number_input("High Depreciation Rate (per year)", min_value=0.00, max_value=0.10, value=0.05)
    
    
    #Calculate preliminaries 
    # Calculate final values in INR and CAD
    final_inr_value = compound_interest(investment_inr, return_rate_inr_adjusted, years)
    final_cad_value = compound_interest(investment_cad, return_rate_cad_adjusted, years)
    
    
    
    
    future_inr_to_cad_low = initial_inr_to_cad / depreciation_factor(low_depreciation, years)
    future_inr_to_cad_med = initial_inr_to_cad / depreciation_factor(medium_depreciation, years)
    future_inr_to_cad_high = initial_inr_to_cad / depreciation_factor(high_depreciation, years)
    
    #Final values for each depreciation rate low
    final_inr_after_cad_conversion_low = final_cad_value * future_inr_to_cad_low
    final_cad_after_inr_conversion_low = final_inr_value * (1/future_inr_to_cad_low)
    
    #Final values for each depreciation rate medium
    
    final_inr_after_cad_conversion_med = final_cad_value * future_inr_to_cad_med
    final_cad_after_inr_conversion_med = final_inr_value * (1/future_inr_to_cad_med)
    
    #Final values for each depreciation rate high
    final_inr_after_cad_conversion_high = final_cad_value * future_inr_to_cad_high
    final_cad_after_inr_conversion_high = final_inr_value * (1/future_inr_to_cad_high)
    
    
    # Display results in a table
    
    df = pd.DataFrame({
        "Depreciation Level": ["Low", "Medium", "High"],
        "Returns when you invest in INR and convert back to CAD": [final_inr_after_cad_conversion_low, final_inr_after_cad_conversion_med, final_inr_after_cad_conversion_high],
        "Returns when you invest in CAD and then convert to INR": [final_cad_after_inr_conversion_low, final_cad_after_inr_conversion_med, final_cad_after_inr_conversion_high]
    })
    st.table(df)
    
    







# # Display results
# st.write(f"Final Value in INR after {years} years: {final_inr_value:.2f} INR")
# st.write(f"Final Value in CAD after {years} years: {final_cad_value:.2f} CAD")
# st.write(f"Future Exchange Rate (CAD to INR) after depreciation: {future_inr_to_cad:.2f}")
# st.write(f"Final INR value if CAD is invested in Canada and converted from CAD to INR after {years} years: {final_inr_after_cad_conversion:.2f} INR")

# # Profit or Loss
# profit_inr = final_inr_value - investment_inr
# profit_cad = final_cad_value * future_inr_to_cad - investment_inr
# profit_cad_inr_convert = final_cad_value * future_inr_to_cad - investment_inr

# st.write(f"Profit or Loss in INR: {profit_inr:.2f} INR")
# st.write(f"Profit or Loss in CAD: {profit_cad:.2f} CAD")
# st.write(f"Profit or Loss in INR if CAD invested in Canada is converted to INR accounting for INR depreciation: {profit_cad_inr_convert:.2f} INR")

# Comparing final returns after conversion
# if final_inr_after_cad_conversion < final_cad_value:
#     # If INR investment converted back to CAD gives a lower profit, calculate minimum INR return required
#     min_return_inr = (final_cad_value / investment_inr) ** (1 / years) - 1
#     st.write(f"Minimum Annual Return in INR required to match CAD: {min_return_inr * 100:.2f}%")

# if final_cad_after_inr_conversion < final_inr_value:
#     # If CAD investment converted back to INR gives a lower profit, calculate minimum CAD return required
#     min_return_cad = (final_inr_value / investment_cad) ** (1 / years) - 1
#     st.write(f"Minimum Annual Return in CAD required to match INR: {min_return_cad * 100:.2f}%")
    
    


# # Minimum return required to match CAD investment in INR
# min_return_inr = (final_cad_value / investment_inr) ** (1 / years) - 1
# st.write(f"Minimum Annual Return in INR required to match CAD: {min_return_inr * 100:.2f}%")

# # Minimum return required to match INR investment in CAD
# min_return_cad = (final_inr_value / investment_cad) ** (1 / years) - 1
# st.write(f"Minimum Annual Return in CAD required to match INR: {min_return_cad * 100:.2f}%")
