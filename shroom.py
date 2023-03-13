
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict

from motor import motor_asyncio


class UserDict(TypedDict):
  _id: int
  joined: datetime
  farmed: int

class FarmDict(TypedDict):
  _id: int | None
  farmed_today: int
  total_farmed: int
  last_farmer: int | None
  farm_channel: int | None
  updated: datetime | None



@dataclass
class Farm:
  _id: int
  farmed_today: int = 0
  total_farmed: int = 0
  last_farmer: int | None = None
  farm_channel: int | None = None
  updated: datetime  = datetime.utcnow()

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



class ShroomFarm:
  def __init__(self, url: str = "localhost"):
    self.db_url = url
    self._db_client = motor_asyncio.AsyncIOMotorClient(url)
    self.shroom_db: motor_asyncio.AsyncIOMotorDatabase = self._db_client["ShroomDB"]

    self.farm_db: motor_asyncio.AsyncIOMotorCollection = self.shroom_db["Farm"]
    self.user_db: motor_asyncio.AsyncIOMotorCollection = self.shroom_db["Users"]

    self.farms: dict[int, Farm] = {}



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

  async def create_farm(self, server_id: int, channel: int | None = None):
    if self.get_farm(server_id) is not None:
      raise ValueError(f"farm with ID `{server_id}` already exists")
    farm = Farm(server_id, farm_channel=channel)
    self.farms[server_id] = farm
    await self.farm_db.insert_one(farm.to_dict())

  async def set_farm_channel(self, farm_id: int, channel_id: int):
    farm = self.get_farm(farm_id)
    if farm is None:
      raise ValueError(f"server with ID `{farm_id}` does not exist")
    farm.farm_channel = channel_id
    await self.save_farm(farm)
  
  async def reset_daily_count(self):
    for farm in self.farms.values():
      farm.farmed_today = 0
    await self.farm_db.update_many({}, {"$set": {"farmed_today": 0}})



  async def get_user(self, user_id: int) -> UserDict | None:
    return await self.user_db.find_one({"_id": user_id})

  async def create_user(self, user_id: int):
    if await self.get_user(user_id) is not None:
      raise ValueError(f"user with ID `{user_id}` already exists")
    await self.user_db.insert_one({"_id": user_id, "joined": datetime.utcnow(), "farmed": 0})
  
  async def inc_user_farmed(self, user_id: int) -> bool:
    result = await self.user_db.update_one({"_id": user_id}, {"$inc": {"farmed": 1}})
    return result.modified_count == 1



  async def farm(self, server_id: int, user_id: int) -> int:

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
