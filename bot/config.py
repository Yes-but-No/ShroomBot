from __future__ import annotations
import os

from typing import TypedDict


CONFIG_KEYS = (
  "token", "dev_server_id", "prefix", "mongo_url"
)

class ConfigDict(TypedDict):
  "A dictionary containing all the data the bot needs"
  token: str
  dev_server_id: int
  prefix: str
  mongo_url: str | None



def get_config_from_env() -> ConfigDict:
  config = {}
  for key in CONFIG_KEYS:
    val = os.getenv(key.upper())
    if val is None:
      continue
    if val == "TRUE":
      val = True
    elif val == "FALSE":
      val = False
    elif val.isdigit():
      val = int(val)
    config[key] = val
  return config # type: ignore
