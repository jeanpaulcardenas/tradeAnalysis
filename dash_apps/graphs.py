from dash import dash, dcc, html, callback
from dash.dependencies import Input, Output
from data_classes.statistics_m import Metrics, metrics_between_dates
from dash_graph_f.graph_high_low import CouldWinTrades, WonVsBestDiff, MetricsRadar
from dash_graph_f.income import ScatterGraph, BarGraph, SunBurst, TimeOpenIncome
from config import _inc_dropdown_options, _BARS_DROPDOWN_OPTIONS, _METRICS_DROPDOWN_OPTIONS, \
    _TIME_TYPE_OPTIONS, _TIME_TYPE_DICT, get_logger
import pandas as pd
import datetime as dt
import pickle

with open('./data/cached_random_dict.pkl', 'rb') as f:
    rand_data = pickle.load(f)

random_metric = Metrics(pd.DataFrame(rand_data), pd.DataFrame(), 'USD')
rand_df = random_metric.df
app = dash.Dash()

logger = get_logger(__name__)


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


def app_layout(start_date, end_date) -> dash.html.Div:
    """Create layout of graph's page. Start and end date will be the initial values of date picker range."""
    layout = html.Div([
        html.H1('Profit', style={'text-align': 'center'}),
        html.Br(),
        dcc.Dropdown(
            options=_METRICS_DROPDOWN_OPTIONS,
            value=False,
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
            options=_inc_dropdown_options(),
            value=0,
            id='income dropdown'
        ),
        dcc.Graph(id='income graph'),
        html.Br(),

        dcc.Dropdown(
            options=_BARS_DROPDOWN_OPTIONS,
            value='YE',
            id='bars dropdown'
        ),
        dcc.Graph(id='bars graph'),
        html.Br(),
        dcc.Graph(id='sunburst'),
        html.Br(),
        dcc.Dropdown(
            options=_TIME_TYPE_OPTIONS,
            value='days',
            id='time style'

        ),
        dcc.Graph(id='time graph'),
        html.Br(),
        dcc.Graph(id='box: could have won'),
        html.Br(),
        dcc.Graph(id='box: real vs max'),
        html.Br(),
        dcc.Dropdown(
            options=_inc_dropdown_options(all_values=True),
            value='symbol',
            id='radar option'
        ),
        dcc.Graph(id='kpi radar'),
        html.Br(),
        html.Br()
    ])

    return layout


start, end = set_start_end_dates(rand_df)
app.layout = app_layout(start_date=start, end_date=end)


@callback(
    [Output('income graph', 'figure'),
     Output('bars graph', 'figure'),
     Output('sunburst', 'figure'),
     Output('time graph', 'figure'),
     Output('box: could have won', 'figure'),
     Output('box: real vs max', 'figure'),
     Output('kpi radar', 'figure')],
    [Input('metric dropdown', 'value'),
     Input('date range', 'start_date'),
     Input('date range', 'end_date'),
     Input('income dropdown', 'value'),
     Input('bars dropdown', 'value'),
     Input('time style', 'value'),
     Input('radar option', 'value')])
def update_charts(measure, start_date, end_date, subplots_choice, bars_choice, time_style, radar_choice):

    metrics_obj = metrics_between_dates(random_metric, start_date=start_date, end_date=end_date)

    income_graph = ScatterGraph(metrics_obj=metrics_obj,
                                subplots_choice=subplots_choice,
                                pips=measure,
                                title='Cumulative Income').get_figure()

    bars_graph = BarGraph(metrics_obj=metrics_obj,
                          subplots_choice=subplots_choice,
                          period=bars_choice).get_figure()

    sunburst = SunBurst(metrics_obj).get_figure()

    time_graph = TimeOpenIncome(metrics_obj=metrics_obj,
                                subplots_choice=subplots_choice,
                                pips=measure,
                                title='Time open vs Income',
                                **_TIME_TYPE_DICT[time_style]).get_figure()

    could_win = CouldWinTrades(metrics_obj,
                               subplots_choice=subplots_choice,
                               title='Trades you could have won').get_figure()
    real_vs_max = WonVsBestDiff(metrics_obj,
                                subplots_choice,
                                title='Real Profit vs Max Possible Profit').get_figure()

    radar = MetricsRadar(metrics_obj, radar_choice, title='KPI Radar').get_figure()

    return [income_graph, bars_graph, sunburst, time_graph, could_win, real_vs_max, radar]
