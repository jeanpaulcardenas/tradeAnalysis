from dash import dcc, html, callback
from dash.dependencies import Input, Output
from application.statistics import Metrics
from constants import *
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import dash
import datetime as dt


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
            'Pair': [self.df[self.df.symbol == pair_symbol] for pair_symbol in self.df['symbol'].unique()],
            'Day of week': [self.df[self.df.day_of_week == day] for day in self.df['day_of_week'].unique()],
        }
        return choices[choice]

    def get_figure(self):
        layout = self.layout()
        fig = go.Figure()
        fig.update_layout(layout)
        objs = self.df[self.choice].copy()

        for i, iter_df in enumerate(objs):
            if self.choice != "Todos":
                column = COLUMN_USED[self.choice]
                name = iter_df.df[column][0]
            else:
                name = "All trades"
            fig.add_trace(go.Scatter(
                name=name,
                showlegend=True,
                legendgroup=name,
                x=iter_df.df.ff,
                y=np.cumsum(iter_df.df.ing),
                mode="lines+markers",
                line=dict(
                    width=2,
                    shape="hv",
                    color=COLORS[i]
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

# def income_graph(start, end, choice, b_time_period, style):
#     d = GaFiltered(df[(df["ff"] >= start) & (df["ff"] <= end)].copy(), "eur")
#
#     unique_active_dow = pd.unique(d.df.dow)
#     act_objects_list = [GaFiltered(d.df[d.df['act'] == act].copy(), 'eur') for act in d.most_traded['act']]
#     cv_objects_list = [GaFiltered(d.df[d.df['tip'] == tip].copy(), 'eur') for tip in d.tip]
#     days_obj_list = [GaFiltered(d.df[d.df["dow"] == day].copy(), "eur") for day in unique_active_dow]
#     for obj in days_obj_list:
#         print(f'object: {obj.df}')
#     income_by_month = d.get_income_by_period(b_time_period)
#     print(income_by_month.to_string())
#     dataframes = {
#         "Todos": [d],
#         "Compra Vs. Venta": cv_objects_list,
#         "Por pares": act_objects_list,
#         "Día de la semana": days_obj_list,
#     }
