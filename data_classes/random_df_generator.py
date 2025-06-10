from config import get_logger
import pandas as pd
import random
import datetime as dt
import pickle


logger = get_logger(__name__)
PAIRS_RANGE_VAL = {
    'EURUSD': [1.2, 0.95],
    'GPBUSD': [1.4, 1.1],
    'USDCAD': [1.42, 1.21],
    'USDJPY': [150, 140],
    'AUDCAD': [0.99, 0.84],
    'USDCHF': [0.75, 0.6]

}

start = dt.datetime.strptime('2023-12-05 11:00:00', '%Y-%m-%d %H:%M:%S')
PAIRS = list(PAIRS_RANGE_VAL.keys())
options = ['buy', 'sell']


class RandDataGen:
    def __init__(self, number_of_trades: int, max_weeks_total: int, max_weeks_per_trade: int, currency: str = 'EUR'):
        self.n_trades = number_of_trades
        self.mw_total = max_weeks_total
        self.mw_trade = max_weeks_per_trade
        self._currency = currency
        self._data_dict = self.rand_init_data()
        self.update_data()
        self._df = pd.DataFrame(self.data_dict)

    def rand_init_data(self) -> dict:
        """Create a dict with simulated data for 'symbol' 'volume' 'order_type' 'open_time' keys."""
        data = {
            'symbol': [random.choice(PAIRS) for _ in range(self.n_trades)],
            'volume': [round(random.randint(1, 10) / 10, 2) for _ in range(self.n_trades)],
            'order_type': [random.choice(options) for _ in range(self.n_trades)],
            'open_time': [RandDataGen._random_future(start, self.mw_total) for _ in range(self.n_trades)]
        }
        return data

    def _add_profits_to_dict(self) -> None:
        """Add 'profit' key and it's values to 'self.dict'. For pairs that don't contain the account
        currency the profit value is calculated as if the base currency was the account currency (very inaccurate)."""
        open_price, close_price, vol, symbol, order_type = \
        [self.data_dict[key_string] for key_string in ['open_price', 'close_price', 'volume', 'symbol', 'order_type']]

        lot = 10 ** 5
        profits = []
        for open_price, close_price, vol, symbol, order_type in zip(open_price, close_price, vol, symbol, order_type):
            quote = symbol[3:]
            sign = 1 if order_type == 'buy' else -1
            if quote == self.currency:
                profits.append(round(sign * lot * vol * (close_price - open_price), 2))

            else:
                profits.append(round(sign * lot * vol * (close_price - open_price) / close_price, 2))

        self.data_dict['profit'] = profits

    def update_data(self) -> None:
        """Updates dict with 'order', 'close_time', 'close_price', 'high', 'low', 'profit', 'sl', 'tp',
        'commission', 'taxes', 'swap', 'base', 'quote'"""
        zeros_list = [0 for _ in range(self.n_trades)]
        self.data_dict['order'] = [1000 + i for i in range(self.n_trades)]
        self.data_dict['close_time'] = [RandDataGen._random_future(open_time, self.mw_trade)
                                        for open_time in self.data_dict['open_time']]

        self.data_dict['open_price'] = [RandDataGen._random_pair_price(pair) for pair in self.data_dict['symbol']]
        self.data_dict['close_price'] = [RandDataGen._get_close_val(vi) for vi in self.data_dict['open_price']]
        self.data_dict['delta_time'] = [end_date - start_date for end_date, start_date in
                                         zip(self.data_dict['close_time'], self.data_dict['open_time'])]
        self.data_dict['high'] = [RandDataGen._random_high(vi, vf)
                                  for vi, vf in zip(self.data_dict['open_price'], self.data_dict['close_price'])]

        self.data_dict['low'] = [RandDataGen._random_low(vi, vf)
                                 for vi, vf in zip(self.data_dict['open_price'], self.data_dict['close_price'])]

        self._add_profits_to_dict()
        self.data_dict['sl'] = zeros_list
        self.data_dict['tp'] = zeros_list
        self.data_dict['commission'] = zeros_list
        self.data_dict['taxes'] = zeros_list
        self.data_dict['swap'] = zeros_list
        self.data_dict['base'] = [symbol[3:] for symbol in self.data_dict['symbol']]
        self.data_dict['quote'] = [symbol[:3] for symbol in self.data_dict['symbol']]

    @staticmethod
    def _random_pair_price(pair: str) -> float:
        """Returns a price from a symbol within the real max and min values for a given pair."""
        return round(random.uniform(PAIRS_RANGE_VAL[pair][0], PAIRS_RANGE_VAL[pair][1]), 5)

    @staticmethod
    def _is_weekend(date: dt.datetime) -> bool:
        """checks weather a date is weekend or not. Returns true if date day is weekend"""
        return date.weekday() in [5, 6]

    @staticmethod
    def _random_future(first: dt.datetime, max_weeks: int) -> dt.datetime:
        """Returns a date from first to max_weeks to the future"""
        week_day = True
        date = dt.datetime.now()
        while week_day:
            val = dt.timedelta(
                weeks=random.randint(0, max_weeks),
                days=random.randint(0, 6),
                hours=random.randint(0, 23),
                seconds=random.randint(0, 3599))
            date = first + val
            if val.total_seconds() != 0:
                week_day = RandDataGen._is_weekend(date)
        return date

    @staticmethod
    def _random_high(open_price: float, close_price: float) -> float:
        """Returns a random high number from the max value between open and close price
         up to 30% * pips gained. Used to get 'high' values for 'self.data_dict'"""
        max_open_close = max(open_price, close_price)
        dif = abs(close_price - open_price)
        return round(max_open_close + random.uniform(1.00, 1.3) * dif, 5)

    @staticmethod
    def _random_low(open_price: float, close_price: float) -> float:
        """Returns a random low number from the max value between open and close price
        down to 30% * pips gained. Used to get 'low' values for 'self.data_dict'"""
        min_open_close = min(open_price, close_price)
        dif = abs(close_price - open_price)
        return round(min_open_close - random.uniform(1.00, 1.3) * dif, 5)

    @staticmethod
    def _get_close_val(initial_val: float) -> float:
        """Gets close_price value for an initial data dictionary. Used to get 'close_price' data"""
        return round(initial_val + random.uniform(-initial_val / 25, initial_val / 25), 5)

    @property
    def data_dict(self) -> dict:
        return self._data_dict

    @property
    def currency(self) -> str:
        return self._currency

    @property
    def df(self) -> pd.DataFrame:
        return self._df


if __name__ == '__main__':
    test = RandDataGen(100, max_weeks_total=54, max_weeks_per_trade=1)
    with open('../data/cached_random_dict.pkl', 'wb') as f:
        pickle.dump(test.df.to_dict(), f)
    print(test.df.to_string())
    print(test.df.dtypes)
