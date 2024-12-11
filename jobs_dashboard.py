# -*- coding: utf-8 -*-
"""jobs_dashboard.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1XEP90tc9EJpu2g2VVFzjSgpGy_seR9k4
"""

import requests
import pandas as pd
import plotly.express as px
from bs4 import BeautifulSoup
import streamlit as st

# function to fetch and parse the data from BLS table and converting data to a dataframe.
def fetch_bls_table_data():
    url = "https://data.bls.gov/dataViewer/view/timeseries/LNS11000000"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find("table", {"id": "seriesDataTable1"})

    if table:
        rows = table.find_all("tr")
        data = []

        for row in rows:
            cols = row.find_all("td")
            if len(cols) > 0:
                year = cols[0].text.strip()
                period = cols[1].text.strip()
                value = float(cols[3].text.strip().replace(",", "").split("\r")[0])

                try:
                    month_code = period[1:]
                    concatenated_date = f"{month_code}-{year}"
                    data.append({
                        "date": concatenated_date,
                        "value": float(value)
                    })
                except ValueError:
                    print(f"Skipping row with invalid date format: {period} {year}")
                    continue

        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"], format="%m-%Y")
        return df
    else:
        print("Table not found.")
        return pd.DataFrame()

# Calculate percentage change for MoM and YoY
def calculate_percentage_change(df, comparison_type):
    if comparison_type == "MoM":
        df["change"] = df["value"].pct_change() * 100
        title = "Month Over Month % Change"
    elif comparison_type == "YoY":
        df["change"] = df["value"].pct_change(periods=12) * 100
        title = "Year Over Year % Change"

    return df, title

# Main Streamlit app
st.title("BLS Employment Data")

df = fetch_bls_table_data()

if not df.empty:
    df["actual"] = df["value"]

# this is the slicer. its a mighty fine slicer if i do say so myself.
    data_type = st.selectbox(
        "Select Data Slice:",
        ["Actual Employment", "Percentage Change (Month over Month)", "Percentage Change (Year over Year)"]
    )

    if data_type == "Actual Employment":
        fig = px.line(df, x="date", y="actual", title="Civilan Labor Force",
                      labels={"date": "Date", "actual": "Actual Employment"},
                      template="plotly_dark")
    else:
        comparison_type = "MoM" if "Month" in data_type else "YoY"
        df, title = calculate_percentage_change(df, comparison_type)
        fig = px.line(df, x="date", y="change", title=title,
                      labels={"date": "Date", "change": "% Change"},
                      template="plotly_dark")  # if you ask me, all dashboards should be black. it is cleaner, easier on the eyes and, most importantly, it looks frickin' cool.

    st.plotly_chart(fig)
else:
    st.error("No data available for the graph.")