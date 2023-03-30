from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
  from farm import Farm
  from id_types import ServerID, UserID


class DailyFarmStatsDict(TypedDict):
  id: ServerID
  farmed: int
  daily_goal: int | None
  contributors: dict[UserID, int]

class DailyStatsDict(TypedDict):
  date: datetime
  total: int
  farms: dict[ServerID, DailyFarmStatsDict]
  users: dict[UserID, int]



@dataclass
class DailyFarmStats:
  id: ServerID
  farmed: int = 0
  daily_goal: int | None = None
  awarded_daily: bool = False # This is needed to ensure we don't award contributors twice
  contributors: dict[UserID, int] = {}

  @property
  def daily_goal_reached(self) -> bool:
    """If the daily goal has been reached.
    Returns `False` if there is no daily goal set
    """
    return (
      self.farmed >= self.daily_goal
      if self.daily_goal is not None
      else False
    )

  def to_dict(self) -> DailyFarmStatsDict:
    return {
      "id": self.id,
      "farmed": self.farmed,
      "daily_goal": self.daily_goal,
      "contributors": self.contributors
    }



@dataclass
class DailyStats:
  date: datetime = datetime.utcnow()
  total: int = 0
  farms: dict[ServerID, DailyFarmStatsDict] = {}
  users: dict[UserID, int] = {}

  @property
  def is_today(self) -> bool:
    return self.date.date() == date.today()

  def get_farm_stats(self, farm_id: ServerID) -> DailyFarmStats | None:
    farm = self.farms.get(farm_id)
    if farm is None:
      return None
    else:
      return DailyFarmStats(**farm)
    
  def get_user_farmed(self, user_id: UserID) -> int:
    return self.users.get(user_id, 0)
  
  def inc_shroom_count(self, farm: Farm, user_id: UserID, amount: int = 1) -> DailyFarmStats:
    self.total += amount

    farm_stats = self.get_farm_stats(farm._id) or DailyFarmStats(farm._id, daily_goal=farm.daily_goal)
    farm_stats.farmed += amount
    if not farm_stats.daily_goal_reached and farm_stats.daily_goal is not None:
      try:
        farm_stats.contributors[user_id] += amount
      except KeyError:
        farm_stats.contributors[user_id] = amount
    self.farms[farm._id] = farm_stats.to_dict()

    try:
      self.users[user_id] += amount
    except KeyError:
      self.users[user_id] = amount

    return farm_stats

  def to_dict(self) -> DailyStatsDict:
    return {
      "date": self.date,
      "total": self.total,
      "farms": self.farms,
      "users": self.users
    }