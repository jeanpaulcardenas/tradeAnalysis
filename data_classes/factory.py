from data_classes.mt4data import FileParser, TradeData, TraderMadeClient
from data_classes.statistics_m import Metrics
from config import _TM_API_KEY


def metrics_from_file(file_path: str) -> Metrics:
    """Create metrics object from a file. uses Parser, TradeData and TradermadeClient"""
    parsed = FileParser.from_filepath(file_path)
    trades_obj = TradeData(parsed)
    client_tm = TraderMadeClient(_TM_API_KEY)
    client_tm.complete_trade_high_low(trades_obj.trades)
    metrics = Metrics.from_trade_data(trades_obj)
    return metrics
