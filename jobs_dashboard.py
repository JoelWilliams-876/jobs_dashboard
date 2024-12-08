# -*- coding: utf-8 -*-
"""jobs_dashboard.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1XY8CYe31X5scHkLU_l3nNjYXbMe6D9jC
"""

import requests
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
from datetime import datetime
import pytz
from bs4 import BeautifulSoup

# Fetch Total Private Jobs Data
def fetch_total_private_jobs():
    url = "https://www.bls.gov/news.release/jolts.a.htm"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    table = soup.find("table", {"class": "datavalue"})
    if table:
        rows = table.find_all("tr")
        data = []
        for row in rows:
            cols = row.find_all("td")
            if len(cols) > 0:
                date = cols[0].text.strip()
                value = cols[1].text.strip()
                data.append({"date": date, "value": float(value.replace(",", ""))})

        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"], format="%b %Y")
        return df
    else:
        print("Table not found on the page.")
        return pd.DataFrame()

# Initialize Dash App
app = Dash(__name__)

# Fetch initial data
total_private_data = fetch_total_private_jobs()

if 'date' not in total_private_data.columns:
    print("Error: 'date' column not found in DataFrame.")
    exit()

app.layout = html.Div([
    html.H1("BLS Jobs Dashboard"),
    html.Label("Select Comparison Type:"),
    dcc.Dropdown(
        id="comparison-type",
        options=[
            {"label": "Month Over Month", "value": "MoM"},
            {"label": "Quarter Over Quarter", "value": "QoQ"},
            {"label": "Year Over Year", "value": "YoY"},
        ],
        value="MoM",
    ),
    html.Label("Select Date Range:"),
    dcc.DatePickerRange(
        id="date-range",
        start_date=total_private_data["date"].min().strftime("%Y-%m-%d"),
        end_date=total_private_data["date"].max().strftime("%Y-%m-%d"),
        display_format="YYYY-MM-DD",
    ),
    dcc.Graph(id="jobs-graph"),
])

@app.callback(
    Output("jobs-graph", "figure"),
    Input("comparison-type", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
)
def update_graph(comparison_type, start_date, end_date):
    private_data = total_private_data

    # Filter data by date range
    try:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        private_data = private_data[(private_data["date"] >= start_date) & (private_data["date"] <= end_date)]
    except Exception as e:
        print("Date range filtering error:", e)
        return px.line(title="Error: Invalid date range.")

    # Ensure data is not empty
    if private_data.empty:
        return px.line(title="No data available for the selected range.")

    # Calculate percentage change
    try:
        if comparison_type == "MoM":
            private_data["change"] = private_data["value"].pct_change(periods=1) * 100
            title = "Month Over Month % Change"
        elif comparison_type == "QoQ":
            private_data["change"] = private_data["value"].pct_change(periods=3) * 100
            title = "Quarter Over Quarter % Change"
        else:
            private_data["change"] = private_data["value"].pct_change(periods=12) * 100
            title = "Year Over Year % Change"
    except Exception as e:
        print("Percentage change calculation error:", e)
        return px.line(title="Error: Unable to calculate changes.")

    # Drop NaN values
    private_data = private_data.dropna(subset=["change"])

    # Plot the figure
    try:
        fig = px.line(
            private_data, x="date", y="change",
            title=title,
            labels={"date": "Date", "change": "% Change in Total Private Jobs"},
            template="plotly_white"
        )

        fig.update_layout(
            yaxis=dict(title="Total Private Jobs % Change"),
        )

        return fig
    except Exception as e:
        print("Graph plotting error:", e)
        return px.line(title="Error: Unable to render graph.")

if __name__ == "__main__":
    app.run_server(debug=True)

!pip install dash
import requests
import pandas as pd
import plotly.express as px
from bs4 import BeautifulSoup
import dash
from dash import dcc, html, Input, Output

# Map month codes (M01, M02, etc.) to actual month names
month_mapping = {
    "M01": "January", "M02": "February", "M03": "March", "M04": "April", "M05": "May", "M06": "June",
    "M07": "July", "M08": "August", "M09": "September", "M10": "October", "M11": "November", "M12": "December"
}

# Function to fetch and parse the data from BLS table
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

# Initialize Dash app
app = dash.Dash(__name__)

df = fetch_bls_table_data()

if not df.empty:
    df["actual"] = df["value"]
    df, title = calculate_percentage_change(df, "MoM")

    app.layout = html.Div([
        html.H1("BLS Employment Data"),

        # Dropdown for selecting data type
        html.Label("Select Data Type:"),
        dcc.Dropdown(
            id="data-type",
            options=[
                {"label": "Actual Unemployment Rate", "value": "actual"},
                {"label": "Percentage Change (MoM)", "value": "MoM"},
                {"label": "Percentage Change (YoY)", "value": "YoY"}
            ],
            value="actual",
        ),

        dcc.Graph(id="unemployment-graph"),
    ])

    # Callback to update the graph
    @app.callback(
        Output("unemployment-graph", "figure"),
        Input("data-type", "value"),
    )
    def update_graph(data_type):
        df_copy = df.copy()

        if data_type == "actual":
            fig = px.line(df_copy, x="date", y="actual", title="Actual Unemployment Rate",
                          labels={"date": "Date", "actual": "Unemployment Rate (%)"},
                          template="plotly_dark")
            fig.update_layout(yaxis=dict(title="Unemployment Rate (%)"))
        else:
            df_copy, title = calculate_percentage_change(df_copy, data_type)
            fig = px.line(df_copy, x="date", y="change", title=title,
                          labels={"date": "Date", "change": "% Change"},
                          template="plotly_dark")
            fig.update_layout(yaxis=dict(title="% Change"))

        return fig

    if __name__ == "__main__":
        app.run_server(debug=True)

else:
    print("No data available for the graph.")