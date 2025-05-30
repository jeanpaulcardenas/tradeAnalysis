from application.statistics import Metrics
from application.constants import *
from application.config import get_logger
import pandas as pd
import plotly.graph_objects as go
import datetime as dt


logger = get_logger(__name__)


class IncomeGraph:

    def __init__(self, start: dt.datetime, end: dt.datetime, metrics_object: Metrics, choice: str):
        self.metrics_ob = metrics_object
        self.df = self.df_between_dates(start_date=start, end_date=end)
        logger.info(f'{__name__} income graph df: {self.df}')
        self.choice = choice

    def df_between_dates(self, start_date: dt.datetime, end_date: dt.datetime) -> pd.DataFrame:
        df = self.metrics_ob.df
        print(f'metrics.df: \n {df}')
        df_ranged = df[(df['open_time'] >= start_date) & (df['close_time'] <= end_date)].reset_index(drop=True)
        return df_ranged

    def layout(self) -> dict:
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
                        ticksuffix=self.metrics_ob.currency_symbol,
                        tickformat='d',
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
        return choices[choice]

    def get_name(self, df):
        if self.choice:
            name = df[self.choice][0]
        else:
            name = "All trades"
        return name

    def get_figure(self):
        fig = go.Figure(layout=self.layout())
        objs = self.create_dataframes(choice=self.choice)
        for i, df in enumerate(objs):
            name = self.get_name(df=df)
            x = [df.open_time[0]] + df.close_time.to_list()
            y = [0] + df.profit.cumsum().to_list()
            fig.add_trace(go.Scatter(
                name=name,
                showlegend=True,
                legendgroup=name,
                x=x,
                y=y,
                mode='lines+markers+text',
                textposition='top right',
                texttemplate='%{y}',
                line=dict(
                    width=2,
                    shape="hv",
                    color=list(COLORS.values())[i]
                )))

        return fig
