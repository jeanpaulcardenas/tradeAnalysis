from application.config import get_logger
import pandas as pd
import random
import datetime as dt


logger = get_logger(__name__)
PAIRS_RANGE_VAL = {
    'EURUSD': [1.2, 0.95],
    'GPBUSD': [1.4, 1.1],
    'USDCAD': [1.42, 1.21],
    'USDJPY': [140, 120],
    'AUDCAD': [0.99, 0.84],
    'USDCHF': [0.75, 0.6]

}

start = dt.datetime.strptime('2023-12-05 11:00:00', '%Y-%m-%d %H:%M:%S')
PAIRS = list(PAIRS_RANGE_VAL.keys())
options = ['buy', 'sell']


class RandDataGen:
    def __init__(self, number_of_trades: int, currency: str = 'EUR'):
        self.n_trades = number_of_trades
        self._currency = currency
        self._data_dict = self.rand_init_data()
        self.update_data()
        self._df = pd.DataFrame(self.data_dict)

    def rand_init_data(self):
        data = {
            'symbol': [random.choice(PAIRS) for _ in range(self.n_trades)],
            'volume': [int(round(random.randint(1, 10) / 10)) for _ in range(self.n_trades)],
            'order_type': [random.choice(options) for _ in range(self.n_trades)],
            'open_time': [RandDataGen.random_future(start, 54) for _ in range(self.n_trades)]
        }
        return data

    def _add_profits_to_dict(self):
        open_price, close_price, vol, symbol = [self.data_dict[key_string]
                                                for key_string in ['open_price', 'close_price', 'volume', 'symbol']]
        lot = 10 ** 5
        profits = []
        for close_price, open_price, vol, symbol in zip (open_price, close_price, vol, symbol):
            quote = symbol[3:]
            if  quote == self.currency:
                profits.append(round(lot * vol * (close_price - open_price), 2))

            else:
                profits.append(round(lot * vol * (close_price - open_price) / close_price, 2))

        self.data_dict['profit'] = profits

    def update_data(self):
        zeros_list = [0 for _ in range(self.n_trades)]
        self.data_dict['order'] = [1000 + i for i in range(self.n_trades)]
        self.data_dict['close_time'] = [RandDataGen.random_future(open_time, 16)
                                        for open_time in self.data_dict['open_time']]

        self.data_dict['open_price'] = [RandDataGen._random_pair_price(pair) for pair in self.data_dict['symbol']]
        self.data_dict['close_price'] = [RandDataGen._get_close_val(vi) for vi in self.data_dict['open_price']]

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

    @staticmethod
    def _random_pair_price(pair):
        return round(random.uniform(PAIRS_RANGE_VAL[pair][0], PAIRS_RANGE_VAL[pair][1]))

    @staticmethod
    def is_weekend(date):
        return date.weekday() in [5, 6]

    @staticmethod
    def random_future(first, max_weeks) -> dt.datetime:
        week_day = True
        date = dt.datetime.now()
        while week_day:
            val = dt.timedelta(
                weeks=random.randint(0, max_weeks),
                days=random.randint(0, 6),
                hours=random.randint(0, 23),
                seconds=random.randint(0, 3599))
            date = first + val
            week_day = RandDataGen.is_weekend(date)
        return date

    @staticmethod
    def _random_high(open_price: float, close_price: float):
        max_open_close = max(open_price, close_price)
        dif = abs(close_price - open_price)
        return round(max_open_close + random.uniform(1.00, 1.2) * dif, 5)

    @staticmethod
    def _random_low(open_price: float, close_price: float):
        max_open_close = min(open_price, close_price)
        dif = abs(close_price - open_price)
        return round(max_open_close - random.uniform(1.00, 1.2) * dif, 5)

    @staticmethod
    def _get_close_val(initial_val: float):
        return round(initial_val + random.uniform(-initial_val / 25, initial_val / 25), 5)

    @property
    def data_dict(self):
        return self._data_dict

    @property
    def currency(self):
        return self._currency

    @property
    def df(self):
        return self._df


if __name__ == '__main__':
    test = RandDataGen(8)
    print(test.df.to_string())
    print(test.df.dtypes)

