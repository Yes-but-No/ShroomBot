from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict, TYPE_CHECKING

from ranks import RANKS

if TYPE_CHECKING:
  from id_types import UserID
  from ranks import Rank


class UserDict(TypedDict):
  _id: UserID
  joined: datetime
  farmed: int
  tokens: int
  rank_enum: int



@dataclass
class User:
  _id: UserID
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