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

    def layout(self, metric) -> dict:
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

    def create_dataframes(self, choice: str) -> list[pd.DataFrame]:
        choices = {
            0: [self.df],
            'order_type': [self.df[self.df.order_type == order_type].reset_index(drop=True)
                           for order_type in order_types],
            'symbol': [self.df[self.df.symbol == pair_symbol].reset_index(drop=True)
                       for pair_symbol in self.df['symbol'].unique()],
            'day_of_week': [self.df[self.df.day_of_week == day].reset_index(drop=True)
                            for day in self.df['day_of_week'].unique()],
        }
        try:
            return choices[choice]
        except KeyError:
            logger.error(f"Error. choice for IncomeGraph {choice} not valid")
            return [pd.DataFrame()]

    def get_legend_name(self, df):
        if self.choice:
            name = df[self.choice][0]
        else:
            name = "All trades"
        return name

    def get_figure(self, column):
        fig = go.Figure(layout=self.layout(column))
        objs = self.create_dataframes(choice=self.choice)
        for i, df in enumerate(objs):
            name = self.get_legend_name(df=df)
            x = [df.open_time[0]] + df.close_time.to_list()
            y = [0] + df[column].cumsum().to_list()
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
                    color=list(COLORS.values())[i]
                )))

        return fig


class BarGraph:
    def __init__(self, metrics_obj: Metrics, choice: str):
        self.metrics = metrics_obj
        self.choice = choice
