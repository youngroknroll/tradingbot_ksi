from decimal import Decimal

from app.domain.entities import Position


def calculate_new_position_on_buy(
    current: Position, filled_quantity: int, filled_price: Decimal
) -> Position:
    total_quantity = current.quantity + filled_quantity
    if total_quantity == 0:
        return Position(symbol=current.symbol)

    total_cost = current.average_price * current.quantity + filled_price * filled_quantity
    new_avg = total_cost / total_quantity

    return Position(
        symbol=current.symbol,
        quantity=total_quantity,
        average_price=new_avg,
        realized_pnl=current.realized_pnl,
    )


def calculate_new_position_on_sell(
    current: Position, filled_quantity: int, filled_price: Decimal
) -> Position:
    sell_qty = min(filled_quantity, current.quantity)
    realized = (filled_price - current.average_price) * sell_qty
    remaining = current.quantity - sell_qty

    return Position(
        symbol=current.symbol,
        quantity=remaining,
        average_price=current.average_price if remaining > 0 else Decimal("0"),
        realized_pnl=current.realized_pnl + realized,
    )


def calculate_unrealized_pnl(position: Position, current_price: Decimal) -> Decimal:
    if position.quantity <= 0:
        return Decimal("0")
    return (current_price - position.average_price) * position.quantity
