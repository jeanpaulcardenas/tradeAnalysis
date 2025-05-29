from dash import dash, dcc, html, callback
from dash.dependencies import Input, Output
from application.statistics import Metrics
from application.dash_graph_f.income import IncomeGraph
from application.random_df_generator import RandDataGen
import pandas as pd
import datetime as dt


my_simulated_df = RandDataGen(10, 'USD').df
print(my_simulated_df.to_string())
app = dash.Dash()
metrics_obj = Metrics(my_simulated_df, pd.DataFrame(), 'USD')  # currency choices should be restricted or checked

try:
    start_date = min(metrics_obj.df.close_time)
    end_date = max(metrics_obj.df.close_time)

except:
    now = dt.datetime.now()
    start_date = now - dt.timedelta(days=10)
    end_date = now

app.layout = html.Div([
    html.H1("Profit", style={"text-align": "center"}),
    html.Br(),
    dcc.DatePickerRange(
        min_date_allowed=start_date,
        start_date_placeholder_text=start_date,
        start_date=start_date,
        end_date=end_date,
        end_date_placeholder_text=end_date,
        initial_visible_month=end_date,
        id="date range"

    ),
    dcc.Dropdown(
        options=["All", "Buy vs Sell", "Pairs", "Day of week"],
        value="All",
        id="income dropdown"
    ),
    dcc.Graph(id="income graph"),
    html.Br()])


@callback(
    [Output("income graph", "figure")],
    [Input("date range", "start_date"),
     Input("date range", "end_date"),
     Input("income dropdown", "value")])
def update_charts(start, end, choice):
    income_graph = IncomeGraph(metrics_obj, choice=choice).get_figure()
    return [income_graph]


if __name__ == '__main__':
    app.run(debug=True)
