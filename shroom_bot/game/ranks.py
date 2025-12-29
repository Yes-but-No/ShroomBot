from __future__ import annotations

from attrs import define


@define
class Rank:
    name: str
    requirement: int


RANKS = (
    Rank("Shroom Forager", 0),
    Rank("Fungi Farmer", 50),
    Rank("Truffle Hunter", 100),
    Rank("Mycology Enthusiast", 250),
    Rank("Fungi Apprentice", 500),
    Rank("Truffle Collector", 1000),
    Rank("Shroom Maestro", 2500),
    Rank("Truffle Connoisseur", 5000),
    Rank("Fungi Master", 10000),
    Rank("Mycologist", 25000),
    Rank("Shroom Baron", 50000),
    Rank("Truffle Monarch", 100000),
    Rank("Fungi Overlord", 250000),
    Rank("Mycology Mogul", 500000),
    Rank("Shroom Deity", 1000000),
)


@define
class RankInfo:
    current_rank: Rank
    next_rank: Rank | None = None


def get_rank_info(lifetime_farmed: int) -> RankInfo:
    """Get the current and next rank based on lifetime farmed shrooms."""
    current_rank = RANKS[0]
    next_rank = None

    for rank in RANKS:
        if lifetime_farmed >= rank.requirement:
            current_rank = rank
        else:
            next_rank = rank
            break

    return RankInfo(current_rank=current_rank, next_rank=next_rank)
