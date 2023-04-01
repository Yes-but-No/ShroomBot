"""
Literal hard-coded ranks for the bot
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Rank:
  name: str
  requirement: int

RANKS = (
  Rank("Shroom Forager", 0),
  Rank("Fungi Farmer", 50),
  Rank("Truffle Hunter", 100),
  Rank("Mycology Enthusiast", 250),
  Rank("Fungi Apprentice", 500),
  Rank("Truffle Collector", 1000),
  Rank("Shroom Maestro", 2500),
  Rank("Truffle Connoisseur", 5000),
  Rank("Fungi Master", 10000),
  Rank("Mycologist", 25000),
  Rank("Shroom Baron", 50000),
  Rank("Truffle King/Queen", 100000),
  Rank("Fungi Overlord", 250000),
  Rank("Mycology Mogul", 500000),
  Rank("Shroom Deity", 1000000)
)