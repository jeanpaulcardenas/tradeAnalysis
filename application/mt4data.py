import datetime
from application.constants import *
from application.config import get_logger
from bs4 import BeautifulSoup
from dataclasses import dataclass
import datetime as dt
import tradermade as tm
import requests
import pandas as pd
import base64
import re
import pickle

logger = get_logger(__name__)


@dataclass
class Trade:
    order: int
    open_time: dt.datetime
    order_type: str
    volume: float
    symbol: str
    open_price: float
    sl: float
    tp: float
    close_time: dt.datetime
    close_price: float
    commission: float
    taxes: float
    swap: float
    profit: float
    high: float = 0
    low: float = 0
    time_opened: dt.timedelta = 0
    base: str = ''
    quote: str = ''


@dataclass
class Balance:
    order: int
    date: datetime
    amount: float
    balance_type: str = ''


class TxtParser:
    _ABOVE_TRADES_REF_LINE = '   <td>Price</td><td>Commission</td><td>Taxes</td><td>Swap</td><td>Profit</td></tr>'
    _ABOVE_ACCT_REF_LINE = '<tr align=left>'

    def __init__(self, txt: str):
        """txt is the raw html string of the mt4 statement"""

        self._raw_html = txt
        self.my_html_list = TxtParser._create_html_list(self.raw_html)
        logger.info(f"TxtParser creation")

    def get_operations_info(self) -> list[list[str]]:
        """returns a list with the meaningful data of the trades and balances of the MT4 operations report"""

        operations_raw = TxtParser._extract_section_from_html_list(
            my_list=self.my_html_list,
            start=TxtParser._ABOVE_TRADES_REF_LINE,
        )
        operations_info = list()
        for line in operations_raw:
            td_content = TxtParser._parse_td(line)
            operations_info.append(td_content)
        return operations_info

    def get_account_info(self) -> dict:
        """returns number account, name, currency and leverage from MT4 report"""

        acct_info_raw = TxtParser._extract_section_from_html_list(
            my_list=self.my_html_list,
            start=TxtParser._ABOVE_ACCT_REF_LINE,
        )
        acct_info = dict()
        for line in acct_info_raw:
            td_content = TxtParser._parse_td(line)
            values = re.split(r': ', td_content[0])

            try:
                acct_info[values[0].lower()] = values[1]
            except IndexError:
                pass
        return acct_info

    @classmethod
    def from_dash_upload(cls, uploaded_file, unicode_encoding='utf-8'):
        """decodes string content from dash upload.
        returns a list of string, each index represents each line in the .txt"""

        decoded = base64.b64decode(uploaded_file)
        file_text = decoded.decode(unicode_encoding)
        file_text = file_text.replace('\r\n', '\n')
        return cls(file_text)

    @classmethod
    def from_filepath(cls, filepath: str):
        """Instantiates a class object from a filepath to the MT4 report"""
        with open(filepath) as d:
            html_text = d.read()

        return cls(html_text)

    @staticmethod
    def _create_html_list(my_txt_string: str) -> list:
        """returns a list of strings with each line being a line from my_txt_string"""

        return my_txt_string.split('\n')

    @staticmethod
    def _extract_section_from_html_list(my_list: list, start: str) -> list:
        """slices txt from a line reference (string) to the next empty line, empty and start
         line not included in returned list"""

        try:
            start_idx = my_list.index(start)
        except ValueError:
            raise ValueError(f"Start line '{start}' not found in HTML content.")

        sliced_list = my_list[start_idx + 1:]
        try:
            end_idx = sliced_list.index('')
        except ValueError:
            raise ValueError("Could not find an empty line after the start reference.")
        section = sliced_list[: end_idx]
        return section

    @staticmethod
    def _parse_td(td: str) -> list[str]:
        """Parses an HTML string containing <td> tags and returns a list of their inner text values"""
        all_td_content = [td.text for td in BeautifulSoup(td, 'html.parser')('td')]
        return all_td_content

    @property
    def raw_html(self):
        return self._raw_html


# TODO: take into account timezones! currenty it's considering only UTC/GMT
#  if the broker uses another timezone every data gotten from the TraderMadeClient would awfully inaccurate
class TradeData:
    _HTML_DATE_SOURCE_FORMAT = "%Y.%m.%d %H:%M:%S"

    def __init__(self, trades_info: TxtParser):
        self.raw_operations = trades_info.get_operations_info()
        self._currency = trades_info.get_account_info()['currency']
        self._trades_raw = []
        self._balances_raw = []
        self._split_operations()
        self._create_trade_objects()
        self._create_balance_objects()
        self._insert_balance_type()
        self._insert_time_opened()
        self._update_base_and_quote()

        logger.info(f" {__name__} amount of traes {len(self.trades)} amount of balances {len(self.balances)}")

    def _insert_time_opened(self):
        """Assigns dt.timedelta value for opening and closing times in Trade.time_opened"""

        for item in self.trades:
            time_opened = item.close_time - item.open_time
            item.time_opened = time_opened

    def _create_balance_objects(self):
        """Creates a list of Balance objects using a parser functionality"""

        self._balance_objects = [
            obj for r in self._balances_raw
            if (obj := TradeData._parse_balance(r, self._HTML_DATE_SOURCE_FORMAT))
        ]

    def _create_trade_objects(self):
        """Creates a list of Trade objects using a parser functionality"""

        self._trade_objects = [
            obj for r in self._trades_raw
            if (obj := TradeData._parse_trade(r, self._HTML_DATE_SOURCE_FORMAT))
        ]

    def _split_operations(self):
        """separates balance and trading info from trades_info. trades are stored in self._trades
        and balances are stored in self._balances"""

        for row in self.raw_operations:
            if TradeData._is_trade(row):
                self._trades_raw.append(row)

            elif TradeData._is_balance(row):
                self._balances_raw.append(row)

    def _insert_balance_type(self):
        """assigns the 'withdrawal' or 'balance' to objects in 'self.balances.type'"""
        for item in self.balances:
            item.order_type = TradeData._get_balance_type(item.amount)

    @staticmethod
    def _parse_balance(row: list, date_format: str) -> Balance | None:
        """Returns Balance object from a row in MT4 format. Returns None if the row is malformed"""
        try:
            if len(row) > 4:
                return Balance(
                    order=int(row[0]),
                    date=dt.datetime.strptime(row[1], date_format),
                    amount=TradeData._balance_to_float(row[4])
                )
            else:
                logger.warning(f"Skipping malformed trade row (too few columns): {row}")
            return None
        except Exception as e:
            logger.warning(f"Failed to parse trade row: {row} | Error: {e}")
            return None

    def _update_base_and_quote(self):
        """Updates 'trade.quote' and 'trade.base' as it's initiated as an empty string.
        Returns 'None' if symbol is not a forex tradable"""

        for trade in self.trades:
            if len(trade.symbol) == 6:
                trade.base = trade.symbol[:3]
                trade.quote = trade.symbol[3:]

    @staticmethod
    def _parse_trade(row: list, date_format: str) -> Trade | None:
        """Returns a Trade object from a row in MT4 format. Returns None if the row is malformed."""

        try:
            if len(row) > 12:
                return Trade(
                    order=int(row[0]),
                    open_time=dt.datetime.strptime(row[1], date_format),
                    order_type=row[2],
                    volume=float(row[3]),
                    symbol=row[4].upper(),
                    open_price=float(row[5]),
                    sl=float(row[6]),
                    tp=float(row[7]),
                    close_time=dt.datetime.strptime(row[8], date_format),
                    close_price=float(row[9]),
                    commission=float(row[10]),
                    taxes=float(row[11]),
                    swap=float(row[12]),
                    profit=float(row[13]),
                )
            else:
                logger.warning(f"Skipping malformed trade row (too few columns): {row}")
                return None
        except Exception as e:
            logger.warning(f"Failed to parse trade row: {row} | Error: {e}")
            return None

    @staticmethod
    def _is_trade(row):
        """returns True if a list contains a trade's information"""

        return row[2].lower() in order_types if len(row) > 2 else False

    @staticmethod
    def _is_balance(row):
        """returns True if a list contains a balance's information"""

        return row[2].lower() == 'balance' if len(row) > 2 else False

    @staticmethod
    def _get_balance_type(amount: float) -> str:
        """return 'withdrawal' if amount < 0.
        returns 'deposit' if amount => 0"""
        if amount >= 0:
            return 'deposit'

        elif amount < 0:
            return 'withdrawal'

    @staticmethod
    def _balance_to_float(balance_amount: str):
        """returns a float from a str having blank spaces as separators.
        e.g. '10 000.00' -> 10000.0'"""
        no_spaces = balance_amount.replace(' ', '')
        try:
            return float(no_spaces)
        except ValueError:
            raise ValueError("Balance amount can't be converted to float")

    @property
    def trades(self):
        return self._trade_objects

    @property
    def balances(self):
        return self._balance_objects

    @property
    def currency(self):
        return self._currency

    @property
    def forex_trades(self):
        return [t for t in self.trades if t.base in PAIRS and t.quote in PAIRS]


class TraderMadeClient:
    _BASE_URL = 'https://marketdata.tradermade.com/api/v1/'
    _TIMESERIES_ENDPOINT = 'timeseries'
    _HISTORICAL_ENDPOINT = 'historical'
    _HOUR_HISTORICAL_ENDPOINT = 'hour_historical'
    _MINUTE_HISTORICAL_ENDPOINT = 'minute_historical'
    _TM_DATE_FORMAT_MINUTE = '%Y-%m-%d-%H:%M'
    _TM_DATE_FORMAT_DAILY = '%Y-%m-%d'

    def __init__(self, tm_api_key):
        self._API_KEY = tm_api_key
        self._set_api_key()

    def complete_trade_high_low(self, trades: list[Trade]):
        """Completes 'trades.high' and 'trades.low' from a list of trades. Uses tradermade api to complete it
        'trades.high' is the max value in between 'trade.open_time' and 'trade.close_time'
        'trades.low' is the min value in between 'trade.open_time' and 'trade.close_time'"""
        for trade in trades:
            try:
                df = self.patched_request(
                    endpoint='timeseries',
                    fields=['high', 'low'],
                    trade=trade
                )

                if df.empty:
                    logger.warning(f"No data for trade {trade.order}")
                    trade.high = max(trade.open_price, trade.close_price)
                    trade.low = min(trade.open_price, trade.close_price)
                    continue

                trade.high = max(df['high'].max(), trade.open_price, trade.close_price)
                trade.low = min(df['low'].min(), trade.open_price, trade.close_price)

            except Exception as e:
                logger.warning(f"Failed to fetch high/low for trade {trade.order}: {e}")

    def patched_request(self, endpoint: str, fields, **kwargs) -> pd.DataFrame:
        """Gets data of a trade from the Tradermade API. Tradermade API requests functions raises Keyvalue error
        when 'quotes' not in response.json(). this patched version accounts for that possibility.
        trade: a trade of type Trade;
        fields: any of ['open', 'close', 'high', 'low'];
        interval= one of ['daily', 'hourly', 'minute']"""

        params = self.build_params(endpoint=endpoint, **kwargs)
        data = TraderMadeClient._get_request(params, endpoint=endpoint)
        return TraderMadeClient._parse_response(data, fields=fields)

    def _build_historical_params(self, trade: Trade, time_unit: str = 'day') -> dict:
        """Create hour historical request parameters given:
         fields: any of ['open', 'close', 'high', 'low'];
         trade: a trade of type Trade;
         time_unit: one of ['minute', 'hour', 'day']"""

        interval_options = {
            'minute': TraderMadeClient._TM_DATE_FORMAT_MINUTE,
            'hour': TraderMadeClient._TM_DATE_FORMAT_MINUTE,
            'day': TraderMadeClient._TM_DATE_FORMAT_DAILY
        }

        return {
            'currency': trade.symbol,
            'date_time': dt.datetime.strftime(trade.open_time, interval_options[time_unit]),
            'api_key': self.api_key
        }

    def _build_timeseries_params(self, trade: Trade, interval: str = '', period: int = '') -> dict:
        """Create time series request parameters given:
         fields: any of ['open', 'close', 'high', 'low'];
        interval: one of ['daily', 'hourly', 'minute'];
        period: Daily Interval = 1
                Hourly interval, choices are - 1, 2, 4, 6, 8, 24
                Minute interval, choices are - 1, 5, 10, 15, 3"""

        if not interval:
            interval = TraderMadeClient._optimal_interval(trade)

        if not period:
            period = TraderMadeClient._get_optimal_period(trade.time_opened, interval)

        tm_start_correction = TraderMadeClient._start_date_correction(interval, trade.open_time, trade.close_time)

        params = {
            'currency': trade.symbol,
            'api_key': self.api_key,
            'start_date': dt.datetime.strftime(trade.open_time + tm_start_correction,
                                               TraderMadeClient._TM_DATE_FORMAT_MINUTE),
            'end_date': dt.datetime.strftime(trade.close_time, TraderMadeClient._TM_DATE_FORMAT_MINUTE),
            'interval': interval,
            'period': period,
            'format': 'split'
        }
        logger.info(f"{__name__} {__class__} api call parameters {params}")
        return params

    def build_params(self, endpoint: str, **kwargs) -> dict:
        """Build parameters dictionary for a given Tradermade endpoint.
        Expected endpoints: ['timeseries', 'historical', 'hour_historical', 'minute_historical'].
        Expected **kwargs:
        Trade: Trade of type Trade.
        interval: one of ['daily', 'hourly', 'minute'];
        period: Daily Interval = 1
                Hourly interval, choices are - 1, 2, 4, 6, 8, 24
                Minute interval, choices are - 1, 5, 10, 15; 30;
        fields = list type ['open', 'close', 'high', 'low']
        time_unit = one of ['day', 'hour', 'minute']"""

        if endpoint == 'timeseries':
            return self._build_timeseries_params(**kwargs)
        elif endpoint in ['historical', 'hour_historical', 'minute_historical']:
            return self._build_historical_params(**kwargs)

        else:
            raise ValueError(f"Wrong endpoint {endpoint} given.Expected endpoints: "
                             f"['timeseries', 'historical', 'hour_historical', 'minute_historical'] ")

    def _set_api_key(self):
        """Sets the RESTful API, runs on instantiation"""

        try:
            tm.set_rest_api_key(self.api_key)

        except Exception as e:
            logger.info(f"Exception while trying to set the restful API {e}")

    @staticmethod
    def _get_request(params: dict, endpoint: str) -> dict:
        """make a request to tradermade.
         Type must be any of the available functionalities: 'timeseries', 'historical',
         'minute_historical', 'hourly_historical"""

        request_url = TraderMadeClient._BASE_URL + endpoint
        try:
            return requests.get(request_url, params).json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"Bad request: {e}")
            return {}

    @staticmethod
    def _optimal_interval(trade: Trade) -> str:
        """Selects the correct, most optimal interval ('daily', 'hourly', 'minute') to get tm.time_series info
         for a given trade"""

        time_opened = trade.time_opened.total_seconds()
        day_in_seconds = 24 * 60 * 60
        less_than_year_old = TraderMadeClient._is_recent_than(trade.open_time, days=365)
        less_than_month_old = TraderMadeClient._is_recent_than(trade.open_time, days=29)

        interval = 'daily'
        if less_than_month_old:
            if time_opened < 2 * day_in_seconds:
                interval = 'minute'
            else:
                interval = 'hourly'

        elif less_than_year_old:
            if time_opened < 29 * day_in_seconds:
                interval = 'hourly'
        logger.info(f"{__name__} is less than month old: {less_than_month_old} less than_year_old {less_than_year_old}")
        return interval

    @staticmethod
    def _get_optimal_period(time_opened: dt.timedelta, interval: str) -> int:
        """Selects the largest possible period for a trade,
         as of not to get unnecessary heavy responses from the timeseries request"""

        thresholds = {
            'minute': [
                (60 * 12, 30),
                (60 * 6, 15),
                (60 * 2, 6),
                (30, 2),
            ],
            'hourly': [
                (60 * 24 * 15, 8),
                (60 * 24 * 8, 6),
                (60 * 24 * 4, 4),
                (60 * 24 * 2, 2)

            ],
            'daily': [
                (0, 1)
            ]}

        if interval in ['minute', 'hourly', 'daily']:
            for threshold, period in thresholds[interval]:
                if time_opened.total_seconds() / 60 > threshold:
                    return period
        else:
            logger.info(f'{__name__} {__class__} interval {interval} for'
                        f'must be one of ["minute", "hourly", "daily"]'
                        f'returned 1 to avoid crash, not optimal')
        return 1

    @staticmethod
    def _is_recent_than(date: dt.datetime, days: int) -> bool:
        """checks weather a date is older than 'days' days"""

        if isinstance(date, dt.datetime):
            how_old = dt.datetime.now() - date
            days = dt.timedelta(days=days)
            return how_old.total_seconds() < days.total_seconds()
        else:
            return False

    @staticmethod
    def _parse_response(data: dict, fields: list[str]) -> pd.DataFrame | dict:
        """Handles tradermade api request answer, returns data frame with [fields] columns if the call was correct.
         returns empty dataframe in any other case"""

        logger.info(f"{__name__} tradermade request keys: {data.keys()}")
        if "quotes" not in data:
            logger.info(f'quotes not in response {data}')
            return pd.DataFrame()

        df = pd.DataFrame(data["quotes"]["data"], columns=data["quotes"]["columns"])
        if fields:
            try:
                df = df[["date"] + fields]
            except KeyError as e:
                logger.warning(f"Some requested fields not found in data: {e}")
                df = pd.DataFrame()
            finally:
                logger.info(f"{__name__} dataframe from Tradermade\n {df.head()}")
                return df

    @staticmethod
    def _start_date_correction(interval: str, open_date: dt.datetime, close_date: dt.datetime) -> dt.timedelta:
        """Trader made won't get start_date data for daily intervals in some specific cases.
        This function fixes the malfunction, returning tm.timedelta(days=-1) to add it to date_start when needed"""

        if interval == 'daily':
            if open_date.hour < 17 or open_date.day == close_date.day:
                return dt.timedelta(days=-1)

        return dt.timedelta(seconds=0)

    @property
    def api_key(self):
        return self._API_KEY


if __name__ == '__main__':
    aux = TxtParser.from_filepath('statement.txt')
    operations_infonow = aux.get_operations_info()
    now = TradeData(aux)

    tm_client = TraderMadeClient(TM_API_KEY)

    one_months = datetime.timedelta(days=3)
    tm_client.complete_trade_high_low(now.trades)
    print(now.forex_trades)
    with open("./cached_trade_data.pkl", "wb") as f:
        pickle.dump(now, f)
