from config import get_logger, _COLORS, _PLOTLY_GRAPH_COLORS
from data_classes.statistics_m import Metrics
import plotly.graph_objects as go
import pandas as pd

logger = get_logger(__name__)

_PLOTLY_GRAPH_TEMPLATE = 'plotly_dark'


class BoxGraph:
    def __init__(self, metrics_obj: Metrics, subplots_choice: str, title: str):
        self._metrics = metrics_obj
        self._subplots_choice = subplots_choice
        self._fig = go.Figure(layout=self._layout(title))

    @property
    def metrics(self):
        """Returns the metric object (Metric class)."""
        return self._metrics

    @property
    def subplots_choice(self) -> str:
        """Subplot choice from the dash dropbox selection"""
        return self._subplots_choice

    @property
    def fig(self) -> go.Figure:
        """Return the 'go.Figure' object."""
        return self._fig

    @property
    def dfs(self) -> list[pd.DataFrame]:
        return self._get_dfs()

    def _layout(self, title: str) -> dict:
        """returns app layout, title is the graph title that will be displayed."""
        return dict(template=_PLOTLY_GRAPH_TEMPLATE,
                    showlegend=True,
                    title=dict(
                        text=title,
                        x=0.5,
                        font=dict(
                            color="#2C74B3",
                            family="sans-serif",
                            size=34
                        )
                    ),
                    yaxis=dict(
                        griddash='solid',
                        zerolinecolor=_COLORS['translucent_grey'],
                        ticksuffix=' ' + self.metrics.currency_symbol,
                        tickformat=',d',
                        ticklabelposition='outside right',
                        separatethousands=True,
                    ))

    def _get_legend_name(self, df: pd.DataFrame) -> str:
        """Gets the corresponding legend name by user's subplot_choice (self.subplot_choice)."""
        if self.subplots_choice:
            try:
                name = df[self.subplots_choice][0]  # Name of the first
            except KeyError:
                name = None
                logger.warning(f"couldn't find df[{self.subplots_choice}][0], no name given to legend")
        else:
            name = "All trades"
        return name

    def _get_dfs(self) -> list[pd.DataFrame]:
        """Get dataframes for each subplot (determined by self.subplots_choice). gets a dataframe for each unique
        value in 'self.metrics.df[self.subplots_choice]'."""
        if not self.subplots_choice:
            return [self.metrics.df]
        else:
            values = self.metrics.df[self.subplots_choice].unique()
            df = self.metrics.df
            return [df[df[self.subplots_choice] == value].reset_index(drop=True) for value in values]


class CouldWinTrades(BoxGraph):
    def __init__(self, metrics_obj: Metrics, subplots_choice: str, title: str):
        super(CouldWinTrades, self).__init__(metrics_obj, subplots_choice, title)

    def get_figure(self, box_points: str = 'all') -> go.Figure:
        """Returns box figure for 'max_possible_gain' for losing trades (profit < 0). box_points determines
        the way individual values are shown in the graph, this must be one of
        '['all', 'outliers', 'suspectedoutliers', False]'"""
        for idx, df in enumerate(self.dfs):
            y = self._get_y_series(df)
            self.fig.add_trace(go.Box(y=y,
                                      name=self._get_legend_name(df),
                                      marker_color=_PLOTLY_GRAPH_COLORS[idx],
                                      boxpoints=box_points))
        return self.fig

    @staticmethod
    def _get_y_series(df: pd.DataFrame) -> pd.DataFrame:
        """Returns a pandas series with values 'max_possible_gain' for losing trades."""
        return df['max_possible_gain'][~df['won_trade']]


class WonVsBestDiff(BoxGraph):
    def __init__(self, metrics: Metrics, subplots_choice: str, title: str):
        super(WonVsBestDiff, self).__init__(metrics, subplots_choice, title)

    def get_figure(self, box_points: str = 'all', custom_data_1: str = 'profit', ) -> go.Figure:
        """Returns box figure for 'max_possible_gain' for losing trades (profit < 0). box_points determines
        the way individual values are shown in the graph, this must be one of
        '['all', 'outliers', 'suspectedoutliers', False]'"""
        for idx, df in enumerate(self.dfs):
            custom_data = WonVsBestDiff._get_custom_data(df)
            y = self._get_y_series(df)
            self.fig.add_trace(go.Box(y=y,
                                      name=self._get_legend_name(df),
                                      marker_color=_PLOTLY_GRAPH_COLORS[idx],
                                      boxpoints=box_points,
                                      customdata=custom_data,
                                      hovertemplate=self.hover_template))
        return self.fig

    @property
    def hover_template(self):
        return f'<b>Difference: </b> %{{y}} <br>'\
               f'<b>Profit: </b> %{{customdata[0]:,d}} {self.metrics.currency_symbol} <br>'\
               f'<b>Max reached</b>: %{{customdata[1]:,d}} {self.metrics.currency_symbol}<br>' \
               f'<b>Order: </b> %{{customdata[2]:d}}'

    @staticmethod
    def _won_trades_df(df: pd.DataFrame) -> pd.DataFrame:
        return df[df['won_trade']]

    @staticmethod
    def _get_custom_data(df: pd.DataFrame):
        return WonVsBestDiff._won_trades_df(df)[['profit', 'max_possible_gain', 'order']].values

    @staticmethod
    def _get_y_series(df: pd.DataFrame) -> pd.Series:
        wins_df = WonVsBestDiff._won_trades_df(df)
        max_vs_real_diff = wins_df['max_possible_gain'] - wins_df['profit']
        return max_vs_real_diff
#
# class CountProfitHistogram:
#     def __init__(self, metrics_obj: Metrics):
#         self.metrics = metrics_obj
#
#     def get_figure(self):
#         won_trades_data = self.metrics.df['profit'][self.metrics.df['won_trade'] == True]
#         df = self.metrics.df[self.metrics.df['won_trade'] == True]
#         perfect_trades_data = self.metrics.df['max_possible_gain'][self.metrics.df['won_trade'] == True]
#         bin_size = perfect_trades_data.mean() / 10
#         labels = ['won trades', 'perfect possible result']
#         print(self.metrics.df.to_string())
#         fig = px.histogram(df, x='profit', color='symbol')
#         return fig
#
#
# class WonVsPerfectHistogram:
#     def __init__(self, metrics_obj: Metrics):
#         self.metrics = metrics_obj
#
#     def get_figure(self):
#         return None
