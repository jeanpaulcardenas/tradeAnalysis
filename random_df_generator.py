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
start = dt.datetime.strptime('2024-12-05 11:00:00', '%Y-%m-%d %H:%M:%S')
PAIRS = list(PAIRS_RANGE_VAL.values())
options = ['buy', 'sell']
POSSIBLE_DAYS = {
    0: [0, 1, 2, 3, 4],
    1: [0, 1, 2, 3, 6],
    2: [0, 1, 2, 5, 6],
    3: [0, 1, 4, 5, 6],
    4: [0, 3, 4, 5, 6]
}


def random_future(first, max_weeks, h) -> dt.datetime:
    val = dt.timedelta(
        weeks=random.randint(0, max_weeks),
        days=random.choice(POSSIBLE_DAYS[first.weekday()]),
        hours=random.randint(h, 5),
        seconds=random.randint(0, 3000))
    return first + val


my_range = range(80)


data = {
    'symbol': [random.choice(PAIRS) for _ in my_range],
    'volume': [random.randint(1, 10) / 10 for _ in my_range],
    'order_type': [random.choice(options) for _ in my_range],
    'open_time': [random_future(start, 50, 5) for _ in my_range]
}
