import pandas as pd
import random
import datetime as dt

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


class RandomDfGenerator:
    def __init__(self, number_of_trades: int):
        self.n_trades = number_of_trades
        self._data_dict = self.rand_init_data()
        self.update_data()

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
            week_day = RandomDfGenerator.is_weekend(date)
        return date

    def rand_init_data(self):
        data = {
            'symbol': [random.choice(PAIRS) for _ in range(self.n_trades)],
            'volume': [int(round(random.randint(1, 10) / 10)) for _ in range(self.n_trades)],
            'order_type': [random.choice(options) for _ in range(self.n_trades)],
            'open_time': [RandomDfGenerator.random_future(start, 54) for _ in range(self.n_trades)]
        }
        return data

    def update_data(self):
        self.data_dict['close_time'] = [RandomDfGenerator.random_future(open_time, 16)
                                        for open_time in self.data_dict['open_time']]

        self.data_dict['open_price'] = [round(random.uniform(PAIRS_RANGE_VAL[pair][0], PAIRS_RANGE_VAL[pair][1]), 5)
                                        for pair in self.data_dict['symbol']]

        self.data_dict['close_price'] = [round(vi + random.uniform(-vi / 25, vi / 25), 5)
                                         for vi in self.data_dict['open_price']]

        self.data_dict['high'] = [round(vi + random.uniform(1.01, 1.2) * abs(vf - vi), 5)
                                  for vf, vi in zip(self.data_dict['close_price'], self.data_dict['open_price'])]

        self.data_dict['low'] = [round(vi - random.uniform(1.02, 1.2) * abs(vf - vi), 5)
                                 for vf, vi in zip(self.data_dict['open_price'], self.data_dict['open_price'])]

    def dates_tester(self):
        for dates in self.data_dict['open_time'], self.data_dict['close_time']:
            for idx, date_to_test in enumerate(dates):
                if date_to_test.weekday() in [5, 6]:
                    print(f'date is weekend {date_to_test} in {idx}')
        else:
            print('done')

    @property
    def data_dict(self):
        return self._data_dict


if __name__ == '__main__':
    test = RandomDfGenerator(8)
    print(test.data_dict)
    test.dates_tester()
