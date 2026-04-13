class TradingBotError(Exception):
    pass


class OrderError(TradingBotError):
    pass


class DuplicateOrderError(OrderError):
    pass


class InsufficientFundsError(OrderError):
    pass


class RiskLimitExceededError(TradingBotError):
    pass


class BrokerError(TradingBotError):
    pass


class BrokerConnectionError(BrokerError):
    pass


class MarketDataError(TradingBotError):
    pass


class StrategyError(TradingBotError):
    pass
