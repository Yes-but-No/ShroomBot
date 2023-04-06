from __future__ import annotations

from asyncio import Semaphore


class FarmingManager:
  """A manager for ensuring that servers are only farming one at a time"""

  def __init__(self):
    self._mapping: dict[int, Semaphore] = {}

  async def acquire_farm(self, farm_id: int):
    try:
      sem = self._mapping[farm_id]
    except KeyError:
      self._mapping[farm_id] = sem = Semaphore(1)
    
    return await sem.acquire()
  
  def release_farm(self, farm_id: int):
    try:
      sem = self._mapping[farm_id]
    except KeyError:
      # ... okay
      return
    else:
      sem.release()

    # Check if there are any more waiting
    if sem._value == 1:
      del self._mapping[farm_id]