import os
import jinja2
import webapp2
from google.appengine.api import users
from database import *
from cached_objects import get_cached_user_courses
from useful import get_local_time

template_dir=os.path.join(os.path.dirname(__file__),"templates")
jinja_environment=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),autoescape=True)

class MainHandler(webapp2.RequestHandler):
  def write(self, *a, **kw):
    self.response.out.write(*a, **kw)
      
  def render_str(self, template, **params):
    t = jinja_environment.get_template(template)
    return t.render(params)
  
  def render(self, template, **kw):  
    local_user = existing_user(users.get_current_user())              
    raw_html = self.render_str(
      template, 
      error = self.request.get('error'),
      success = self.request.get('success'),
      google_user_api = users,
      local_user = local_user,
      get_student = get_student,
      courses = get_user_courses(local_user),
      enrollments = get_enrolled_courses(local_user),
      get_local_time = get_local_time,
      **kw)
    self.write(raw_html)
    return raw_html



