from __future__ import annotations
from dataclasses import dataclass
import os


@dataclass
class Config:
  token: str
  dev_server_id: int
  prefix: str = "$"
  maintenance_mode: bool = False
  mongo_url: str = "localhost"


def get_config_from_env() -> Config:
  config = {}
  for key in Config.__dataclass_fields__.keys():
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
  return Config(**config)
