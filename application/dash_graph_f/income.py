from application.statistics import Metrics
from application.constants import *
import pandas as pd
import plotly.graph_objects as go


class IncomeGraph:

    def __init__(self, metrics_object: Metrics, choice: str):
        self.metrics_ob = metrics_object
        self.df: pd.DataFrame = metrics_object.df
        self.choice = choice

    def layout(self) -> dict:
        return dict(template="plotly_dark",
                    showlegend=True,
                    title=dict(
                        text="Ingreso acumulado", x=0.5,
                        font=dict(
                            color="#2C74B3",
                            family="sans-serif",
                            size=34
                        )
                    ),

                    yaxis=dict(
                        griddash="solid",
                        zerolinecolor="rgba(120, 120, 120, 0.5)",
                        ticksuffix=f" {self.metrics_ob.currency}",
                        separatethousands=True,
                    ))

    def create_dataframes(self, choice: str) -> str:
        choices = {
            'All': [self.df],
            'Buy vs Sell': [self.df[self.df.order_type == order_type] for order_type in order_types],
            'Pairs': [self.df[self.df.symbol == pair_symbol] for pair_symbol in self.df['symbol'].unique()],
            'Day of week': [self.df[self.df.day_of_week == day] for day in self.df['day_of_week'].unique()],
        }
        return choices[choice]

    def get_name(self, df):
        if self.choice != "All":
            column = COLUMN_USED[self.choice]
            name = df[column][0]
        else:
            name = "All trades"
        return name

    def get_figure(self):
        fig = go.Figure(layout=self.layout())
        objs = self.create_dataframes(choice=self.choice)
        for i, df in enumerate(objs):
            df = df.copy()
            df.reset_index(inplace=True)
            name = self.get_name(df=df)
            fig.add_trace(go.Scatter(
                name=name,
                showlegend=True,
                legendgroup=name,
                x=[df.open_time[0]] + df.close_time.to_list(),
                y=[0] + df.profit.cumsum().to_list(),
                mode="lines+markers",
                line=dict(
                    width=2,
                    shape="hv",
                    color=list(COLORS.values())[i]
                )))
            last_data = fig.data[2 * i]

            fig.add_scatter(
                x=[last_data.x[-1]],
                y=[last_data.y[-1]],
                mode="text",
                text="  {:,} {}".format(fig.data[2 * i].y[-1], self.metrics_ob.currency),
                textfont=dict(color="white"),
                textposition="middle right",
                legendgroup=last_data["name"],
                showlegend=False,

            )
        return fig
