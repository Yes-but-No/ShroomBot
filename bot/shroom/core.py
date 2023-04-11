from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from operator import itemgetter

from typing import TYPE_CHECKING

from motor import motor_asyncio

from bot.shroom.farm import Farm
from bot.shroom.ranks import Rank
from bot.shroom.stats import DailyStats
from bot.shroom.user import User

if TYPE_CHECKING:
  from bot.shroom.stats import DailyStatsDict, DailyFarmStats

@dataclass
class FarmResult:
  farmed: int
  daily_goal_reached: bool
  daily_goal: int | None
  user: User
  user_ranked_up: bool = False
  awarding_daily: bool = False


class ShroomFarm:
  def __init__(self, url: str = "localhost"):
    self.db_url = url
    self._db_client = motor_asyncio.AsyncIOMotorClient(url)
    self.shroom_db: motor_asyncio.AsyncIOMotorDatabase = self._db_client["ShroomDB"]

    self.farm_db: motor_asyncio.AsyncIOMotorCollection = self.shroom_db["Farm"]
    self.user_db: motor_asyncio.AsyncIOMotorCollection = self.shroom_db["Users"]
    self.stats_db: motor_asyncio.AsyncIOMotorCollection = self.shroom_db["Stats"]

    super().__init__()

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

  async def create_farm(self, server_id: int, channel: int | None = None) -> Farm:
    if await self.get_farm(server_id) is not None:
      raise ValueError(f"farm with ID `{server_id}` already exists")
    farm = Farm(server_id, farm_channel=channel)
    await self.farm_db.insert_one(farm.to_dict())
    return farm

  async def set_farm_channel(self, farm_id: int, channel_id: int):
    farm = await self.get_farm(farm_id)
    if farm is None:
      raise ValueError(f"server with ID `{farm_id}` does not exist")
    farm.farm_channel = channel_id
    await self.save_farm(farm)

  async def set_daily_goal(self, farm_id: int, daily_goal: int | None):
    farm = await self.get_farm(farm_id)
    if farm is None:
      raise ValueError(f"server with ID `{farm_id}` does not exist")
    farm.daily_goal = daily_goal
    await self.save_farm(farm)

  ################################
  ### User Collection Operations
  ################################

  async def save_user(self, user: User) -> bool:
    result = await self.user_db.update_one(
      {
        "_id": user._id
      },
      {
        "$set": user.to_dict(include_id=False)
      }
    )
    return result.modified_count == 1

  async def get_user(self, user_id: int) -> User | None:
    d = await self.user_db.find_one({"_id": user_id})
    if d is None:
      return None
    return User(**d)

  async def create_user(self, user_id: int) -> User:
    if await self.get_user(user_id) is not None:
      raise ValueError(f"user with ID `{user_id}` already exists")
    user = User(user_id)
    await self.user_db.insert_one(user.to_dict())
    return user
  
  async def inc_user_farmed(self, user_id: int, amount: int = 1) -> bool:
    result = await self.user_db.update_one({"_id": user_id}, {"$inc": {"farmed": amount}})
    return result.modified_count == 1
  
  async def inc_user_tokens(self, user_id: int, tokens: int = 1) -> bool:
    result = await self.user_db.update_one({"_id": user_id}, {"$inc": {"tokens": tokens, "lifetime_tokens": tokens}})
    return result.modified_count == 1
  
  async def set_user_tokens(self, user_id: int, tokens: int | None = None) -> bool:
    """|coro|

    Directly set the number of tokens a user has.
    NOTE: This does not check if the user exists in the database
    """
    result = await self.user_db.update_one({"_id": user_id}, {"$set": {"tokens": tokens}})
    return result.modified_count == 1
  
  async def set_user_rank(self, user_id: int, rank_or_int: Rank | int) -> bool:
    """|coro|

    Sets the user's rank
    NOTE: This does not implement any check to see if the user deserves that rank
    """
    if isinstance(rank_or_int, Rank):
      enum = rank_or_int.enum
    elif isinstance(rank_or_int, int):
      enum = rank_or_int
    else:
      raise TypeError("value must be either a `Rank` or `int` type")

    result = await self.user_db.update_one({"_id": user_id}, {"$set": {"rank_enum": enum}})
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
    
  async def save_daily_stats(self, stats: DailyStats) -> bool:
    latest_stats = await self.get_latest_daily_stats()
    if latest_stats is not None and latest_stats.date.date() == stats.date.date():
      result = await self.stats_db.replace_one({"_id": latest_stats._id}, stats.to_dict())
      return result.modified_count == 1
    else:
      result = await self.stats_db.insert_one(stats.to_dict())
      return bool(result)

  async def clear_daily_stats(self):
    """|coro|

    Removes all documents in the `Stats` collection
    WARNING: This function is extremely destructive and will wipe out
    1 week's worth of farming data.
    """
    await self.stats_db.delete_many({}) # rip

  async def update_daily_stats(self) -> bool:
    if self.daily_stats.date.isoweekday() == 7:
      # If it's a Sunday, we have to clear the `Stats` collection
      await self.clear_daily_stats()
      # We can't tell if it is successful since we don't know how many
      # documents are in the collection, so we just assume it worked
      result = True
    else:
      result = await self.save_daily_stats(self.daily_stats)
    self.daily_stats = DailyStats()
    return result


  def get_server_farmed_today(self, farm_id: int) -> int:
    farm_stats = self.daily_stats.get_farm_stats(farm_id)
    return farm_stats.farmed if farm_stats is not None else 0
  
  def get_user_farmed_today(self, user_id: int) -> int:
    return self.daily_stats.get_user_farmed(user_id)


  async def get_total_weekly_farmed(self) -> int:
    total = self.daily_stats.total
    async for stat in self.stats_db.find({}, projection=("total",)):
      total += stat["total"]
    return total
  
  async def get_server_weekly_farmed(self, farm_id: int) -> int:
    total = self.get_server_farmed_today(farm_id)
    async for farm_stats in self.stats_db.find({}, projection=("farms",)):
      farm_stats = farm_stats["farms"].get(str(farm_id))
      if farm_stats is None:
        continue
      else:
        total += farm_stats.get("farmed", 0)
    return total
  
  async def get_user_weekly_farmed(self, user_id: int) -> int:
    total = self.daily_stats.get_user_farmed(user_id)
    async for user_stats in self.stats_db.find({}, projection=("users",)):
      total += user_stats["users"].get(str(user_id), 0)
    return total


  async def get_server_contributors(self, farm_id: int) -> dict[int, int]:
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
    return {int(k): v for k, v in contributors.items()}
  
  def get_server_top_daily_contributors(self, farm_id: int) -> dict[int, int]:
    farm_stats = self.daily_stats.get_farm_stats(farm_id)
    if farm_stats is None:
      return dict()
    contributors = farm_stats.contributors
    return {int(k): v for k, v in sorted(contributors.items(), key=itemgetter(1), reverse=True)} 
  
  async def get_server_top_weekly_contributors(self, farm_id: int) -> dict[int, int]:
    contributors = await self.get_server_contributors(farm_id)
    return {int(k): v for k, v in sorted(contributors.items(), key=itemgetter(1), reverse=True)}



  async def award_contributors(self, farm_stats: DailyFarmStats):
    farm_stats.awarded_daily = True
    for user_id, amount in farm_stats.contributors.items():
      await self.inc_user_tokens(user_id, amount)
    self.daily_stats.save_farm_stats(farm_stats)

  async def farm(self, farm: Farm, user_id: int, amount: int = 1) -> FarmResult:
    farm_stats = self.daily_stats.inc_shroom_count(farm, user_id, amount)

    farm.total_farmed += amount
    farm.last_farmer = user_id

    user = await self.get_user(user_id) or await self.create_user(user_id)
    user.farmed += amount
    user.tokens += amount
    user.lifetime_tokens += amount

    result = FarmResult(
      farm_stats.farmed,
      farm_stats.daily_goal_reached,
      farm_stats.daily_goal,
      user
    )

    if user.ranked_up:
      user = user.update_rank()
      result.user_ranked_up = True

    if all((
      farm_stats.daily_goal is not None,
      farm_stats.daily_goal_reached,
      not farm_stats.awarded_daily
    )):
      await self.award_contributors(farm_stats)
      result.awarding_daily = True

    await self.save_user(user)
    await self.save_farm(farm)

    return result