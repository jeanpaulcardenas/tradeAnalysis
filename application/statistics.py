from application.mt4data import Trade, TradeData, Balance
import pandas as pd
import numpy as np
import pickle
from application.config import get_logger

with open("cached_trade_data.pkl", "rb") as f:
    test_trade_data = pickle.load(f)

logger = get_logger(__name__)


class MetricsObject:
    tip = ['buy', 'sell']
    dow = {
        0: 'monday',
        1: 'tuesday',
        2: 'wednesday',
        3: 'thursday',
        4: 'friday',
        5: 'saturday',
        6: 'sunday'
    }

    def __init__(self, trade_data: TradeData):
        self._currency = trade_data.currency
        trade_dicts = [trade.__dict__ for trade in trade_data.forex_trades]
        self.df = pd.DataFrame(trade_dicts)
        self._amount_of_trades = self.get_amount_of_trades()
        self.sort_df_values(by='open_time')
        self.complete_dataframe()
        print(self.df.to_string())

    def sort_df_values(self, by):
        self.df.sort_values(by=by, inplace=True)

    def get_amount_of_trades(self) -> int:
        return self.df.shape[0]

    def complete_dataframe(self):
        self.df['max_possible_gain'] = self.df.apply(self.get_max_gain, axis='columns')
        self.df['max_possible_loss'] = self.df.apply(lambda row: round(self.get_max_gain(row, True), 2), axis='columns')
        self.df['accumulative profit'] = np.add.accumulate(self.df.profit)
        self.df['day_of_week'] = [self.dow[date.weekday()] for date in self.df.close_time]
        self.df['won_trade'] = np.where(self.df.profit > 0, True, False)

    def get_max_gain(self, row: pd.Series, max_loss: bool = False) -> float:
        limits = [row.high, row.low]
        if max_loss:
            limits.reverse()
        gain = - 10 ** 100
        if row.type == 'buy':
            gain = self.get_trade_income(row, limits[0])
        elif row.type == 'sell':
            gain = -self.get_trade_income(row, limits[1])

        if self._max_is_less_than_actual(gain, row.profit, max_loss):
            logger.warning(f'In trade order: {row.order} max_possible_gain/loss {round(gain, 2)} '
                           f'is less than profit {row.profit}')
            return row.profit
        return gain

    @staticmethod
    def _max_is_less_than_actual(maxim: float, actual: float, reverse: bool = False) -> bool:
        if reverse:
            return round(maxim, 2) > round(actual, 2)
        else:
            return round(maxim, 2) < round(actual, 2)

    def get_trade_income(self, row: pd.Series, final_value) -> float:
        lot = 10 ** 5
        if row.quote == self.currency:
            return lot * row.volume * (final_value - row.open_price)

        elif row.base == self.currency:
            return lot * row.volume * (final_value - row.open_price) / final_value

        elif row.profit:
            return abs(row.profit) * (final_value - row.open_price) / (row.close_price - row.open_price)

        else:
            return row.profit

    @property
    def amount_of_trades(self) -> int:
        return self.df.shape[0]

    @property
    def currency(self) -> str:
        return self._currency


my_df = Ga(test_trade_data)
print(my_df.df.dtypes)
