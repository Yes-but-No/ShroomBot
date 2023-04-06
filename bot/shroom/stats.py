from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import TYPE_CHECKING, TypedDict

from bson import ObjectId

from bot.utils import str_key_to_int, int_key_to_str

if TYPE_CHECKING:
  from shroom.farm import Farm

class DailyFarmStatsDict(TypedDict):
  id: int
  farmed: int
  daily_goal: int | None
  awarded_daily: bool
  contributors: dict[str, int]

class DailyStatsDict(TypedDict):
  date: datetime
  total: int
  farms: dict[str, DailyFarmStatsDict]
  users: dict[str, int]



@dataclass
class DailyFarmStats:
  id: int
  farmed: int = 0
  daily_goal: int | None = None
  awarded_daily: bool = False # This is needed to ensure we don't award contributors twice
  contributors: dict[int, int] = field(default_factory=dict)

  @classmethod
  def from_db(cls, d: DailyFarmStatsDict):
    return cls(
      id=d["id"],
      farmed=d["farmed"],
      daily_goal=d["daily_goal"],
      awarded_daily=d["awarded_daily"],
      contributors=str_key_to_int(d["contributors"])
    )

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
      "awarded_daily": self.awarded_daily,
      "contributors": int_key_to_str(self.contributors)
    }



@dataclass
class DailyStats:
  date: datetime = datetime.utcnow()
  total: int = 0
  farms: dict[int, DailyFarmStatsDict] = field(default_factory=dict)
  users: dict[int, int] = field(default_factory=dict)
  _id: ObjectId | None = None

  @classmethod
  def from_db(cls, d: DailyStatsDict):
    return cls(
      date=d["date"],
      total=d["total"],
      farms=str_key_to_int(d["farms"]),
      users=str_key_to_int(d["users"]),
      _id=d.get("_id")
    )

  @property
  def is_today(self) -> bool:
    return self.date.date() == date.today()

  def get_farm_stats(self, farm_id: int) -> DailyFarmStats | None:
    farm = self.farms.get(farm_id)
    if farm is None:
      return None
    else:
      return DailyFarmStats.from_db(farm)
    
  def save_farm_stats(self, farm_stats: DailyFarmStats):
    self.farms[farm_stats.id] = farm_stats.to_dict()
    
  def get_user_farmed(self, user_id: int) -> int:
    return self.users.get(user_id, 0)
  
  def inc_shroom_count(self, farm: Farm, user_id: int, amount: int = 1) -> DailyFarmStats:
    self.total += amount

    farm_stats = self.get_farm_stats(farm._id) or DailyFarmStats(farm._id, daily_goal=farm.daily_goal)
    if not farm_stats.daily_goal_reached and farm_stats.daily_goal is not None:
      amt = min(
        farm_stats.daily_goal-farm_stats.farmed,
        amount
      )
      try:
        farm_stats.contributors[user_id] += amt
      except KeyError:
        farm_stats.contributors[user_id] = amt
    farm_stats.farmed += amount
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
      "farms": int_key_to_str(self.farms),
      "users": int_key_to_str(self.users)
    }