"""
Literal hard-coded ranks for the bot
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Rank:
  name: str
  requirement: int
  enum: int

RANKS = (
  #   |     Rank Name     | Required | Enum |
  Rank("Shroom Forager"     , 0      , 0),
  Rank("Fungi Farmer"       , 50     , 1),
  Rank("Truffle Hunter"     , 100    , 2),
  Rank("Mycology Enthusiast", 250    , 3),
  Rank("Fungi Apprentice"   , 500    , 4),
  Rank("Truffle Collector"  , 1000   , 5),
  Rank("Shroom Maestro"     , 2500   , 6),
  Rank("Truffle Connoisseur", 5000   , 7),
  Rank("Fungi Master"       , 10000  , 8),
  Rank("Mycologist"         , 25000  , 9),
  Rank("Shroom Baron"       , 50000  , 10),
  Rank("Truffle King/Queen" , 100000 , 11),
  Rank("Fungi Overlord"     , 250000 , 12),
  Rank("Mycology Mogul"     , 500000 , 13),
  Rank("Shroom Deity"       , 1000000, 14)
)