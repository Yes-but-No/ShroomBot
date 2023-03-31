from __future__ import annotations
from collections import Counter
from operator import itemgetter

from typing import TYPE_CHECKING, TypedDict

from motor import motor_asyncio

from farm import Farm
from stats import DailyStats
from user import User
from id_types import UserID

if TYPE_CHECKING:
  from id_types import ServerID, ChannelID
  from stats import DailyStatsDict, DailyFarmStats

class FarmResultsDict(TypedDict):
  farm_stats: DailyFarmStats
  user: User


class ShroomFarm:
  def __init__(self, url: str = "localhost"):
    self.db_url = url
    self._db_client = motor_asyncio.AsyncIOMotorClient(url)
    self.shroom_db: motor_asyncio.AsyncIOMotorDatabase = self._db_client["ShroomDB"]

    self.farm_db: motor_asyncio.AsyncIOMotorCollection = self.shroom_db["Farm"]
    self.user_db: motor_asyncio.AsyncIOMotorCollection = self.shroom_db["Users"]
    self.stats_db: motor_asyncio.AsyncIOMotorCollection = self.shroom_db["Stats"]

  async def setup(self):
    latest_stats = await self.get_latest_daily_stats()
    if latest_stats is not None and latest_stats.is_today:
      self.daily_stats = latest_stats
    else:
      self.daily_stats = DailyStats()

  ##################################
  ### Server Collection Operations
  ##################################

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

  async def get_farm(self, farm_id: int) -> Farm | None:
    d = await self.farm_db.find_one({"_id": farm_id})
    if d is None:
      return None
    return Farm(**d)

  async def create_farm(self, server_id: ServerID, channel: ChannelID | None = None) -> Farm:
    if await self.get_farm(server_id) is not None:
      raise ValueError(f"farm with ID `{server_id}` already exists")
    farm = Farm(server_id, farm_channel=channel)
    await self.farm_db.insert_one(farm.to_dict())
    return farm

  async def set_farm_channel(self, farm_id: ServerID, channel_id: ChannelID):
    farm = await self.get_farm(farm_id)
    if farm is None:
      raise ValueError(f"server with ID `{farm_id}` does not exist")
    farm.farm_channel = channel_id
    await self.save_farm(farm)

  async def set_daily_goal(self, farm_id: ServerID, daily_goal: int | None):
    farm = await self.get_farm(farm_id)
    if farm is None:
      raise ValueError(f"server with ID `{farm_id}` does not exist")
    farm.daily_goal = daily_goal
    await self.save_farm(farm)

  ################################
  ### User Collection Operations
  ################################

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

  async def get_user(self, user_id: UserID) -> User | None:
    d = await self.user_db.find_one({"_id": user_id})
    if d is None:
      return None
    return User(**d)

  async def create_user(self, user_id: UserID) -> User:
    if await self.get_user(user_id) is not None:
      raise ValueError(f"user with ID `{user_id}` already exists")
    user = User(user_id)
    await self.user_db.insert_one(user.to_dict())
    return user
  
  async def inc_user_farmed(self, user_id: UserID, amount: int = 1) -> bool:
    result = await self.user_db.update_one({"_id": user_id}, {"$inc": {"farmed": amount}})
    return result.modified_count == 1
  
  async def inc_user_tokens(self, user_id: UserID, tokens: int = 1) -> bool:
    result = await self.user_db.update_one({"_id": user_id}, {"$inc": {"tokens": tokens}})
    return result.modified_count == 1
  
  async def user_farm(self, user_id: UserID, amount: int = 1) -> bool:
    result = await self.user_db.update_one({"_id": user_id}, {"$inc": {"farmed": amount, "tokens": amount}})
    return result.modified_count == 1
  
  async def set_user_tokens(self, user_id: UserID, tokens: int | None = None) -> bool:
    """|coro|

    Directly set the number of tokens a user has.
    NOTE: This does not check if the user exists in the database
    """
    result = await self.user_db.update_one({"_id": user_id}, {"$set": {"tokens": tokens}})
    return result.modified_count == 1
  
  async def rank_up_user(self, user_id: UserID) -> bool:
    """|coro|

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
      return DailyStats.from_db(stats)
    
  async def save_daily_stats(self, stats: DailyStats):
    latest_stats = await self.get_latest_daily_stats()
    if latest_stats is not None and latest_stats.is_today:
      return
    else:
      await self.stats_db.insert_one(stats.to_dict())
      self.daily_stats = DailyStats()

  async def clear_daily_stats(self):
    """|coro|

    Removes all documents in the `Stats` collection
    WARNING: This function is extremely destructive and will wipe out
    1 week's worth of farming data.
    """
    await self.stats_db.delete_many({}) # rip

  async def update_daily_stats(self):
    if self.daily_stats.date == 6:
      # If it's a Sunday, we have to clear the `Stats` collection
      await self.clear_daily_stats()
    else:
      await self.save_daily_stats(self.daily_stats)
    self.daily_stats = DailyStats()


  def get_server_farmed_today(self, farm_id: ServerID) -> int:
    farm_stats = self.daily_stats.get_farm_stats(farm_id)
    return farm_stats.farmed if farm_stats is not None else 0
  
  def get_user_farmed_today(self, user_id: UserID) -> int:
    return self.daily_stats.get_user_farmed(user_id)


  async def get_total_weekly_farmed(self) -> int:
    total = self.daily_stats.total
    async for stat in self.stats_db.find({}, projection=("total",)):
      total += stat["total"]
    return total
  
  async def get_server_weekly_farmed(self, farm_id: ServerID) -> int:
    total = self.get_server_farmed_today(farm_id)
    async for farm_stats in self.stats_db.find({}, projection=("farms",)):
      farm_stats = farm_stats.get(str(farm_id))
      if farm_stats is None:
        continue
      else:
        total += farm_stats.get("farmed", 0)
    return total
  
  async def get_user_weekly_farmed(self, user_id: UserID) -> int:
    total = self.daily_stats.get_user_farmed(user_id)
    async for user_stats in self.stats_db.find({}, projection=("users",)):
      total += user_stats.get(str(user_id), 0)
    return total


  async def get_server_contributors(self, farm_id: ServerID) -> dict[UserID, int]:
    farm_stats = self.daily_stats.get_farm_stats(farm_id)
    if farm_stats is None:
      contributors = Counter()
    else:
      contributors = Counter(farm_stats.contributors)
    async for farm_stats in self.stats_db.find({}, projection=("farms",)):
      farm_stats = farm_stats.get(str(farm_id))
      if farm_stats is None:
        continue
      else:
        contributors.update(farm_stats["contributors"])
    return {UserID(k): v for k, v in contributors.items()}
  
  def get_server_top_daily_contributors(self, farm_id: ServerID) -> dict[UserID, int]:
    farm_stats = self.daily_stats.get_farm_stats(farm_id)
    if farm_stats is None:
      return dict()
    contributors = farm_stats.contributors
    return {UserID(k): v for k, v in sorted(contributors.items(), key=itemgetter(1), reverse=True)} 
  
  async def get_server_top_weekly_contributors(self, farm_id: ServerID) -> dict[UserID, int]:
    contributors = await self.get_server_contributors(farm_id)
    return {UserID(k): v for k, v in sorted(contributors.items(), key=itemgetter(1), reverse=True)}



  async def award_contributors(self, farm_stats: DailyFarmStats):
    for user_id, amount in farm_stats.contributors.items():
      await self.inc_user_tokens(user_id, amount)
    farm_stats.awarded_daily = True
    self.daily_stats.save_farm_stats(farm_stats)

  async def farm(self, farm: Farm, user_id: UserID, amount: int = 1) -> FarmResultsDict:

    farm_stats = self.daily_stats.inc_shroom_count(farm, user_id, amount)

    farm.total_farmed += amount
    farm.last_farmer = user_id
    
    # Why do I do this
    user = await self.get_user(user_id) or await self.create_user(user_id)
    await self.user_farm(user_id)

    await self.save_farm(farm)

    return {"farm_stats": farm_stats, "user": user}