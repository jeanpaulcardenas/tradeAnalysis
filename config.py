from dotenv import load_dotenv
import plotly.express.colors as pxc
import logging
import os

DEBUG = False


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

        formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')

        file_handler = logging.FileHandler('./data/test.log', mode='w')
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


load_dotenv()

TM_API_KEY = os.getenv('TM_API_KEY')  # Tradermade API key

order_types = {'buy', 'sell'}

METRICS_DF_KEYS = ['order', 'symbol', 'order_type', 'volume', 'open_time', 'close_time', 'time_opened', 'open_price',
                   'close_price', 'high', 'low', 'sl', 'tp', 'profit', 'max_possible_gain', 'max_possible_loss',
                   'cum_profit', 'pips', 'commission', 'day_of_week', 'won_trade', 'taxes', 'swap', 'base', 'quote']
DOW = {
    0: 'monday',
    1: 'tuesday',
    2: 'wednesday',
    3: 'thursday',
    4: 'friday',
    5: 'saturday',
    6: 'sunday'
}

PLOTLY_GRAPH_TEMPLATE = 'plotly_dark'

PLOTLY_GRAPH_COLORS = pxc.qualitative.Light24[1:]
PLOTLY_GRAPH_COLORS.insert(1, pxc.qualitative.Light24[0])
SUNBURST_PATH = ['won_lost', 'order_type', 'day_of_week', 'symbol']

TIME_TYPE_OPTIONS = [
    {'label': 'Swing', 'value':  'days'},
    {'label': 'Intraday', 'value': 'hours'},
    {'label': 'Scalping', 'value': 'minutes'}
]
TIME_TYPE_DICT = {
    'days': {'period': 'days', 'denominator': 60*60*24, 'ceiling': 10**10},
    'hours': {'period': 'hours', 'denominator': 3600, 'ceiling': 60*60*24},
    'minutes': {'period': 'minutes', 'denominator': 60, 'ceiling': 15*60}
}

METRICS_DROPDOWN_OPTIONS = [
    {'label': 'Income (in acct currency)', 'value': False},
    {'label': 'PIPs', 'value': True}
]

BARS_DROPDOWN_OPTIONS = [
    {'label': 'Weekly', 'value': 'W'},
    {'label': 'Monthly', 'value': 'ME'},
    {'label': 'Annual', 'value': 'YE'}
]

INCOME_DROPDOWN_OPTIONS = [
    {'label': 'All', 'value': 0},
    {'label': 'Buy vs Sell', 'value': 'order_type'},
    {'label': 'Pairs', 'value': 'symbol'},
    {'label': 'Day of week', 'value': 'day_of_week'}
]

MONTHS = {
    '01': 'enero',
    '02': 'febrero',
    '03': 'marzo',
    '04': 'abril',
    '05': 'mayo',
    '06': 'junio',
    '07': 'julio',
    '08': 'agosto',
    '09': 'septiembre',
    '10': 'octubre',
    '11': 'noviembre',
    '12': 'diciembre',
}

CURRENCIES = {
    'EUR': '€',
    'USD': '$',
    'AUD': '$',
    'CAD': '$',
    'NZD': '$',
    'GBP': '£',
    'JPY': '¥',
}

PAIRS = {
    'AED': 'UAE Dirham',
    'AOA': 'Angolan Kwanza',
    'ARS': 'Argentine Peso',
    'AUD': 'Australian Dollar',
    'BGN': 'Bulgaria Lev',
    'BHD': 'Bahraini Dinar',
    'BRL': 'Brazilian Real',
    'CAD': 'Canadian Dollar',
    'CHF': 'Swiss Franc',
    'CLP': 'Chilean Peso',
    'CNY': 'Chinese Yuan onshore',
    'CNH': 'Chinese Yuan offshore',
    'COP': 'Colombian Peso',
    'CZK': 'Czech Koruna',
    'DKK': 'Danish Krone',
    'EUR': 'Euro',
    'GBP': 'British Pound Sterling',
    'HKD': 'Hong Kong Dollar',
    'HRK': 'Croatian Kuna',
    'HUF': 'Hungarian Forint',
    'IDR': 'Indonesian Rupiah',
    'ILS': 'Israeli New Sheqel',
    'INR': 'Indian Rupee',
    'ISK': 'Icelandic Krona',
    'JPY': 'Japanese Yen',
    'KRW': 'South Korean Won',
    'KWD': 'Kuwaiti Dinar',
    'MAD': 'Moroccan Dirham',
    'MXN': 'Mexican Peso',
    'MYR': 'Malaysian Ringgit',
    'NGN': 'Nigerean Naira',
    'NOK': 'Norwegian Krone',
    'NZD': 'New Zealand Dollar',
    'OMR': 'Omani Rial',
    'PEN': 'Peruvian Nuevo Sol',
    'PHP': 'Philippine Peso',
    'PLN': 'Polish Zloty',
    'RON': 'Romanian Leu',
    'RUB': 'Russian Ruble',
    'SAR': 'Saudi Arabian Riyal',
    'SEK': 'Swedish Krona',
    'SGD': 'Singapore Dollar',
    'THB': 'Thai Baht',
    'TRY': 'Turkish Lira',
    'TWD': 'Taiwanese Dollar',
    'USD': 'US Dollar',
    'VND': 'Vietnamese Dong',
    'XAG': 'Silver (troy ounce)',
    'XAU': 'Gold (troy ounce)',
    'XPD': 'Palladium',
    'XPT': 'Platinum',
    'ZAR': 'South African Rand'
}

COLORS = {
    'blue': 'rgb(0, 80, 250)',
    'red': 'rgb(250, 0, 0)',
    'white': 'rgb(255, 255, 255)',
    'green': 'rgb(0, 250, 0)',
    'yellow': 'rgb(255, 255, 10)',
    'purple': 'rgb(110, 0, 255)',
    'orange': 'rgb(220, 125, 15)',
    'dark_red': 'rgb(120, 30, 30)',
    'lightblue': 'rgb(45, 250, 250)',
    'pink': 'rgb(250, 90, 255)',
    'translucent_grey': 'rgba(120, 120, 120, 0.5)',
}

COLUMN_USED = {
    'All': None,
    'Buy vs Sell': 'order_type',
    'Pairs': 'symbol',
    'Day of week': 'day_of_week',
}
