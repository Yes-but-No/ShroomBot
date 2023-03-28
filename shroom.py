from __future__ import annotations
from collections import Counter
from operator import itemgetter

from typing import TYPE_CHECKING

from motor import motor_asyncio

from farm import Farm
from stats import DailyStats
from user import User

if TYPE_CHECKING:
  from id_types import ServerID, UserID, ChannelID
  from stats import DailyStatsDict, DailyFarmStatsDict


class ShroomFarm:
  def __init__(self, url: str = "localhost"):
    self.db_url = url
    self._db_client = motor_asyncio.AsyncIOMotorClient(url)
    self.shroom_db: motor_asyncio.AsyncIOMotorDatabase = self._db_client["ShroomDB"]

    self.farm_db: motor_asyncio.AsyncIOMotorCollection = self.shroom_db["Farm"]
    self.user_db: motor_asyncio.AsyncIOMotorCollection = self.shroom_db["Users"]
    self.stats_db: motor_asyncio.AsyncIOMotorCollection = self.shroom_db["Stats"]

    self.farms: dict[ServerID, Farm] = {}
    self.daily_stats: DailyStats = DailyStats()

  ##################################
  ### Server Collection Operations
  ##################################

  async def load_farms(self): # since all database lookup calls are async, we cant do it in __init__
    async for farm in self.farm_db.find({}):
      self.farms[farm["_id"]] = Farm(**farm)

  async def save_farm(self, farm: Farm) -> bool:
    result = await self.farm_db.update_one(
      {
        "_id": farm._id
      },
      {
        "$set": farm.to_dict(include_id=False, include_time=False),
        "$currentDate": {"updated": True}
      }
    )
    return result.modified_count == 1

  def get_farm(self, farm_id: int) -> Farm | None:
    return self.farms.get(farm_id)

  async def create_farm(self, server_id: ServerID, channel: ChannelID | None = None):
    if self.get_farm(server_id) is not None:
      raise ValueError(f"farm with ID `{server_id}` already exists")
    farm = Farm(server_id, farm_channel=channel)
    self.farms[server_id] = farm
    await self.farm_db.insert_one(farm.to_dict())

  async def set_farm_channel(self, farm_id: ServerID, channel_id: ChannelID):
    farm = self.get_farm(farm_id)
    if farm is None:
      raise ValueError(f"server with ID `{farm_id}` does not exist")
    farm.farm_channel = channel_id
    await self.save_farm(farm)
  
  async def reset_daily_count(self):
    for farm in self.farms.values():
      farm.farmed_today = 0
    await self.farm_db.update_many({}, {"$set": {"farmed_today": 0}})

  ################################
  ### User Collection Operations
  ################################

  async def get_user(self, user_id: UserID) -> User | None:
    return User(**await self.user_db.find_one({"_id": user_id}))

  async def create_user(self, user_id: UserID):
    if await self.get_user(user_id) is not None:
      raise ValueError(f"user with ID `{user_id}` already exists")
    await self.user_db.insert_one(User(user_id).to_dict())

  async def save_user(self, user: User) -> bool:
    result = await self.farm_db.update_one(
      {
        "_id": user._id
      },
      {
        "$set": user.to_dict(include_id=False)
      }
    )
    return result.modified_count == 1
  
  async def inc_user_farmed(self, user_id: UserID, amount: int = 1) -> bool:
    result = await self.user_db.update_one({"_id": user_id}, {"$inc": {"farmed": amount}})
    return result.modified_count == 1
  
  async def set_user_tokens(self, user_id: UserID, tokens: int | None = None) -> bool:
    """
    Set the number of shroom tokens a user has
    If you wish to change it directly rather than changing the `User` object,
    use the `tokens` parameter.
    """
    result = await self.user_db.update_one({"_id": user_id}, {"$set": {"tokens": tokens}})
    return result.modified_count == 1
  
  async def rank_up_user(self, user_id: UserID) -> bool:
    """
    Increases the user's rank by 1
    NOTE: This does not implement any check to see if the user is already at the max rank
    """
    result = await self.user_db.update_one({"_id": user_id}, {"$inc": {"rank_enum": 1}})
    return result.modified_count == 1

  ################################
  ### Stat Collection Operations
  ################################

  async def get_latest_daily_stats(self) -> DailyStats | None:
    stats: DailyStatsDict | None = await self.stats_db.find_one({}, sort=[("$natural", -1)])
    if stats is None:
      return None
    else:
      return DailyStats(**stats)
    
  async def insert_daily_stats(self, stats: DailyStats):
    await self.stats_db.insert_one(stats.to_dict())

  async def clear_daily_stats(self):
    """|coro|

    Removes all documents in the `Stats` collection
    WARNING: This function is extremely destructive and will wipe out
    1 week's worth of farming data.
    This is only here to reset the `Stats` collection completely when the bot restarts
    which will only happen once a month due to limitations with free hosting.
    """
    await self.stats_db.delete_many({}) # rip


  async def get_total_weekly_farmed(self) -> int:
    total = self.daily_stats.total
    async for stat in self.stats_db.find({}, projection=("total",)):
      total += stat["total"]
    return total
  
  async def get_server_weekly_farmed(self, farm_id: ServerID) -> int:
    farm_stats = self.daily_stats.get_farm_stats(farm_id)
    total = farm_stats.farmed if farm_stats is not None else 0
    async for farm_stats in self.stats_db.find({}, projection=("farms",)):
      farm_stats = farm_stats.get(farm_id)
      if farm_stats is None:
        continue
      else:
        total += farm_stats.get("farmed", 0)
    return total
  
  async def get_user_weekly_farmed(self, user_id: UserID) -> int:
    total = self.daily_stats.get_user_farmed(user_id)
    async for user_stats in self.stats_db.find({}, projection=("users",)):
      total += user_stats.get(user_id, 0)
    return total


  async def get_server_contributors(self, farm_id: ServerID) -> dict[UserID, int]:
    farm_stats = self.daily_stats.get_farm_stats(farm_id)
    if farm_stats is None:
      contributors = Counter()
    else:
      contributors = Counter(farm_stats.contributors)
    async for farm_stats in self.stats_db.find({}, projection=("farms",)):
      farm_stats = farm_stats.get(farm_id)
      if farm_stats is None:
        continue
      else:
        contributors.update(farm_stats["contributors"])
    return dict(contributors)
  
  def get_server_top_daily_contributors(self, farm_id: ServerID, limit: int = 10) -> dict[UserID, int]:
    farm_stats = self.daily_stats.get_farm_stats(farm_id)
    if farm_stats is None:
      return dict()
    contributors = farm_stats.contributors
    return dict(sorted(contributors.items(), key=itemgetter(1), reverse=True))
  
  async def get_server_top_weekly_contributors(self, farm_id: ServerID, limit: int = 10) -> dict[UserID, int]:
    contributors = await self.get_server_contributors(farm_id)
    return dict(sorted(contributors.items(), key=itemgetter(1), reverse=True))



  async def farm(self, server_id: ServerID, user_id: UserID) -> int:

    farm = self.farms[server_id]
    farm.total_farmed += 1
    farm.farmed_today += 1
    farm.last_farmer = user_id
    
    # Why do I do this
    if await self.get_user(user_id) is None:
      await self.create_user(user_id)
    await self.inc_user_farmed(user_id)

    await self.save_farm(farm)

    return farm.farmed_today
