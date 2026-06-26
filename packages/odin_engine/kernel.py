import numpy as np
from numba import njit


@njit
def _evaluate_condition(left: float, right: float, op_code: int) -> bool:
    if np.isnan(left) or np.isnan(right):
        return False
    if op_code == 0:
        return left == right
    if op_code == 1:
        return left > right
    if op_code == 2:
        return left < right
    if op_code == 3:
        return left >= right
    if op_code == 4:
        return left <= right
    return False


@njit
def run_backtest_kernel(
    left_values: np.ndarray,
    right_values: np.ndarray,
    op_codes: np.ndarray,
    close_prices: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = close_prices.shape[0]
    entries = np.zeros(n, dtype=np.bool_)
    exits = np.zeros(n, dtype=np.bool_)
    positions = np.zeros(n, dtype=np.int8)

    in_position = False
    entry_price = 0.0

    for i in range(1, n):
        signal = True
        for j in range(op_codes.shape[0]):
            if not _evaluate_condition(left_values[j, i], right_values[j, i], op_codes[j]):
                signal = False
                break

        if not in_position and signal:
            entries[i] = True
            in_position = True
            entry_price = close_prices[i]
            positions[i] = 1
        elif in_position:
            pnl_pct = (close_prices[i] - entry_price) / entry_price * 100.0
            if pnl_pct <= -1.0 or pnl_pct >= 2.0 or (not signal):
                exits[i] = True
                in_position = False
                positions[i] = 0
            else:
                positions[i] = 1

    return entries, exits, positions
