from dash import dash, dcc, html, callback
from dash.dependencies import Input, Output
from application.config import get_logger
from application.statistics import Metrics
from application.dash_graph_f.income import IncomeGraph, BarGraph
from application.random_df_generator import RandDataGen
from application.constants import INCOME_DROPDOWN_OPTIONS, BARS_DROPDOWN_OPTIONS, METRICS_DROPDOWN_OPTIONS
from application.helpers import metrics_between_dates
import pandas as pd
import datetime as dt
import pickle

app = dash.Dash()
logger = get_logger(__name__)
with open('../cached_random_df.pkl', 'rb') as f:
    rand_data = pickle.load(f)
    random_metric = Metrics(rand_data.df, pd.DataFrame(), rand_data.currency)
    rand_df = random_metric.df


def set_start_end_dates(base_df: pd.DataFrame) -> tuple[dt.datetime, dt.datetime]:
    """Returns tuple (min date, max date) of a metrics.df"""
    try:
        start_date = min(base_df.close_time)
        end_date = max(base_df.close_time)
        logger.info(f"{__name__} dates from date range picker: {start_date} to {end_date}")

    except Exception:
        logger.error(f"Error getting dataframes from min and max dates of {base_df['close_time'].head()}, "
                     f"using 100 days back from today")
        now = dt.datetime.now()
        start_date = now - dt.timedelta(days=100)
        end_date = now
    return start_date, end_date


def app_layout(start_date, end_date):
    """Create layout of graph's page. Start and end date will be the initial values of date picker range."""
    layout = html.Div([
        html.H1('Profit', style={'text-align': 'center'}),
        html.Br(),
        dcc.Dropdown(
            options=METRICS_DROPDOWN_OPTIONS,
            value='profit',
            id='metric dropdown'
        ),
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
            options=INCOME_DROPDOWN_OPTIONS,
            value=0,
            id='income dropdown'
        ),
        dcc.Graph(id='income graph'),
        html.Br(),

        dcc.Dropdown(
            options=BARS_DROPDOWN_OPTIONS,
            value=0,
            id='bars dropdown'
        ),
        dcc.Graph(id='bars graph')
    ])

    return layout


@callback(
    [Output('income graph', 'figure'),
     Output('bars graph', 'figure')],
    [Input('metric dropdown', 'value'),
     Input('date range', 'start_date'),
     Input('date range', 'end_date'),
     Input('income dropdown', 'value'),
     Input('bars dropdown', 'value')])
def update_charts(metric, start_date, end_date, inc_choice, bars_choice):
    metrics_obj = metrics_between_dates(random_metric, start_date=start_date, end_date=end_date)
    income_graph = IncomeGraph(metrics_object=metrics_obj, choice=inc_choice).get_figure(metric)
    bars_graph = BarGraph(metrics_obj=metrics_obj, choice=inc_choice, period=bars_choice).add_bar_plot()
    return [income_graph, bars_graph]


if __name__ == '__main__':
    start, end = set_start_end_dates(rand_df)
    app.layout = app_layout(start_date=start, end_date=end)
    app.run(debug=True)
