from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class BacktestMetrics:
    total_return: float
    total_trades: int
    win_count: int
    loss_count: int
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float

    def summary(self) -> str:
        return (
            f"=== Backtest Results ===\n"
            f"Total Return: {self.total_return:+.2f}%\n"
            f"Total Trades: {self.total_trades}\n"
            f"Win/Loss: {self.win_count}/{self.loss_count}\n"
            f"Win Rate: {self.win_rate:.1f}%\n"
            f"Max Drawdown: {self.max_drawdown:.2f}%\n"
            f"Sharpe Ratio: {self.sharpe_ratio:.2f}\n"
            f"Profit Factor: {self.profit_factor:.2f}\n"
        )


def calculate_metrics(
    equity_curve: list[float], trade_pnls: list[float]
) -> BacktestMetrics:
    if not equity_curve or len(equity_curve) < 2:
        return BacktestMetrics(
            total_return=0, total_trades=0, win_count=0, loss_count=0,
            win_rate=0, max_drawdown=0, sharpe_ratio=0, profit_factor=0,
        )

    total_return = (equity_curve[-1] / equity_curve[0] - 1) * 100

    wins = [p for p in trade_pnls if p > 0]
    losses = [p for p in trade_pnls if p < 0]
    win_count = len(wins)
    loss_count = len(losses)
    total_trades = len(trade_pnls)
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0

    peak = equity_curve[0]
    max_dd = 0.0
    for val in equity_curve:
        if val > peak:
            peak = val
        dd = (peak - val) / peak * 100
        if dd > max_dd:
            max_dd = dd

    returns = np.diff(equity_curve) / equity_curve[:-1]
    sharpe = 0.0
    if len(returns) > 1 and np.std(returns) > 0:
        sharpe = float(np.mean(returns) / np.std(returns) * np.sqrt(252))

    gross_profit = sum(wins) if wins else 0
    gross_loss = abs(sum(losses)) if losses else 1
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

    return BacktestMetrics(
        total_return=total_return,
        total_trades=total_trades,
        win_count=win_count,
        loss_count=loss_count,
        win_rate=win_rate,
        max_drawdown=max_dd,
        sharpe_ratio=sharpe,
        profit_factor=profit_factor,
    )
