def int_to_ordinal(n: int) -> str:
  s = str(n)
  if len(s) >= 2 and s[-2] in "123": # I love bugfixing this
    s += "th"
  elif s[-1] == "1":
    s += "st"
  elif s[-1] == "2":
    s += "nd"
  elif s[-1] == "3":
    s += "rd"
  else:
    s += "th"
  return s

def str_key_to_int(d: dict):
  return {int(k): v for k, v in d.items()}

def int_key_to_str(d: dict):
  return {str(k): v for k, v in d.items()}