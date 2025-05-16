import datetime
from application.constants import *
from application.config import get_logger
from bs4 import BeautifulSoup
from dataclasses import dataclass
from datetime import datetime
import tradermade as tm
import requests
import pandas as pd
import logging
import base64
import re

logger = get_logger(__name__)
@dataclass
class Trade:
    order: int
    open_time: datetime
    type: str
    volume: float
    symbol: str
    open_price: float
    sl: float
    tp: float
    close_time: datetime
    close_price: float
    commission: float
    taxes: float
    swap: float
    profit: float
    high: float = 0
    low: float = 0


class TxtParser:
    _ABOVE_TRADES_REF_LINE = '   <td>Price</td><td>Commission</td><td>Taxes</td><td>Swap</td><td>Profit</td></tr>'
    _ABOVE_ACCT_REF_LINE = '<tr align=left>'

    def __init__(self, txt: str):
        """txt is the raw html string of the mt4 statement"""

        self._raw_html = txt
        self.my_html_list = self._create_html_list(self.raw_html)
        logger.info(f'TxtParser creation')

    def get_operations_info(self) -> list[list[str]]:
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
        logging.info(f'Sliced result from index {start_idx} to {end_idx}: {section}')
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
    def __init__(self, trades_info: list[list[str]]):
        self.raw_operations = trades_info
        self._trades = list()
        self._balances = list()

        self._split_operations()
        self._create_trade_objects()

        logging.info(f'trades info {self.trades} balance info {self.balances} and trade objects {self.trade_objects}')

    def _create_trade_objects(self):
        """Creates self.trade_objects attribute. This attribute represents a list of Trade objects
        from the list of trades contained in the trades_info instantiation argument"""

        self.trade_objects = [self._parse_trade(r) for r in self.trades]

    def _split_operations(self):
        """separates balance and trading info from trades_info. trades are stored in self._trades
        and balances are stored in self._balances"""

        for row in self.raw_operations:
            if self._is_trade(row):
                self._trades.append(row)

            elif self._is_balance(row):
                self._balances.append(row)

    @staticmethod
    def _is_trade(row):
        """returns True if a list contains a trade's information"""

        return row[2].lower() in {'buy', 'sell'} if len(row) > 2 else False

    @staticmethod
    def _is_balance(row):
        """returns True if a list contains a balance's information"""

        return row[2].lower() == 'balance' if len(row) > 2 else False

    @staticmethod
    def _parse_trade(row) -> Trade:
        return Trade(
            order=int(row[0]),
            open_time=datetime.strptime(row[1], "%Y.%m.%d %H:%M:%S"),
            type=row[2],
            volume=float(row[3]),
            symbol=row[4].upper(),
            open_price=float(row[5]),
            sl=float(row[6]),
            tp=float(row[7]),
            close_time=datetime.strptime(row[8], "%Y.%m.%d %H:%M:%S"),
            close_price=float(row[9]),
            commission=float(row[10]),
            taxes=float(row[11]),
            swap=float(row[12]),
            profit=float(row[13]),
        )

    @property
    def trades(self):
        return self._trades

    @property
    def balances(self):
        return self._balances





#
# class MtData:
#     def __init__(self, file: list[str], sql_data_length):
#         self.sql_data_length = sql_data_length
#         self._text = file
#         self._currency = self.get_currency()
#         self.history = self.get_history()
#         self.dict = self.get_trades_dict()
#         self.trades_made = len(self.dict['act'])
#         print(f'dict:\n{self.dict} \n\n {self.history} \n\n {self.get_balance_dict()}')
#
#     @property
#     def text(self):
#         return self._text
#
#     @staticmethod
#     def get_pair_name(pair):
#         """returns long-name pair from pair in the form of 6 letters characters e.g 'EURUSD'"""
#         try:
#             return f'{PAIRS[pair[:3]]} / {PAIRS[pair[3:]]}'
#
#         except KeyError:
#             return pair
#
#     @staticmethod
#     def tm_date_format(date: dt):
#         """formats date-time type to tm API required format 'YYYY-mm-dd-HH:MM"""
#         return date.strftime('%Y-%m-%d-%H:%M')
#
#     @staticmethod
#     def set_rest_api_key(key):
#         tm.set_rest_api_key(key)
#
#
#     @staticmethod
#     def parse_html_row(row):
#         soup = BeautifulSoup(row, 'html.parser')
#         td_text_list = [_.text for _ in soup.find_all('td')]
#         return td_text_list
#
#     @staticmethod
#     def is_trade(my_list):
#         """gets """
#
#
#     def get_currency_symbol(self):
#         if self._currency in CURRENCIES:
#             return CURRENCIES[self._currency]
#
#         else:
#             return ""
#
#     def get_history(self):
#         """Gets dictionary from statement.txt"""
#
#         data = get_raw_info()
#         list_of_trades = list()
#         list_of_balance = list()
#         for row in data:
#
#             soup = BeautifulSoup(row, 'html.parser')
#             td_text_list = [_.text for _ in soup.find_all('td')]
#             base = td_text_list[4][:3].upper()
#             cotizada = td_text_list[4][3:].upper()
#
#             if base in list(PAIRS.keys()) and cotizada in list(PAIRS.keys()):
#                 list_of_trades.append(td_text_list)
#
#             elif td_text_list[2] == 'balance':
#                 list_of_balance.append(td_text_list)
#
#         return {
#             'trades': list_of_trades,
#             'balances': list_of_balance
#         }
#
#     def get_trades_dict(self):
#
#         list_of_trades = self.history['trades']
#
#         return {
#             'act': [trade[4].upper() for trade in list_of_trades],
#             'vol': [float(trade[3]) for trade in list_of_trades],
#             'tip': [trade[2] for trade in list_of_trades],
#             'fi': [dt.datetime.strptime(trade[1], '%Y.%m.%d %H:%M:%S') for trade in list_of_trades],
#             'vi': [float(trade[5]) for trade in list_of_trades],
#             'ff': [dt.datetime.strptime(trade[8], '%Y.%m.%d %H:%M:%S') for trade in list_of_trades],
#             'vf': [float(trade[9]) for trade in list_of_trades],
#             'sl': [float(trade[6]) for trade in list_of_trades],
#             'tp': [float(trade[7]) for trade in list_of_trades],
#             'ing': [float(trade[-1]) for trade in list_of_trades],
#             'lnm': [self.get_pair_name(trade[4].upper()) for trade in list_of_trades],
#             'com': [float(trade[10]) for trade in list_of_trades],
#             'tax': [float(trade[11]) for trade in list_of_trades],
#             'swp': [float(trade[12]) for trade in list_of_trades]
#         }
#
#     def get_balance_dict(self):
#         my_balances = self.history['balances']
#         aux = {
#             'ing': [float(balance[-1].replace(" ", "")) for balance in my_balances],
#             'ff': [dt.datetime.strptime(balance[1], '%Y.%m.%d %H:%M:%S') for balance in my_balances],
#         }
#         aux['tip'] = ['DEPOSIT' if val >= 0 else 'WITHDRAWAL' for val in aux['ing']]
#
#         return aux
#
#     def get_api_data(self):
#         """get highs and lows from each trade. returns a list of dataframes (one for each trade)"""
#         self.set_rest_api_key(TM_API_KEY)
#         data = []
#         period = 1
#         for t in range(self.sql_data_length, self.trades_made):
#             start = self.dict['fi'][t]
#             end = self.dict['ff'][t]
#             print(start, type(start))
#             now = dt.datetime.now()
#             start_api = self.tm_date_format(start)
#             end_api = self.tm_date_format(end)
#
#             if start + dt.timedelta(days=1) > end and start + dt.timedelta(days=30) > now:
#                 interval = 'minute'
#                 print('minute')
#
#                 if start + dt.timedelta(hours=6) > end:
#                     period = 1
#                 else:
#                     period = 5
#
#             elif start + dt.timedelta(days=30) > end and start + dt.timedelta(days=360) > now:
#
#                 interval = 'hourly'
#                 print('hour')
#                 start_api = dt.datetime.strftime(start - dt.timedelta(hours=1), '%Y-%m-%d-%H:%M')
#
#                 if start + dt.timedelta(days=15) > end:
#                     period = 1
#                 else:
#                     period = 2
#
#             else:
#                 interval = "daily"
#                 logging.info(f'start date{start_api}')
#             print(self.dict['act'][t], start_api, end_api, interval, period)
#             r = tm.timeseries(
#                 currency='EURUSD',
#                 start='2025-02-05-12:20',
#                 end='2025-02-05-20:20',
#                 interval='hourly',
#                 period=1
#             )
#             print(r)
#             r = patched_timeseries(self.dict['act'], start=start_api, end=end_api, interval='daily', period=15)
#             print(r)
#
#             if r.empty:
#                 print('empty')
#
#                 if start + dt.timedelta(minutes=1) > end:
#                     interval = 'minute'
#
#                 elif start + dt.timedelta(hours=1) > end:
#                     interval = 'hourly'
#
#                 else:
#                     interval = 'daily'
#
#                 r = tm.historical(
#                     currency=self.dict['act'][t].lower(),
#                     date=end_api,
#                     interval=interval,
#                     fields=['high', 'low']
#
#                 )
#
#
#             data.append(r)
#
#
#         return data
# def patched_timeseries(currency, start, end, fields=None, interval='daily', period=15):
#     url = "https://marketdata.tradermade.com/api/v1/timeseries"
#     params = {
#         "currency": currency,
#         "api_key": TM_API_KEY,
#         "start_date": start,
#         "end_date": end,
#         "interval": interval,
#         "period": period,
#         "format": "split"
#     }
#     response = requests.get(url, params=params)
#
#     data = response.json()
#     if "quotes" not in data:
#         return data  # likely an error message
#     df = pd.DataFrame(data["quotes"]["data"], columns=data["quotes"]["columns"])
#     if fields:
#         return df[["date"] + fields]
#     return df
#
#
#
aux = TxtParser.from_filepath('statement.txt')
operations_infonow = aux.get_operations_info()
now = TradeData(operations_infonow)
logger.info(f'TradeData.trades {now.trade_objects}')
