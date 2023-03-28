from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
  from id_types import ServerID, UserID


class DailyFarmStatsDict(TypedDict):
  id: ServerID
  farmed: int
  daily_goal_reached: bool
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
  daily_goal_reached: bool = False
  contributors: dict[UserID, int] = {}

  def to_dict(self) -> DailyFarmStatsDict:
    return {
      "id": self.id,
      "farmed": self.farmed,
      "daily_goal_reached": self.daily_goal_reached,
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
  
  def set_daily_goal_reached(self, farm_id: ServerID):
    self.farms[farm_id]["daily_goal_reached"] = True
  
  def inc_shroom_count(self, farm_id: ServerID, user_id: UserID, amount: int = 1):
    self.total += amount

    farm_stat = self.get_farm_stats(farm_id) or DailyFarmStats(farm_id)
    farm_stat.farmed += amount
    if not farm_stat.daily_goal_reached:
      try:
        farm_stat.contributors[user_id] += amount
      except KeyError:
        farm_stat.contributors[user_id] = amount
    self.farms[farm_id] = farm_stat.to_dict()

    try:
      self.users[user_id] += amount
    except KeyError:
      self.users[user_id] = amount

  def to_dict(self) -> DailyStatsDict:
    return {
      "date": self.date,
      "total": self.total,
      "farms": self.farms,
      "users": self.users
    }