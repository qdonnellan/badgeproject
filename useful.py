from dateutil import tz
from datetime import datetime
from google.appengine.api import users
from database import existing_user
import re

def valid_user():
  current_google_user = users.get_current_user()
  local_user = existing_user(current_google_user)
  if local_user:
    return local_user
  else:
    return False

def get_local_time(timestamp):
  from_zone = tz.tzutc()
  to_zone = tz.gettz('America/New_York')
  timestamp = timestamp.replace(tzinfo=from_zone)
  central = timestamp.astimezone(to_zone)
  return central.strftime("%A, %B %d, %H:%M EST")
