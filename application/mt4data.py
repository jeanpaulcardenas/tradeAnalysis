import re
from application.constants import *
from bs4 import BeautifulSoup


class MtData:
    def __init__(self, file: list[str]):
        self._text = file
        self._currency = self.get_currency()
        self.history = self.get_history()

    @property
    def text(self):
        return self._text

    def get_currency(self):
        reference = self.text.index("<tr align=left>")
        line = self.text[reference + 3]
        currency = re.split(r'Currency: |</b', line)[1]  # splits the line in 3, the middle object is the currency string

        return currency

    def get_currency_symbol(self):
        if self._currency in CURRENCIES:
            return CURRENCIES[self._currency]

        else:
            return ""

    def get_history(self):
        """Gets dictionary from statement.txt"""
        def get_raw_info():
            reference = \
                self.text.index('   <td>Price</td><td>Commission</td><td>Taxes</td><td>Swap</td><td>Profit</td></tr>')
            data = self.text[reference + 1:]
            index = data.index("")
            data = data[:index]
            return data

        data = get_raw_info()
        print(f'{data}\n\n')
        list_of_trades = list()
        list_of_balance = list()
        for row in data:

            soup = BeautifulSoup(row, 'html.parser')
            td_text_list = [_.text for _ in soup.find_all('td')]
            base = td_text_list[4][:3].upper()
            cotizada = td_text_list[4][3:].upper()

            if base in list(PAIRS.keys()) and cotizada in list(PAIRS.keys()):
                list_of_trades.append(td_text_list)

            elif td_text_list[2] == 'balance':
                list_of_balance.append(td_text_list)

        return {
            'trades': list_of_trades,
            'balances': list_of_balance
        }
