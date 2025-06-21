from data_classes.statistics_m import Metrics
from config import get_logger, _METRICS_DF_KEYS, _PLOTLY_GRAPH_TEMPLATE, _PLOTLY_GRAPH_COLORS, _COLORS
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

logger = get_logger(__name__)


class ScatterGraph:
    _PLOTLY_GRAPH_TEMPLATE = 'plotly_dark'

    def __init__(self, metrics_obj: Metrics, subplots_choice: str, pips: bool, title: str):
        self._measure = 'pips' if pips else 'profit'
        self._metrics_obj = metrics_obj
        self._df = self.metrics_obj.df
        self._subplots_choice = subplots_choice
        self._fig = go.Figure()
        self._currency_symbol = self.metrics_obj.currency_symbol if self.measure == 'profit' else ''
        self.fig.update_layout(self._layout(title))

    def get_figure(self) -> go.Figure:
        """Returns a scatter plot figure. Plots are dependent on self.subplots_choice"""
        objs = self._create_dataframes(subplots_choice=self.subplots_choice)
        for i, df in enumerate(objs):
            name = self._get_legend_name(df=df)
            x = df.close_time  # adding open_time[0] value at index 0
            y = df[self.measure].cumsum()  # adding a zero value at index 0
            self._add_scatter_plot(
                name=name, x=x, y=y, idx=i, mode='lines+markers',
                hover_template=self.hover_template, custom_data=df[['order', self.measure]])
            self._add_final_markers(idx=i, name=name)  # add text marker at the end of each line plot
        return self.fig

    def _layout(self, title, **kwargs) -> dict:
        """Creates layout  dict for a plot. This one is specifically created for a plotly scatter plot"""
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
                        ticksuffix=' ' + self.metrics_obj.currency_symbol if self.measure == 'profit' else None,
                        tickformat=',d',
                        ticklabelposition='outside right',
                        separatethousands=True,
                    ),
                    **kwargs)

    def _create_dataframes(self, subplots_choice: str) -> list[pd.DataFrame]:
        """returns dataframes for the given subplots_choice. e.g. if subplots_choice == pairs, returns a dataframe
        for each unique pair containing only data with that pair symbol."""
        try:
            if subplots_choice == 0:
                # if there is no subplots_choice return self.df, this will lead a global income figure
                return [self.df]
            elif subplots_choice in _METRICS_DF_KEYS:
                # Create a list a dataframes, one for each unique self.df[subplots_choice],
                # e.g. self.df[subplots_choice].unique = ['EURUSD', 'USDJPY']
                return [self.df[self.df[subplots_choice] == item].reset_index(drop=True)
                        for item in self.df[subplots_choice].unique()]
        except KeyError:
            logger.error(f"Error. subplots_choice for IncomeGraph {subplots_choice} not valid")
            return [pd.DataFrame()]

    def _get_legend_name(self, df: pd.DataFrame) -> str:
        """Gets the corresponding legend name by user's subplots_choice (self.subplots_choice)."""
        if self.subplots_choice:
            try:
                name = df[self.subplots_choice][0]
            except KeyError:
                name = None
                logger.warning(f"couldn't find df[{self.subplots_choice}][0], no name given to legend")
        else:
            name = "All trades"
        return name

    def _add_final_markers(self, idx: int, name) -> None:
        """Adds final marker's text, introducing a new x y value trace to figure. **kwargs are pass to fig.add_trace"""
        idx = idx * 2
        last_date = self.fig.data[idx].x[-1]
        last_cuml = self.fig.data[idx].y[-1]
        self.fig.add_trace(go.Scatter(
            x=[last_date],
            y=[last_cuml],
            mode='text',
            textposition='middle right',
            texttemplate='   %{y}',
            showlegend=False,
            legendgroup=name,
        ))

    def _add_scatter_plot(self, name: str, x: list[float], y: list[float],
                          idx: int, mode, custom_data: list[list[float]] = None, hover_template: str = None) -> None:
        """Adds scatter plot to fig."""
        self.fig.add_trace(go.Scatter(
            name=name,
            showlegend=True,
            legendgroup=name,
            x=x,
            y=y,
            mode=mode,
            customdata=custom_data,
            hovertemplate=hover_template,
            textposition='top right',
            texttemplate='%{y}',
            line=dict(
                width=2,
                shape='linear',
                color=_PLOTLY_GRAPH_COLORS[idx]
            )))

    @property
    def hover_template(self) -> str:
        return '<b>Cumulative profit:</b> %{y}<br>' \
               '<b>Order:</b> %{customdata[0]}<br>' \
               '<b>Close date:</b> %{x}<br>' \
               f'<b>Profit:</b> %{{customdata[1]}} {self.currency_symbol}'

    @property
    def metrics_obj(self) -> Metrics:
        """Returns metrics object."""
        return self._metrics_obj

    @property
    def fig(self) -> go.Figure:
        """Returns figure."""
        return self._fig

    @property
    def measure(self) -> str:
        """Returns measure type, it will be 'pips' if pips argument is true, else 'profit'"""
        return self._measure

    @property
    def df(self) -> pd.DataFrame:
        """Returns dataframe used in the plotting."""
        return self._df

    @property
    def subplots_choice(self) -> str:
        """Returns subplots_choice selection."""
        return self._subplots_choice

    @property
    def currency_symbol(self) -> str | None:
        """Returns currency symbol for y values in the plot figure. If measure is PIPS then None is returned"""
        return self._currency_symbol


class TimeOpenIncome(ScatterGraph):
    _HOVER_TEMPLATE = '<b>Profit:</b> %{y}<br>' \
                      '<b>Time open:</b> %{x}<br>' \
                      '<b>Order:</b> %{customdata[0]}<br>' \
                      '<b>Date:</b> %{customdata[1]}'

    def __init__(self, metrics_obj, subplots_choice, pips, title, ceiling: int, denominator: int, period: str):
        super(TimeOpenIncome, self).__init__(metrics_obj, subplots_choice, pips, title)
        self.ceiling = ceiling
        self.denominator = denominator
        self.period = period

    def get_figure(self) -> go.Figure:
        """Returns a scatter plot figure. Plots are dependent on self.subplots_choice"""
        objs = self._create_dataframes(subplots_choice=self.subplots_choice)
        for i, df in enumerate(objs):
            name = self._get_legend_name(df=df)
            df = self._filter_by_style(df)
            x, y = self._get_x_values(df), self._get_y_values(df)
            self._add_scatter_plot(name=name, x=x, y=y, idx=i,
                                   mode='markers', hover_template=TimeOpenIncome._HOVER_TEMPLATE,
                                   custom_data=df[['order', 'close_time']])
        self._update_axes()

        return self.fig

    def _get_x_values(self, df) -> list[float]:
        """Gets total seconds of 'delta_time' column of df and divides it by 'self.denominator'."""
        logger.info(self.denominator)
        series = df['delta_time'].dt.total_seconds() / self.denominator
        series = series.apply(lambda x: round(x, 1))
        return series.to_list()

    def _get_y_values(self, df: pd.DataFrame) -> list[float]:
        """Gets the y value as a list, depends on 'measure'."""
        return df[self.measure].to_list()

    def _filter_by_style(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter df depending on 'time_style' ceiling"""
        return df[df['delta_time'].dt.total_seconds() < self.ceiling]

    def _update_axes(self) -> None:
        self.fig.update_xaxes(
            ticksuffix=f' {self.period}',
            title='Time',
        )


class BarGraph:
    def __init__(self, metrics_obj: Metrics, subplots_choice: str, period: str):
        self.metrics = metrics_obj
        self.subplots_choice = subplots_choice
        self.df = self.metrics.df
        self.period = period

    def _bar_fig_layout(self) -> dict:
        """Returns layout dictionary for a plotly bar figure"""
        return dict(
            height=700,
            barmode='relative',
            template=_PLOTLY_GRAPH_TEMPLATE,
            title=dict(
                text=f'Income by period', x=0.5,
                font=dict(
                    color='#2C74B3',
                    family='sans-serif',
                    size=34
                )
            ), xaxis=dict(
                gridcolor='rgba(44, 116, 179, 0.2)',
                griddash='solid',
                zerolinecolor='rgba(120, 120, 120, 0.4)',

            ), yaxis=dict(
                gridcolor='rgba(44, 116, 179, 0.2)',
                griddash='solid',
                zerolinecolor='rgba(44, 116, 179, 0.5)',
                separatethousands=True,
                ticksuffix=self.metrics.currency_symbol
            ))

    def _crate_dataframe(self) -> pd.DataFrame:
        """Create grouped dataframe with columns df[column].unique() and their values are profit and the
        frequency is grouped by 'self.period' close_date."""
        dataframe = self.metrics.income_by_period(column=self.subplots_choice, frequency=self.period)

        return dataframe

    def get_figure(self) -> go.Figure:
        """Creates the bar plot with init arguments."""
        fig = go.Figure(layout=self._bar_fig_layout())
        dataframe = self._crate_dataframe()
        for idx, item in enumerate(dataframe.columns):
            fig.add_bar(
                name=item,
                x=dataframe.index,
                y=dataframe[item],
                textposition='inside',
                textangle=0,
                marker=dict(
                    color=_PLOTLY_GRAPH_COLORS[idx]
                ),
                texttemplate='%{y:,.0f} ' + self.metrics.currency_symbol,
                insidetextfont=dict(
                    color=_COLORS['white']
                )

            )

        return fig


class SunBurst:
    _PATH = ['won_lost', 'order_type', 'day_of_week', 'symbol']

    def __init__(self, metric_obj: Metrics):
        self.metric = metric_obj
        self.df = self.metric.df.copy()
        self.add_won_lost_column()

    @staticmethod
    def update_layout() -> dict:
        return {
            'width': 700,
            'height': 700,
            'margin': dict(autoexpand=True),
            'showlegend': True,
            'plot_bgcolor': "#0A2647",
            'legend': dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.70
            ), 'title': dict(
                text="Earnings sunburst", x=0.5,
                font=dict(
                    color="#2C74B3",
                    family="sans-serif",
                    size=34,
                ))}

    def _get_color_map(self) -> list[str]:
        """Returns the correct order of ['blue', 'red'] so that won trades are always blue. To be used in get_figure."""
        if self.metric.net_income < 0:
            return [_COLORS['red'], _COLORS['blue']]
        else:
            return [_COLORS['blue'], _COLORS['red']]

    def add_won_lost_column(self) -> None:
        self.df['won_lost'] = ['Won' if won else 'Lost' for won in self.df.won_trade]

    def get_figure(self) -> go.Figure:
        """Returns a sunburst figure"""
        color_map = self._get_color_map()
        fig = px.sunburst(data_frame=self.df,
                          path=SunBurst._PATH,
                          values=abs(self.df.profit),
                          color_discrete_sequence=color_map,
                          )
        fig.update_traces(
            hovertemplate=f'<b>%{{label}}</b><br>Profit: %{{value:,d}} {self.metric.currency_symbol}'
        )
        layout = SunBurst.update_layout()
        fig.update_layout(layout)
        return fig
