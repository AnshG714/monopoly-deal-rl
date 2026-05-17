from __future__ import annotations

from collections.abc import Sequence


def combinations_of_indices(pool_size: int, choose: int) -> list[list[int]]:
    """Return every ``choose``-sized combination of ``range(pool_size)`` (increasing order)."""
    if choose < 0 or choose > pool_size:
        return []
    if choose == 0:
        return [[]]

    result: list[list[int]] = []
    current: list[int] = []

    def dfs(start: int) -> None:
        if len(current) == choose:
            result.append(current[:])
            return
        for idx in range(start, pool_size):
            current.append(idx)
            dfs(idx + 1)
            current.pop()

    dfs(0)
    return result


def combinations_greater_than_amount(
    values: Sequence[int],
    amount: int,
) -> list[list[int]]:
    """Index subsets whose ``values`` sum to at least ``amount``.

    Assets are tried in descending value order. Once a partial subset reaches
    ``amount``, it is recorded and no further assets are added on that branch,
    so voluntary overpayment supersets (e.g. 5M owed plus extra properties) are
    omitted. Necessary overpay (only a larger bill can cover the debt) is kept.
    """
    pool_size = len(values)
    if pool_size == 0:
        return [[]] if amount <= 0 else []

    order = sorted(range(pool_size), key=lambda i: values[i], reverse=True)
    result: list[list[int]] = []
    current: list[int] = []

    def dfs(position: int, total: int) -> None:
        if total >= amount:
            result.append(sorted(current))
            return
        if position >= pool_size:
            return

        idx = order[position]
        current.append(idx)
        dfs(position + 1, total + values[idx])
        current.pop()
        dfs(position + 1, total)

    dfs(0, 0)
    return result
