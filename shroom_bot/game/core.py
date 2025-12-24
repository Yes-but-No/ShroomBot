from __future__ import annotations

import asyncio

from .models import ShroomFarm


class ShroomFarmGame:
    def __init__(self):
        self._farms: dict[int, ShroomFarm] = {}  # server_id -> ShroomFarm
        self._farm_locks: dict[int, asyncio.Lock] = {}  # server_id -> Lock

    async def acquire_farm_lock(self, server_id: int):
        try:
            sem = self._farm_locks[server_id]
        except KeyError:
            self._farm_locks[server_id] = sem = asyncio.Lock()

        return await sem.acquire()

    def release_farm_lock(self, server_id: int):
        try:
            sem = self._farm_locks[server_id]
        except KeyError:
            # ... okay
            return
        else:
            sem.release()

        # Check if there are any more waiting
        if not sem.locked():
            del self._farm_locks[server_id]

    async def get_farm(self, server_id: int) -> ShroomFarm | None:
        return self._farms.get(server_id)

    async def get_all_farms(self) -> list[ShroomFarm]:
        return list(self._farms.values())

    async def create_farm(self, server_id: int, farm_channel_id: int) -> ShroomFarm:
        if await self.get_farm(server_id) is not None:
            raise ValueError(f"farm with ID `{server_id}` already exists")
        farm = ShroomFarm(server_id=server_id, farm_channel_id=farm_channel_id)
        self._farms[server_id] = farm
        return farm

    async def set_farm_channel(self, server_id: int, farm_channel_id: int) -> None:
        farm = await self.get_farm(server_id)
        if farm is None:
            raise ValueError(f"farm with ID `{server_id}` does not exist")
        farm.farm_channel_id = farm_channel_id

    async def update_server_farmed(
        self, server_id: int, farmer_id: int, amount: int = 1
    ):
        farm = await self.get_farm(server_id)
        if farm is None:
            raise ValueError(f"farm with ID `{server_id}` does not exist")
        farm.last_farmer_id = farmer_id
        farm.farmed += amount
        return farm
