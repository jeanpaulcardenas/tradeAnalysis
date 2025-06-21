from dash import html, dash_table
from dash.dash_table.Format import Format, Symbol, Group, Scheme
from config import get_logger, _COLORS
import pandas as pd
import numpy as np
import dash
from data_classes.statistics_m import Metrics


class TradesDataTable:
    _PRICE_FORMAT = Format(precision=5, scheme=Scheme.fixed, group=Group.yes, groups=3)

    def __init__(self, metrics_obj: Metrics):
        self.metrics = metrics_obj
        self.df = metrics_obj.df

    @property
    def columns(self):
        price_format = TradesDataTable._PRICE_FORMAT
        money_formats = Format(
            symbol=Symbol.yes, symbol_prefix=f'{self.metrics.currency_symbol}', group=Group.yes)
        return [
            {'name': 'Order ID', 'id': 'order', 'type': 'numeric'},
            {'name': 'symbol', 'id': 'symbol', 'type': 'text'},
            {'name': 'Volume', 'id': 'volume', 'type': 'numeric'},
            {'name': 'Type', 'id': 'order_type', 'type': 'text'},
            {'name': 'Open Time', 'id': 'open_time', 'type': 'datetime'},
            {'name': 'Open Price', 'id': 'open_price', 'type': 'numeric', 'format': price_format},
            {'name': 'Close Time', 'id': 'close_time', 'type': 'datetime'},
            {'name': 'Close Price', 'id': 'close_price', 'type': 'numeric', 'format': price_format},
            {'name': 'Highest Price', 'id': 'high', 'type': 'numeric', 'format': price_format},
            {'name': 'Lowest Price', 'id': 'low', 'type': 'numeric', 'format': price_format},
            {'name': 'PIPs', 'id': 'pips', 'type': 'numeric', 'format': Format(
                precision=0, scheme=Scheme.fixed, group=Group.yes)},
            {'name': 'Profit', 'id': 'profit', 'type': 'numeric', 'format': money_formats},
            {'name': 'Cumulative Profit', 'id': 'cum_profit', 'type': 'numeric', 'format': money_formats}
        ]

    def get_dash_table_component(self, table_id: str, page_size: int = 20) -> dash.dash_table:
        return dash_table.DataTable(
            id=table_id,
            data=self.df.to_dict("records"),
            columns=self.columns,
            page_size=page_size,
            style_data_conditional=
            [self._negative_style_conditional(_COLORS[color], quantile=quantile) for color, quantile in
             zip(['mona_lisa', 'red_accent', 'red'], [1, 0.25, 0.1])],
            style_header={
                'backgroundColor': 'rgb(210, 210, 210)',
                'color': 'black',
                'fontWeight': 'bold'
            },
        )

    def _negative_style_conditional(self, bg_color: str, font_color: str = 'white', quantile: float = 1):

        return {
            'if': {
                'filter_query': f'{{profit}} < 0 && {{profit}} < {self.df["profit"].quantile(quantile)}',
                'column_id': 'profit'
            },
            'backgroundColor': bg_color,
            'color': font_color,

        }
