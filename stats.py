from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from typing import TypedDict, TYPE_CHECKING

if TYPE_CHECKING:
  from id_types import UserID, ServerID


class DailyFarmStatsDict(TypedDict):
  id: ServerID
  farmed: int
  contributors: dict[UserID, int] # User ID : Amount contributed to daily goal

@dataclass
class DailyFarmStats:
  id: ServerID
  farmed: int = 0
  contributors: dict[UserID, int] = {}

  def to_dict(self) -> DailyFarmStatsDict:
    return {
      "id": self.id,
      "farmed": self.farmed,
      "contributors": self.contributors
    }



@dataclass
class DailyStats:
  date: datetime
  total: int
  farms: dict[ServerID, DailyFarmStatsDict]
  users: dict[UserID, int]