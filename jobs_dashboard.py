# -*- coding: utf-8 -*-
"""jobs_dashboard.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1XY8CYe31X5scHkLU_l3nNjYXbMe6D9jC
"""

pip install dash
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
        html.Label("Select Data Slice:"),
        dcc.Dropdown(
            id="data-type",
            options=[
                {"label": "Actual Employment", "value": "actual"},
                {"label": "Percentage Change (Month over Month)", "value": "MoM"},
                {"label": "Percentage Change (Year over Year)", "value": "YoY"}
            ],
            value="actual",
        ),

        dcc.Graph(id="participation-graph"),
    ])

    # Callback to update the graph
    @app.callback(
        Output("participation-graph", "figure"),
        Input("data-type", "value"),
    )
    def update_graph(data_type):
        df_copy = df.copy()

        if data_type == "actual":
            fig = px.line(df_copy, x="date", y="actual", title="Civilan Labor Force",
                          labels={"date": "Date", "actual": "Actual Employment"},
                          template="plotly_dark")
            fig.update_layout(yaxis=dict(title="Actual Employment"))
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
