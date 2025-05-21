from application.mt4data import Trade, TradeData
import pandas as pd
import numpy as np
import pickle
from application.config import get_logger
with open("cached_trade_data.pkl", "rb") as f:
    trade_data = pickle.load(f)


logger = get_logger(__name__)

class Ga:
    tip = ['buy', 'sell']
    dow = {
        0: "lunes",
        1: "martes",
        2: "miércoles",
        3: "jueves",
        4: "viernes",
        5: "sábado"
    }

    def __init__(self, trade_data: TradeData):
        self.currency = trade_data.currency
        trade_dicts = [trade.__dict__ for trade in trade_data.trades]
        self.df = pd.DataFrame(trade_dicts)
        self.amount_of_trades = len(self.df.symbol)
        self.df = self.df.sort_values(by='close_time')
        print(f'{self.df.to_string()}\n')


my_df = Ga(trade_data)
print(my_df.df.dtypes)
