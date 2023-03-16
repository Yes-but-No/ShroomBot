from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict


class FarmDict(TypedDict):
  """
  Describes the format of Farms in the `Farm` collection in the database
  These dictionaries can be inserted into the database with no issue
  """
  _id: int
  total_farmed: int
  last_farmer: int | None
  farm_channel: int | None
  daily_goal: int | None
  updated: datetime | None



@dataclass
class Farm:
  _id: int
  farmed_today: int = 0
  total_farmed: int = 0
  last_farmer: int | None = None
  farm_channel: int | None = None
  daily_goal: int | None = None
  updated: datetime  = datetime.utcnow()

  @property
  def daily_goal_reached(self) -> bool:
    """If the daily goal has been reached.
    Returns `False` if there is no daily goal set
    """
    return (
      self.farmed_today >= self.daily_goal
      if self.daily_goal is not None
      else False
    )

  def to_dict(self, include_id=True, include_time=True) -> FarmDict:
    d = {
      "farmed_today": self.farmed_today,
      "total_farmed": self.total_farmed,
      "last_farmer": self.last_farmer,
      "farm_channel": self.farm_channel
    }
    if include_id:
      d["_id"] = self._id
    if include_time:
      d["updated"] = self.updated
    return d