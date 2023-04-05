from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Self, TypedDict

from bot.shroom.ranks import RANKS

if TYPE_CHECKING:
  from shroom.ranks import Rank


class UserDict(TypedDict):
  _id: int
  joined: datetime
  farmed: int
  tokens: int
  rank_enum: int



@dataclass
class User:
  _id: int
  joined: datetime = datetime.utcnow()
  farmed: int = 0
  tokens: int = 0
  rank_enum: int = 0

  @property
  def rank(self) -> Rank:
    return RANKS[self.rank_enum]
  
  @rank.setter
  def rank(self, value: Rank):
    self.rank_enum = RANKS.index(value)

  @property
  def next_rank(self) -> Rank | None:
    if self.rank_enum == len(RANKS) - 1:
      return None
    else:
      return RANKS[self.rank_enum+1]
    
  @property
  def ranked_up(self) -> bool:
    if self.next_rank is None:
      return False
    else:
      return self.farmed >= self.next_rank.requirement
    
  def update_rank(self) -> Self:
    """Updates user's rank to their highest possible rank,
    which may be higher or lower than the user's current rank
    """
    if self.farmed < self.rank.requirement:
      while self.farmed < self.rank.requirement:
        if self.rank_enum == 0:
          break
        self.rank_enum -= 1
    else:
      while self.ranked_up:
        self.rank_enum += 1
    return self
    
  def to_dict(self, include_id=True) -> UserDict:
    d = {
      "joined": self.joined,
      "farmed": self.farmed,
      "tokens": self.tokens,
      "rank_enum": self.rank_enum
    }
    if include_id:
      d["_id"] = self._id
    return d # type: ignore