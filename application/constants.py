import os
from dotenv import load_dotenv
load_dotenv()

TM_API_KEY = os.getenv('TM_API_KEY')  # Tradermade API key

order_types = {'buy', 'sell'}

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
    'AED':	'UAE Dirham',
    'AOA':	'Angolan Kwanza',
    'ARS':	'Argentine Peso',
    'AUD':	'Australian Dollar',
    'BGN':	'Bulgaria Lev',
    'BHD':	'Bahraini Dinar',
    'BRL':	'Brazilian Real',
    'CAD':	'Canadian Dollar',
    'CHF':	'Swiss Franc',
    'CLP':  'Chilean Peso',
    'CNY':	'Chinese Yuan onshore',
    'CNH':	'Chinese Yuan offshore',
    'COP':	'Colombian Peso',
    'CZK':	'Czech Koruna',
    'DKK':	'Danish Krone',
    'EUR':	'Euro',
    'GBP':	'British Pound Sterling',
    'HKD':	'Hong Kong Dollar',
    'HRK':  'Croatian Kuna',
    'HUF':	'Hungarian Forint',
    'IDR':	'Indonesian Rupiah',
    'ILS':	'Israeli New Sheqel',
    'INR':	'Indian Rupee',
    'ISK':	'Icelandic Krona',
    'JPY':	'Japanese Yen',
    'KRW':	'South Korean Won',
    'KWD':	'Kuwaiti Dinar',
    'MAD':	'Moroccan Dirham',
    'MXN':	'Mexican Peso',
    'MYR':	'Malaysian Ringgit',
    'NGN':	'Nigerean Naira',
    'NOK':	'Norwegian Krone',
    'NZD':	'New Zealand Dollar',
    'OMR':	'Omani Rial',
    'PEN':	'Peruvian Nuevo Sol',
    'PHP':	'Philippine Peso',
    'PLN':	'Polish Zloty',
    'RON':	'Romanian Leu',
    'RUB':	'Russian Ruble',
    'SAR':	'Saudi Arabian Riyal',
    'SEK':	'Swedish Krona',
    'SGD':	'Singapore Dollar',
    'THB':	'Thai Baht',
    'TRY':	'Turkish Lira',
    'TWD':	'Taiwanese Dollar',
    'USD':	'US Dollar',
    'VND':	'Vietnamese Dong',
    'XAG':	'Silver (troy ounce)',
    'XAU':	'Gold (troy ounce)',
    'XPD':	'Palladium',
    'XPT':	'Platinum',
    'ZAR':	'South African Rand'
}


COLORS = {
    'blue': 'rgb(0,80,250)',
    'red': 'rgb(250, 0, 0)',
    'white': 'rgb(255, 255, 255)',
    'green': 'rgb(0, 250, 0)',
    'yellow': 'rgb(255,255,10)',
    'purple': 'rgb(110, 0, 255)',
    'orange': 'rgb(220,125,15)',
    'dark_red': 'rgb(120,30,30)',
    'lightblue': 'rgb(45,250,250)',
    'pink': 'rgb(250,90,255)'
}

COLUMN_USED = {
    'All': None,
    'Buy vs Sell': 'order_types',
    'Pair': 'symbol',
    'Day of week': 'day_of_week',
}

