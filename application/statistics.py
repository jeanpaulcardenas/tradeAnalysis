from application.mt4data import Trade, TradeData, Balance  # noqa: F401
import pandas as pd
import pickle
from application.config import get_logger

with open("cached_trade_data.pkl", "rb") as f:
    test_trade_data = pickle.load(f)

logger = get_logger(__name__)


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
        self.df.convert_dtypes()
        self._n_of_trades = self.get_n_of_trades()
        self.sort_df_values(by='open_time')
        self._complete_dataframe()

        # self.mom_grow_seriesth = 0
        # self.max_run_up = round(self.get_runup())
        # self.max_drawdown = round(self.get_drawdown())
        # self.t_time_mean = st.mean(self.df.time)
        # self.t_efficiency = divide(self.t_net_income, self.max_income_possible)
        # self.act_count_df = self.act_count()
        # self.most_traded = self.get_most_traded()
        print(self.df.to_string())

    @property
    def n_trades_won(self) -> float:
        return self.df.won_trade.sum()

    @property
    def n_trades_loss(self) -> float:
        return (self.df.won_trade == 0).sum()

    @property
    def trades_win_rate(self) -> float:
        return self.n_trades_won/self.n_trades_loss

    @property
    def gross_revenue(self) -> float:
        return self.df.profit[self.df['won_trade']].sum()

    @property
    def gross_loss(self) -> float:
        return self.df.profit[self.df.won_trade == 0].sum()

    @property
    def net_income(self) -> float:
        return self.gross_revenue + self.gross_loss

    @property
    def avg_trade_profit(self) -> float:
        return self.net_income/self.n_of_trades

    @property
    def profit_factor(self) -> float:
        """profit factor: gross loss / gross gross_revenue"""
        return self.gross_revenue/self.gross_loss

    @property
    def perfect_efficiency_income(self) -> float:
        """profit if closed trade at best possible moment in between close time and open time"""
        return self.df.max_possible_gain.sum()

    @property
    def efficiency(self) -> float:
        return self.gross_revenue/self.perfect_efficiency_income

    @property
    def most_traded(self) -> str:
        return self.df.symbol.mode()[0]

    def sort_df_values(self, by):
        """sorts dataframe by values 'by'. 'by' must be any of the available column names"""
        self.df.sort_values(by=by, inplace=True, ignore_index=True)

    def get_n_of_trades(self) -> int:
        return self.df.shape[0]

    def _complete_dataframe(self):
        """Add key columns to the dataframe for analysis.

        Columns: max_possible_gain, max_possible_loss, day_of_week, won_trade, accumulative_profit"""

        self.df['max_possible_gain'] = self.df.apply(self.get_max_gain, axis='columns')
        self.df['max_possible_loss'] = self.df.apply(lambda row: round(self.get_max_gain(row, True), 2), axis='columns')
        self.df['accumulative_profit'] = self.df.profit.cumsum()
        self.df['day_of_week'] = [self.dow[date.weekday()] for date in self.df.close_time]
        self.df['won_trade'] = (self.df.profit > 0)
        self.df.symbol = self.df.symbol.astype('category')
        self.df.type = self.df.symbol.astype('category')

    def get_max_gain(self, row: pd.Series, max_loss: bool = False) -> float:
        """gets max gain possible gain for a trade, taking into account whether it's a buy or a sell trade.
        max_loss inverts the logic, so we can calculate the maximum possible loss. It's done by comparing it to what
        the profit would have been if closed in high price (or low price for max_loss=True)"""

        limits = [row.high, row.low]
        if max_loss:
            limits.reverse()
        gain = - 10 ** 100
        if row.type == 'buy':
            gain = self.get_trade_profit(row, limits[0])
        elif row.type == 'sell':
            gain = -self.get_trade_profit(row, limits[1])

        if self._max_is_less_than_actual(gain, row.profit, max_loss):
            logger.warning(f'In trade order: {row.order} max_possible_gain/loss {round(gain, 2)} '
                           f'is less than profit {row.profit}')
            return row.profit
        return gain

    def get_trade_profit(self, row: pd.Series, final_value) -> float:
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
    def _max_is_less_than_actual(maxim: float, actual: float, reverse: bool = False) -> bool:
        """return true when a maxim value is less than a close price. Used to handle possible illogical results
        in get_max_possible when best possible profit is less than actual profit"""

        if reverse:
            return round(maxim, 2) > round(actual, 2)
        else:
            return round(maxim, 2) < round(actual, 2)

    @property
    def n_of_trades(self) -> int:
        return self.df.shape[0]

    @property
    def currency(self) -> str:
        return self._currency


my_metrics = Metrics(test_trade_data)

for attr_name in dir(my_metrics.__class__):
    attr = getattr(my_metrics.__class__, attr_name)
    if isinstance(attr, property):
        print(f"{attr_name}: {getattr(my_metrics, attr_name)}")
