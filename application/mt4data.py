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

logger = get_logger(__name__)


@dataclass
class Trade:
    order: int
    open_time: dt.datetime
    type: str
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


@dataclass
class Balance:
    order: int
    date: datetime
    amount: float
    type: str = ''


class TxtParser:
    _ABOVE_TRADES_REF_LINE = '   <td>Price</td><td>Commission</td><td>Taxes</td><td>Swap</td><td>Profit</td></tr>'
    _ABOVE_ACCT_REF_LINE = '<tr align=left>'

    def __init__(self, txt: str):
        """txt is the raw html string of the mt4 statement"""

        self._raw_html = txt
        self.my_html_list = self._create_html_list(self.raw_html)
        logger.info(f'TxtParser creation')

    def get_operations_info(self) -> list[list[str]]:
        """returns a list with the meaningful data of the trades and balances of the MT4 operations report"""

        operations_raw = self._extract_section_from_html_list(
            my_list=self.my_html_list,
            start=self._ABOVE_TRADES_REF_LINE,
        )
        operations_info = list()
        for line in operations_raw:
            td_content = self.parse_td(line)
            operations_info.append(td_content)
        return operations_info

    def get_account_info(self) -> dict:
        """returns number Account, Name, Currency and Leverage from MT4 report"""

        acct_info_raw = self._extract_section_from_html_list(
            my_list=self.my_html_list,
            start=self._ABOVE_ACCT_REF_LINE,
        )
        acct_info = dict()
        for line in acct_info_raw:
            td_content = self.parse_td(line)
            values = re.split(r': ', td_content[0])

            try:
                acct_info[values[0]] = values[1]
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
    def parse_td(td: str) -> list[str]:
        """Parses an HTML string containing <td> tags and returns a list of their inner text values"""
        all_td_content = [td.text for td in BeautifulSoup(td, 'html.parser')('td')]
        return all_td_content

    @property
    def raw_html(self):
        return self._raw_html


class TradeData:
    _HTML_DATE_SOURCE_FORMAT = "%Y.%m.%d %H:%M:%S"

    def __init__(self, trades_info: list[list[str]]):
        self.raw_operations = trades_info
        self._trades_raw = []
        self._balances_raw = []

        self._split_operations()
        self._create_trade_objects()
        self._create_balance_objects()
        self._insert_balance_type()
        self._insert_time_opened()

        logger.info(f' {__name__}trades info {self.trades[0]} balance info {len(self.balances)}')

    def _insert_time_opened(self):
        """Assigns dt.timedelta value for opening and closing times in Trade.time_opened"""

        for item in self.trades:
            time_opened = item.close_time - item.open_time
            item.time_opened = time_opened

    def _create_balance_objects(self):
        """Creates a list of Balance objects using a parser functionality"""

        self._balance_objects = [
            obj for r in self._balances_raw
            if (obj := self._parse_balance(r, self._HTML_DATE_SOURCE_FORMAT))
        ]

    def _create_trade_objects(self):
        """Creates a list of Trade objects using a parser functionality"""

        self._trade_objects = [
            obj for r in self._trades_raw
            if (obj := self._parse_trade(r, self._HTML_DATE_SOURCE_FORMAT))
        ]

    def _split_operations(self):
        """separates balance and trading info from trades_info. trades are stored in self._trades
        and balances are stored in self._balances"""

        for row in self.raw_operations:
            if self._is_trade(row):
                self._trades_raw.append(row)

            elif self._is_balance(row):
                self._balances_raw.append(row)

    def _insert_balance_type(self):
        """assigns the 'withdrawal' or 'balance' to objects in 'self.balances.type'"""
        for item in self.balances:
            item.type = self._get_balance_type(item.amount)

    def _parse_balance(self, row: list, date_format: str) -> Balance | None:
        """Returns Balance object from a row in MT4 format. Returns None if the row is malformed"""
        try:
            if len(row) > 4:
                return Balance(
                    order=int(row[0]),
                    date=dt.datetime.strptime(row[1], date_format),
                    amount=self._balance_to_float(row[4])
                )
            else:
                logger.warning(f"Skipping malformed trade row (too few columns): {row}")
            return None
        except Exception as e:
            logger.warning(f"Failed to parse trade row: {row} | Error: {e}")
            return None

    @staticmethod
    def _parse_trade(row: list, date_format: str) -> Trade | None:
        """Returns a Trade object from a row in MT4 format. Returns None if the row is malformed."""

        try:
            if len(row) > 12:
                return Trade(
                    order=int(row[0]),
                    open_time=dt.datetime.strptime(row[1], date_format),
                    type=row[2],
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

        return row[2].lower() in {'buy', 'sell'} if len(row) > 2 else False

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


class TraderMadeClient:
    _BASE_URL = 'https://marketdata.tradermade.com/api/v1/'
    _TIMESERIES_ENDPOINT = 'timeseries'
    _HISTORICAL_ENDPOINT = 'historical'
    _HOUR_HISTORICAL_ENDPOINT = 'hour_historical'
    _MINUTE_HISTORICAL_ENDPOINT = 'minute_historical'
    _TM_DATE_FORMAT_MINUTE = '%Y-%m-%d-%H:%M'
    _TM_DATE_FORMAT_DAILY = '%Y-%m-%d'

    def __init__(self, tm_api_key):
        self._API_KEI = tm_api_key
        self._set_api_key()

    def _build_historical_params(self, trade: Trade, time_unit: str = 'day') -> dict:
        """Create hour historical request parameters given:
         fields: any of ['open', 'close', 'high', 'low'];
         trade: a trade of type Trade;
         time_unit: one of ['minute', 'hour', 'day']"""

        interval_options = {
            'minute': self._TM_DATE_FORMAT_MINUTE,
            'hour': self._TM_DATE_FORMAT_MINUTE,
            'day': self._TM_DATE_FORMAT_DAILY
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
            interval = self._optimal_interval(trade)

        if not period:
            period = self._get_optimal_period(trade.time_opened, interval)

        tm_start_correction = self._start_date_correction(interval, trade.open_time, trade.close_time)

        params = {
            'currency': trade.symbol,
            'api_key': self.api_key,
            'start_date': dt.datetime.strftime(trade.open_time + tm_start_correction, self._TM_DATE_FORMAT_MINUTE),
            'end_date': dt.datetime.strftime(trade.close_time, self._TM_DATE_FORMAT_MINUTE),
            'interval': interval,
            'period': period,
            'format': 'split'
        }
        logger.info(f'{__name__} {__class__} api call parameters {params}')
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

    def _get_request(self, params: dict, endpoint: str) -> dict:
        """make a request to tradermade.
         Type must be any of the available functionalities: 'timeseries', 'historical',
         'minute_historical', 'hourly_historical"""

        request_url = self._BASE_URL + endpoint
        try:
            return requests.get(request_url, params).json()
        except requests.exceptions.RequestException as e:
            logger.warning(f'Bad request: {e}')
            return {}

    def patched_request(self, endpoint: str, fields, **kwargs) -> pd.DataFrame:
        """Gets data of a trade from the Tradermade API. Tradermade API requests functions raises Keyvalue error
        when 'quotes' not in response.json(). this patched version accounts for that possibility.
        trade: a trade of type Trade;
        fields: any of ['open', 'close', 'high', 'low'];
        interval= one of ['daily', 'hourly', 'minute']"""

        params = self.build_params(endpoint=endpoint, **kwargs)
        data = self._get_request(params, endpoint=endpoint)
        return self._parse_response(data, fields=fields)

    def _set_api_key(self):
        """Sets the RESTful API, runs on instantiation"""

        try:
            tm.set_rest_api_key(self.api_key)

        except Exception as e:
            logger.info(f'Exception while trying to set the restful API {e}')

    def _optimal_interval(self, trade: Trade) -> str:
        """Selects the correct, most optimal interval ('daily', 'hourly', 'minute') to get tm.time_series info
         for a given trade"""

        time_opened = trade.time_opened.total_seconds()
        day_in_seconds = 24 * 60 * 60
        less_than_year_old = self._is_recent_than(trade.open_time, days=365)
        less_than_month_old = self._is_recent_than(trade.open_time, days=29)

        interval = 'daily'
        if less_than_month_old:
            if time_opened < 2 * day_in_seconds:
                interval = 'minute'
            else:
                interval = 'hourly'

        elif less_than_year_old:
            if time_opened < 29 * day_in_seconds:
                interval = 'hourly'
        logger.info(f'{__name__} is less than month old: {less_than_month_old} less than_year_old {less_than_year_old}')
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

        logger.info(f'{__name__} tradermade request response: {data}')
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
                logger.info(f'{__name__} dataframe from Tradermade\n {df.head()}')
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
        return self._API_KEI


aux = TxtParser.from_filepath('statement.txt')
operations_infonow = aux.get_operations_info()
now = TradeData(operations_infonow)
logger.info(f'TradeData.trades {len(now.trades)} \n\nTradeData.balances {len(now.balances)}')

tm_client = TraderMadeClient(TM_API_KEY)

one_months = datetime.timedelta(days=3)
print(dt.datetime.now())
df = tm_client.patched_request(endpoint='timeseries', fields=['high', 'low'], trade=now.trades[0])
print(df.info())
