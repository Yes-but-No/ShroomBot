from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
  from id_types import ServerID, UserID, ChannelID


class FarmDict(TypedDict):
  """
  Describes the format of Farms in the `Farm` collection in the database
  These dictionaries can be inserted into the database with no issue
  """
  _id: ServerID
  total_farmed: int
  last_farmer: int | None
  farm_channel: int | None
  daily_goal: int | None
  updated: datetime | None



@dataclass
class Farm:
  _id: ServerID
  total_farmed: int = 0
  last_farmer: UserID | None = None
  farm_channel: ChannelID | None = None
  daily_goal: int | None = None
  updated: datetime = datetime.utcnow()

  def to_dict(self, include_id=True, include_time=True) -> FarmDict:
    d = {
      "total_farmed": self.total_farmed,
      "last_farmer": self.last_farmer,
      "farm_channel": self.farm_channel
    }
    if include_id:
      d["_id"] = self._id
    if include_time:
      d["updated"] = self.updated
    return d # type: ignore