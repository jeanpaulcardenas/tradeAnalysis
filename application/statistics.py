from application.mt4data import Trade, TradeData, Balance  # noqa: F401
from application.config import get_logger
from dataclasses import fields
import pandas as pd
import pickle

with open("cached_trade_data.pkl", "rb") as f:
    test_trade_data = pickle.load(f)

logger = get_logger(__name__)


def zero_division_to_zero(func):
    def wrapper(self):
        try:
            return func(self)
        except ZeroDivisionError:
            logger.warning(f"{__name__} {func.__class__} zero division error! returned 0 instead. ")
            return 0
    return wrapper


class Metrics:
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
        if not self.df.empty:
            self.df.convert_dtypes()
            self.sort_df_values(by='open_time')
            self._complete_dataframe()
        else:
            keys = [field.name for field in fields(Trade)]\
                 + ['won_trade', 'max_possible_gain', 'max_possible_loss', 'accumulative_profit', 'day of week', 'pip']
            self.df = pd.DataFrame(columns=keys)
            print(self.df.to_string())

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
        """trades won / number of trades"""
        return self.n_trades_won/self.n_of_trades

    @property
    def gross_revenue(self) -> float:
        """sum of all wining trades profit"""
        return self.df.profit[self.df['won_trade']].sum()

    @property
    def gross_loss(self) -> float:
        """sum of all losing trades loss"""
        return self.df.profit[self.df.won_trade == 0].sum()

    @property
    def net_income(self) -> float:
        """returns the sum of all profits. (loss - earnings)"""
        return self.gross_revenue + self.gross_loss

    @property
    @zero_division_to_zero
    def expectancy(self) -> float:
        """	Shows average expected outcome per trade — excellent for evaluation."""
        return self.net_income/self.n_of_trades

    @property
    @zero_division_to_zero
    def avg_win_trade_profit(self) -> float:
        """average winning trade profit"""
        return self.gross_revenue/self.n_trades_won

    @property
    @zero_division_to_zero
    def avg_lose_trade_loss(self) -> float:
        """average losing trade loss"""
        return self.gross_loss/self.n_trades_loss

    @property
    def avg_win_over_loss(self) -> float:
        """ratio between the average won trade profit to the average losing trade loss """
        return self.avg_win_trade_profit/self.avg_lose_trade_loss

    @property
    @zero_division_to_zero
    def profit_factor(self) -> float:
        """profit factor: gross loss / gross gross_revenue"""
        return self.gross_revenue/self.gross_loss

    @property
    def perfect_efficiency_income(self) -> float:
        """profit if closed trade at best possible moment in between close time and open time"""
        return self.df.max_possible_gain.sum()

    @property
    @zero_division_to_zero
    def efficiency(self) -> float:
        """returns the ratio between the obtained revenue (only winning trades) to the 'perfect possible income'
        it's: gross_revenue/perfect_efficiency_income"""
        return self.gross_revenue/self.perfect_efficiency_income

    @property
    def most_traded(self) -> str:
        """returns the symbol of the most traded pair"""
        try:
            return self.df.symbol.mode()[0]
        except KeyError:
            return ''

    @property
    def n_of_trades(self) -> int:
        return self.df.shape[0]

    @property
    def currency(self) -> str:
        return self._currency

    @property
    def consecutive_wins(self):
        return self._max_consecutive_streak(True)

    @property
    def consecutive_losses(self):
        return self._max_consecutive_streak(False)

    @property
    def largest_earning_trade(self):
        return self.df.profit.max()

    @property
    def largest_loss_trade(self):
        return self.df.profit.min()

    def get_max_run_up(self):
        """returns the value of the max run up """
        accumulative_profit = self.df.accum.to_list()
        min_val = 0
        max_runup = 0
        for val in accumulative_profit:
            if val < min_val:
                min_val = val
            elif val - min_val > max_runup:
                max_runup = val - min_val
        return max_runup

    def sort_df_values(self, by):
        """sorts dataframe by values 'by'. 'by' must be any of the available column names"""
        self.df.sort_values(by=by, inplace=True, ignore_index=True)

    def _max_consecutive_streak(self, condition: bool = True):
        """Returns the maximum consecutive streak of trades where won_trade == condition"""
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

    def _complete_dataframe(self):
        """Add key columns to the dataframe for analysis.

        Columns: max_possible_gain, max_possible_loss, day_of_week, won_trade, accumulative_profit, 'pips'"""

        self.df['max_possible_gain'] = self.df.apply(func=self._get_max_gain, axis='columns')
        self.df['max_possible_loss'] = self.df.apply(func=lambda row: round(self._get_max_gain(row, True), 2),
                                                     axis='columns')
        self.df['accumulative_profit'] = self.df.profit.cumsum()
        self.df['day_of_week'] = self.df.close_time.apply(func=lambda date: Metrics.dow[date.weekday()])
        self.df['won_trade'] = (self.df.profit > 0)
        self.df['pips'] = self.df.apply(Metrics._get_pips, axis='columns')
        self.df.symbol = self.df.symbol.astype('category')
        self.df.order_type = self.df.symbol.astype('category')

    def _get_max_gain(self, row: pd.Series, max_loss: bool = False) -> float:
        """gets max gain possible gain for a trade, taking into account whether it's a buy or a sell trade.
        max_loss inverts the logic, so we can calculate the maximum possible loss. It's done by comparing it to what
        the profit would have been if closed in high price (or low price for max_loss=True)"""

        limits = [row.high, row.low]
        if max_loss:
            limits.reverse()
        gain = - 10 ** 100
        if row.order_type == 'buy':
            gain = self._get_trade_profit(row, limits[0])
        elif row.order_type == 'sell':
            gain = -self._get_trade_profit(row, limits[1])

        if Metrics._max_is_less_than_actual(gain, row.profit, max_loss):
            logger.warning(f'In trade order: {row.order} max_possible_gain/loss {round(gain, 2)} '
                           f'is less than profit {row.profit}')
            return row.profit
        return gain

    def _get_trade_profit(self, row: pd.Series, final_value) -> float:
        """Gets the profit from open_price to a settable final price.
        if account currency is not the quote nor base currency, the rule of three is used.
        This might not work when open and close price are equal, in which case profit returned is 0."""

        lot = 10 ** 5
        if row.quote == self.currency:
            return lot * row.volume * (final_value - row.open_price)

        elif row.base == self.currency:
            return lot * row.volume * (final_value - row.open_price) / final_value

        elif row.profit:
            denominator = row.close_price - row.open_price
            if denominator == 0:
                logger.warning(f"in trade {row.order} open and close prices are equal: {row.open_price},"
                               f" unable to calculate max possible nor min possible be rule of three")
                return row.profit
            return abs(row.profit) * (final_value - row.open_price) / (row.close_price - row.open_price)

        else:
            return row.profit

    @staticmethod
    def _get_pips(row: pd.Series):
        diff = row.close_price - row.open_price
        if 'JPY' in row.symbol:
            return 100 * diff
        else:
            return 10 ** 4 * diff

    @staticmethod
    def _max_is_less_than_actual(maxim: float, actual: float, reverse: bool = False) -> bool:
        """return true when a maxim value is less than a close price. Used to handle possible illogical results
        in get_max_possible when best possible profit is less than actual profit"""

        if reverse:
            return round(maxim, 2) > round(actual, 2)
        else:
            return round(maxim, 2) < round(actual, 2)


my_metrics = Metrics(test_trade_data)
print(my_metrics.df.to_string())

for attr_name in dir(my_metrics.__class__):
    attr = getattr(my_metrics.__class__, attr_name)
    if isinstance(attr, property):
        print(f"{attr_name}: {getattr(my_metrics, attr_name)}")
