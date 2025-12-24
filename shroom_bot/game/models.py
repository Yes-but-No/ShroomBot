from __future__ import annotations

from attrs import define


@define
class ShroomFarm:
    """Represents a Shroom Farm in a discord server."""

    server_id: int
    last_farmer_id: int | None = None
    farm_channel_id: int | None = None
    farmed: int = 0
