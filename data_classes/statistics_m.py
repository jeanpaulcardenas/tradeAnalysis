from data_classes.mt4data import Trade, TradeData, Balance  # noqa: F401
from config import _METRICS_DF_KEYS, get_logger
import datetime as dt
import numpy as np
import pandas as pd
import pickle

logger = get_logger(__name__)  # Create loging instance for this module.


def zero_division_to_zero(func):
    """Decorator that returns zero when a 'ZeroDivisionError' occurs."""

    def wrapper(self):
        try:
            return func(self)
        except ZeroDivisionError:
            logger.warning(f"{__name__} {func.__class__} zero division error! returned 0 instead. ")
            return 0

    return wrapper


class Metrics:
    _CURRENCIES = {
        'EUR': '€',
        'USD': '$',
        'AUD': '$',
        'CAD': '$',
        'NZD': '$',
        'GBP': '£',
        'JPY': '¥',
    }
    _DOW = {
        0: 'monday',
        1: 'tuesday',
        2: 'wednesday',
        3: 'thursday',
        4: 'friday',
        5: 'saturday',
        6: 'sunday'
    }

    def __init__(self, trades_df: pd.DataFrame, balance_df: pd.DataFrame, currency: str):
        self.df = trades_df.reset_index(drop=True)
        self.balance_df = balance_df
        self._currency = currency.upper()
        if not self.df.empty:
            self.df.convert_dtypes()
            self.sort_df_values(by='close_time')
            self._complete_dataframe()

        # Create a dataframe with expected columns for self.df without rows data.
        # This avoids errors when instantiating a Metrics object with empty trade data.
        else:
            keys = _METRICS_DF_KEYS
            self.df = pd.DataFrame(columns=keys)

    @classmethod
    def from_trade_data(cls, trade_data: TradeData):
        """Creates a Metrics object from a df created from a dataframe with all columns of self.df existing.
        Intended to create objects from self.df themselves"""
        currency = trade_data.currency
        trade_dict = [trade.__dict__ for trade in trade_data.forex_trades]  # Create dict from Trade object
        df = pd.DataFrame(trade_dict)
        balance_dict = [balance.__dict__ for balance in trade_data.balances]  # Crate dict from Balance object
        balance_df = pd.DataFrame(balance_dict)
        return cls(df, balance_df, currency)

    @property
    def currency(self) -> str:
        """Returns account currency as string."""
        return self._currency

    @property
    def currency_symbol(self):
        """Returns account currency symbol, if currency symbol is not supported, '$' will be return"""
        try:
            return Metrics._CURRENCIES[self.currency]
        except KeyError:
            return Metrics._CURRENCIES['USD']

    @property
    def n_of_trades(self) -> int:
        """Returns total number of trades."""
        return self.df.shape[0]

    @property
    def n_trades_won(self) -> float:
        """Counts the number of winning trades"""
        return self.df.won_trade.sum()

    @property
    def n_trades_loss(self) -> float:
        """Counts the number of losing trades (negative profit)"""
        return (self.df.won_trade == 0).sum()

    @property
    @zero_division_to_zero
    def win_rate(self) -> float:
        """Trades won / number of trades"""
        return self.n_trades_won / self.n_of_trades

    @property
    def gross_revenue(self) -> float:
        """Sum of all wining trades profit"""
        return self.df.profit[self.df['won_trade']].sum()

    @property
    def gross_loss(self) -> float:
        """Sum of all losing trades loss"""
        return self.df.profit[self.df.won_trade == 0].sum()

    @property
    def net_income(self) -> float:
        """Returns the sum of all profits. (loss - earnings)"""
        return self.gross_revenue + self.gross_loss

    @property
    @zero_division_to_zero
    def expectancy(self) -> float:
        """	Shows average expected outcome per trade."""
        return self.net_income / self.n_of_trades

    @property
    @zero_division_to_zero
    def avg_win_trade_profit(self) -> float:
        """Average winning trade profit"""
        return self.gross_revenue / self.n_trades_won

    @property
    @zero_division_to_zero
    def avg_lose_trade_loss(self) -> float:
        """Average losing trade loss"""
        return self.gross_loss / self.n_trades_loss

    @property
    def avg_win_over_loss(self) -> float:
        """Ratio between the average won trade profit to the average losing trade loss """
        return self.avg_win_trade_profit / self.avg_lose_trade_loss

    @property
    @zero_division_to_zero
    def profit_factor(self) -> float:
        """Profit factor: gross loss / gross gross_revenue"""
        return abs(self.gross_revenue / self.gross_loss)

    @property
    def perfect_efficiency_income(self) -> float:
        """Profit if closed trade at best possible moment in between close time and open time"""
        return self.df.max_possible_gain.sum()

    @property
    @zero_division_to_zero
    def efficiency(self) -> float:
        """Returns the ratio between the obtained revenue (only winning trades) to the 'perfect possible income'
        it's: gross_revenue/perfect_efficiency_income"""
        return self.gross_revenue / self.perfect_efficiency_income

    @property
    def most_traded(self) -> str:
        """Returns the symbol of the most traded pair"""
        try:
            return self.df.symbol.mode()[0]
        except KeyError:
            return ''

    @property
    def consecutive_wins(self) -> int:
        """Returns max number of consecutive wins"""
        return self._max_consecutive_streak(True)

    @property
    def consecutive_losses(self) -> int:
        """Returns count of max consecutive losses"""
        return self._max_consecutive_streak(False)

    @property
    def largest_earning_trade(self) -> float:
        """Returns largest profit trade amount"""
        return self.df.profit.max()

    @property
    def largest_loss_trade(self) -> float:
        """Returns largest lose trade amount"""
        return self.df.profit.min()

    @property
    def std_profit(self) -> float:
        """Returns standard deviation of profit column"""
        if self.n_of_trades < 2:
            return 0
        else:
            return self.df.profit.std()

    @property
    def max_runup(self):
        return self.get_max_run()

    @property
    def max_drawdown(self):
        return - self.get_max_run(drawdown=True)

    def get_max_run(self, drawdown=False) -> float:
        """Returns the value of the max run up of profit colum.  For drawdown = False get max drawdown"""
        # if we want the dropdown, we just flip the graph by changing sign (we flip the graph)
        cum_profit = (-1) ** drawdown * self.df.cum_profit
        min_val = 0
        max_runup = 0
        for val in cum_profit:
            if val < min_val:
                min_val = val
            elif val - min_val > max_runup:
                max_runup = val - min_val
        return max_runup

    def sort_df_values(self, by):
        """sorts dataframe by values 'by'. 'by' must be any of the available column names"""
        self.df.sort_values(by=by, inplace=True, ignore_index=True)

    def _complete_dataframe(self) -> None:
        """Add key columns to the dataframe for analysis.

        Columns: max_possible_gain, max_possible_loss, day_of_week, won_trade, accumulative_profit, 'pips'"""

        self.df['max_possible_gain'] = self.df.apply(func=lambda row: round(self._get_max_gain(row, False), 2),
                                                     axis='columns')
        self.df['max_possible_loss'] = self.df.apply(func=lambda row: round(self._get_max_gain(row, True), 2),
                                                     axis='columns')
        self.df['cum_profit'] = self.df.profit.cumsum()
        self.df['day_of_week'] = self.df.close_time.apply(func=lambda date: Metrics._DOW[date.weekday()])
        self.df['won_trade'] = (self.df.profit > 0)
        self.df['pips'] = self.df.apply(Metrics._get_pips, axis='columns')
        self.df.symbol = self.df.symbol.astype('category')
        self.df.order_type = self.df.order_type.astype('category')
        self.df.day_of_week = self.df.day_of_week.astype('category')
        self.df = self.df[_METRICS_DF_KEYS]

    def _max_consecutive_streak(self, condition: bool = True) -> int:
        """Returns the maximum consecutive streak of trades where won_trade == True | False"""
        max_streak = 0
        streak = 0
        for val in self.df.won_trade:
            if val == condition:
                streak += 1
                if streak > max_streak:
                    max_streak = streak
            else:
                streak = 0
        return max_streak

    def _get_max_gain(self, row: pd.Series, max_loss: bool = False) -> float:
        """gets max gain possible gain for a trade, taking into account whether it's a buy or a sell trade.
        max_loss inverts the logic, so we can calculate the maximum possible loss. It's done by comparing it to what
        the profit would have been if closed in high price (or low price for max_loss=True)"""

        limits = [row.high, row.low]
        if max_loss:
            # reverse if we're looking for max loss instead of max gain
            limits.reverse()
        gain = - 10 ** 100
        if row.order_type == 'buy':
            gain = self._get_trade_profit(row, limits[0])
        elif row.order_type == 'sell':
            gain = self._get_trade_profit(row, limits[1])

        if Metrics._max_is_less_than_actual(gain, row.profit, max_loss):
            logger.warning(f'In trade order: {row.order} max_possible_gain/loss {round(gain, 2)} '
                           f'is less than profit {row.profit}')
            return row.profit
        return gain

    def _get_trade_profit(self, row: pd.Series, final_value) -> float:
        """Gets the profit from open_price to a settable final price.
        if account currency is not the quote nor base currency, the rule of three is used.
        This might not work when open and close price are equal, in which case profit returned is 0."""

        lot = 10 ** 5  # a lot is 100 000 units
        sign = (-1) ** (row.order_type == 'sell')
        if row.quote == self.currency:
            return sign * lot * row.volume * (final_value - row.open_price)

        elif row.base == self.currency:
            return sign * lot * row.volume * (final_value - row.open_price) / final_value
        # TODO: create logic for cases where denom == 0. Calling the API to get account_currency/quote would satisfy
        elif row.profit:
            denominator = row.close_price - row.open_price
            if denominator == 0:  # we are not able to calculate by rule of 3 when open price == close price
                logger.warning(f"in trade {row.order} open and close prices are equal: {row.open_price},"
                               f" unable to calculate max possible nor min possible be rule of three")
                return row.profit
            # apply rule of 3
            return row.profit * (final_value - row.open_price) / (row.close_price - row.open_price)

        else:
            return row.profit

    def income_by_period(self, column: str, frequency: str) -> pd.DataFrame:
        """returns a grouped dataframe with columns df[column].unique() and index my frequency: frequency end's."""

        df = self.df[['close_time']].copy()
        try:
            if not column:
                # if no column, just return profit for all rows of df
                df = self.df[['close_time', 'profit']]

            else:
                for item in self.df[column].unique():
                    # create column for each unique value in df[column] with values = 'profit'
                    df[item] = self.df.profit[self.df[column] == item]

        except KeyError:
            logger.error(f"Column parameter for income_by_period '{column}'"
                         f" does not exist in dataframe:\n {self.df.head()}")
            return pd.DataFrame()
        #
        grouped_df = df.groupby(pd.Grouper(key='close_time', freq=frequency)).sum()
        logger.info(f"This is the grouped df:\n {grouped_df.head()}")
        return grouped_df

    @staticmethod
    def bootstrap_confidence_interval_mean(
            data: pd.Series, n_iterations: int = 10000, ci: int = 95) -> (float, float, str):
        """Returns a Confidence Interval of ci= percentage of the ci, statistic = numpy function (np.mean, np.std)
        and n_iterations"""
        msg = 'This 95% CI is based on historical trade outcomes. Future results may differ.'
        if n_iterations < 1 or 1 > ci > 100 or not (isinstance(data[0], float) or isinstance(data[0], int)):
            logger.warning(f"can't run _bootstrap_confidence_interval_mean function with"
                           f"params: iterations={n_iterations}, ci={ci}")
            return 0, 0, ''
        data = np.asarray(data)
        size = data.size
        if size < 2:
            msg = 'insufficient amount of trades to calculate confidence intervals'
            return 0, 0, msg
        if size < 30:
            msg = 'bootstrap CI sample less than 30! result not very meaningful'
            logger.info(f"{__name__} {__class__} {msg}")
        # produce n iterations of size data.size from data, to create samples. Values can repeat (replace=True)
        samples = np.random.choice(data, size=(n_iterations, data.size), replace=True)
        # get the mean of the n samples
        stats = np.apply_along_axis(np.mean, axis=1, arr=samples)
        lower = np.percentile(stats, (100 - ci) / 2)
        upper = np.percentile(stats, 100 - (100 - ci) / 2)
        return lower, upper, msg

    @staticmethod
    def _get_pips(row: pd.Series) -> int:
        """Get pips as 0.0001 pair value difference. for JPY pair's it's 0.01."""
        diff = abs(row.close_price - row.open_price)
        sign = 1
        if isinstance(row.won_trade, bool):
            sign = (-1) ** (row.won_trade + 1)
        if 'JPY' in row.symbol:
            # for JPY pairs a pip is 0.01 times bigger than the minimum decimal
            return int(round(sign * 100 * diff, 0))
        else:
            # for most other pairs a pip is 0.0001
            return int(round(sign * 10 ** 4 * diff, 0))

    @staticmethod
    def _max_is_less_than_actual(maxim: float, actual: float, reverse: bool = False) -> bool:
        """return true when a maxim value is less than a close price. Used to handle possible illogical results
        in get_max_possible when best possible profit is less than actual profit"""

        if reverse:
            return round(maxim, 2) > round(actual, 2)
        else:
            return round(maxim, 2) < round(actual, 2)


def metrics_between_dates(metrics_obj: Metrics, start_date: dt.datetime, end_date: dt.datetime) -> Metrics:
    """Returns a metric object from a metric object given a start date and end date to filter."""
    df = metrics_obj.df
    df_ranged = df[(df['open_time'] >= start_date) & (df['close_time'] <= end_date)].reset_index(drop=True)
    return Metrics(df_ranged, pd.DataFrame(), metrics_obj.currency)


# Running this module as main loads a Trade object, creates metrics instance and prints dataframe and log all properties
if __name__ == '__main__':
    with open('../data/cached_trade_data.pkl', 'rb') as f:
        # If trade object does not exist, run 'mt4data.py' as main
        # note: running 'mt4data.py' (THIS WILL USE API CALLS)
        test_trade_data = pickle.load(f)

    my_metrics = Metrics.from_trade_data(test_trade_data)
    print(my_metrics.df.to_string())
    print(my_metrics.bootstrap_confidence_interval_mean(my_metrics.df.profit[my_metrics.df.won_trade]))

    for attr_name in dir(my_metrics.__class__):
        attr = getattr(my_metrics.__class__, attr_name)
        if isinstance(attr, property):
            logger.info(f"{attr_name}: {getattr(my_metrics, attr_name)}")  # Print all metrics properties
