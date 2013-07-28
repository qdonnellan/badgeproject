
from google.appengine.api import users
from database import existing_user

def valid_user():
  current_google_user = users.get_current_user()
  local_user = existing_user(current_google_user)
  if local_user:
    return local_user
  else:
    return False