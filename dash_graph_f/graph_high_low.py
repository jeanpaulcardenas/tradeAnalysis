from config import get_logger, _COLORS, _PLOTLY_GRAPH_COLORS
from data_classes.statistics_m import Metrics
import plotly.graph_objects as go
import pandas as pd

logger = get_logger(__name__)
_PLOTLY_GRAPH_TEMPLATE = 'plotly_dark'


def normalize_data(data: pd.Series) -> list[float]:
    """Normalize a list of float values to range (0, 1) where the min value is 0 and largest is 1"""
    sample_max = max(data)
    sample_min = min(data)
    denominator = sample_max - sample_min
    if len(data) < 2:
        return data.to_list()

    elif not list(filter(lambda x: x < 0, data)):
        # if data is positive: this way avoids turning positive values to zero, which is a better interpretation
        # of metrics, considering this function will be used to plot radars. e.g. in a list of PFs with minimum value of
        # 2.8, the above formula would turn it to 0, which would point to the base of the radar indicating 'bad',
        # that would be a bad interpretation
        return list(map(lambda x: (x / sample_max), data))

    elif denominator:
        if not list(filter(lambda x: x > 0, data)):
            # if there is no positive value in data, then normalize from 0 to 0.5
            normalized = list(map(lambda x: (x - sample_min) / (2 * denominator), data))
            return normalized
        else:
            # normalize the list this way if it contains negative numbers.
            # The most negative number is the '0' val reference
            normalized = list(map(lambda x: (x - sample_min) / denominator, data))
            return normalized
    else:
        # if denominator == 0 then return list of zeros
        return [0 for _ in data]


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

    def get_figure(self, box_points: str = 'all') -> go.Figure:
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
        return f'<b>Difference: </b> %{{y}} <br>' \
               f'<b>Profit: </b> %{{customdata[0]:,d}} {self.metrics.currency_symbol} <br>' \
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


class MetricsRadar(BoxGraph):
    _THETA = ['Profit factor', 'Efficiency', 'Times traded', 'Average Profit']
    _THETA_ACCESS = ['profit_factor', 'efficiency', 'n_of_trades', 'expectancy']
    _HOVER_TEMPLATE = '<b>%{theta}</b>: %{customdata[0]:.2f}<extra></extra>'

    def __init__(self, metrics: Metrics, subplots_choice: str, title: str):
        super(MetricsRadar, self).__init__(metrics, subplots_choice, title)
        self._unique_df_ids = self.metrics.df[self.subplots_choice].unique()
        self._delete_radar_axis_ticks()

    def get_figure(self) -> go.Figure | None:
        """Returns a radar (scatter polar graph) with normalized profit factors, efficiencies,
         amount of trades and expectancies"""
        if len(self.unique_df_ids) < 2:
            # don't return a figure if there's only one metric object to plot. This radar uses normalized values
            # we cant normalize KPI if there's only one float value for each KPI
            return None
        normed_kpi_df = self._normalized_kpi_df()
        real_kpi_df = self._create_kpi_df()
        # name : KPI metric identifier e.g. 'monday'. values: KPI values in _THETA_ACCESS for the given metrics object
        for idx, ((name, values), (name_2, real_vals)) in enumerate(zip(normed_kpi_df.items(), real_kpi_df.items())):
            r = values.to_list()
            r += [r[0]]  # we append the first r value to close the line graph of the radar, it's a style choice
            r_real = real_vals.to_list()
            r_real += [r_real[0]],
            theta = MetricsRadar._THETA
            self.fig.add_trace(go.Scatterpolar(
                theta=theta + [theta[0]],
                r=r,
                customdata=[[v] for v in r_real],
                name=name,
                marker=dict(
                    color=_PLOTLY_GRAPH_COLORS[idx]
                ),
                hovertemplate=MetricsRadar._HOVER_TEMPLATE
            ))
        return self.fig

    @property
    def unique_df_ids(self) -> list[str]:
        """Return string names for each subset"""
        return self._unique_df_ids

    def _get_subplots_metrics(self) -> dict:
        """gets metrics for all unique subplot dataframes"""
        if self.subplots_choice:
            return {key: Metrics(df, pd.DataFrame(), self.metrics.currency_symbol)
                    for key, df in zip(self.unique_df_ids, self.dfs)}
        else:
            return {'all': self.metrics}

    def _create_kpi_df(self) -> pd.DataFrame:
        """creates a dataframe with columns as the unique subset identifiers (e.g. ['USDCAD', 'EURGBP',...]) and
        index ['profit_factor', 'efficiency', 'n_of_trades', 'expectancy']."""
        metrics = self._get_subplots_metrics()
        kpis = {name: [getattr(metric, name) for metric in metrics.values()] for name in MetricsRadar._THETA_ACCESS}
        kpi_df = pd.DataFrame(data=kpis.values(), index=list(kpis.keys()), columns=self.unique_df_ids)
        logger.info(f'kpis:\n{kpi_df.head()}')
        return kpi_df

    def _normalized_kpi_df(self) -> pd.DataFrame:
        """returns normalized dataframe with columns as the unique subset identifiers (e.g. ['USDCAD', 'EURGBP',...])
        and index ['profit_factor', 'efficiency', 'n_of_trades', 'expectancy']"""
        kpi_df = self._create_kpi_df()
        for idx in kpi_df.index:
            kpi_df.loc[idx] = normalize_data(kpi_df.loc[idx])
        logger.info(f"normalized kpis:\n{kpi_df.head().to_string()}")
        return kpi_df

    def _delete_radar_axis_ticks(self):
        """Hides radar axis tick labels."""
        self.fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    showticklabels=False,
                )
            )
        )
