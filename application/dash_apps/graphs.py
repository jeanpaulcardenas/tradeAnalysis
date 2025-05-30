from dash import dash, dcc, html, callback
from dash.dependencies import Input, Output
from application.config import get_logger
from application.statistics import Metrics
from application.dash_graph_f.income import IncomeGraph
from application.random_df_generator import RandDataGen
import pandas as pd
import datetime as dt


app = dash.Dash()
logger = get_logger(__name__)
df = RandDataGen(80, 'USD').df
try:
    start_date = min(df.close_time)
    end_date = max(df.close_time)
    logger.info(f"{__name__} dates from date range picker: {start_date} to {end_date}")

except Exception as e:
    logger.error(f"Error getting dataframes from min and max dates of {df['close_time']}, "
                 f"using 100 days back from today")
    now = dt.datetime.now()
    start_date = now - dt.timedelta(days=100)
    end_date = now

metrics_obj = Metrics(df, pd.DataFrame(), 'USD')  # currency choices should be restricted or checked
app.layout = html.Div([
    html.H1('Profit', style={'text-align': 'center'}),
    html.Br(),
    dcc.DatePickerRange(
        min_date_allowed=start_date,
        start_date_placeholder_text=start_date,
        start_date=start_date,
        end_date=end_date,
        end_date_placeholder_text=end_date,
        initial_visible_month=end_date,
        id='date range'

    ),
    dcc.Dropdown(
        options=['All', 'Buy vs Sell', 'Pairs', 'Day of week'],
        value='All',
        id='income dropdown'
    ),
    dcc.Graph(id='income graph'),
    html.Br()])


@callback(
    [Output('income graph', 'figure')],
    [Input('date range', 'start_date'),
     Input('date range', 'end_date'),
     Input('income dropdown', 'value')])
def update_charts(start, end, choice):
    income_graph = IncomeGraph(metrics_object=metrics_obj, start=start, end=end, choice=choice).get_figure()
    return [income_graph]


if __name__ == '__main__':
    app.run(debug=True)
