from application.statistics import Metrics
from application.constants import *
from application.config import get_logger
import pandas as pd
import plotly.graph_objects as go

logger = get_logger(__name__)


class IncomeGraph:
    def __init__(self, metrics_object: Metrics, choice: str):
        self.metrics_ob = metrics_object
        self.df = self.metrics_ob.df
        self.choice = choice

    def get_figure(self, column):
        """Returns a scatter plot figure. Plots are dependant on self.choice"""
        fig = go.Figure(layout=self._layout(column))
        objs = self._create_dataframes(choice=self.choice)
        for i, df in enumerate(objs):
            name = self._get_legend_name(df=df)
            x = [df.open_time[0]] + df.close_time.to_list()
            y = [0] + df[column].cumsum().to_list()
            IncomeGraph._add_scatter_plot(fig, name, x, y, i)
        return fig

    def _layout(self, metric) -> dict:
        """Creates layout  dict for a plot. This one is specifically created for a plotly scatter plot"""
        return dict(template="plotly_dark",
                    showlegend=True,
                    title=dict(
                        text='accumulative income', x=0.5,
                        font=dict(
                            color="#2C74B3",
                            family="sans-serif",
                            size=34
                        )
                    ),

                    yaxis=dict(
                        griddash="solid",
                        zerolinecolor="rgba(120, 120, 120, 0.5)",
                        ticksuffix=self.metrics_ob.currency_symbol if metric == 'profit' else None,
                        tickformat=',d',
                        ticklabelposition='outside right',
                        separatethousands=True,
                    ))

    def _create_dataframes(self, choice: str) -> list[pd.DataFrame]:
        try:
            if choice == 0:
                return [self.df]
            elif choice in METRICS_DF_KEYS:
                return [self.df[self.df[choice] == item].reset_index(drop=True) for item in self.df[choice].unique()]
        except KeyError:
            logger.error(f"Error. choice for IncomeGraph {choice} not valid")
            return [pd.DataFrame()]

    def _get_legend_name(self, df):
        """Gets the corresponding legend name by user's choice (self.choice)."""
        if self.choice:
            name = df[self.choice][0]
        else:
            name = "All trades"
        return name

    @staticmethod
    def _add_scatter_plot(fig: go.Figure, name: str, x: list[float], y: list[float], idx: int):
        fig.add_trace(go.Scatter(
            name=name,
            showlegend=True,
            legendgroup=name,
            x=x,
            y=y,
            mode='lines+markers',
            textposition='top right',
            texttemplate='%{y}',
            line=dict(
                width=2,
                shape="hv",
                color=list(COLORS.values())[idx]
            )))


class BarGraph:
    def __init__(self, metrics_obj: Metrics, choice: str, period: str):
        self.metrics = metrics_obj
        self.choice = choice
        self.df = self.metrics.df
        self.period = period

    def _bar_fig_layout(self) -> dict:
        """Returns layout dictionary for a plotly bar figure"""
        return dict(
            height=700,
            barmode='relative',
            template="plotly_dark",
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

    def _crate_dataframe(self):
        dataframe = self.metrics.income_by_period(column=self.choice, frequency=self.period)

        return dataframe

    def add_bar_plot(self):
        fig = go.Figure(layout=self._bar_fig_layout())
        dataframe = self._crate_dataframe()
        for item in dataframe.columns:
            print(item)
            fig.add_bar(
                name=item,
                x=dataframe.index,
                y=dataframe[item]
            )

        return fig
