import webapp2
from handlers import MainHandler
from icon_list import the_list
import re, logging
from google.appengine.api import users
from database import *
from ajax import *
from useful import valid_user


class badgeCreator(MainHandler):
  def get(self, badgeID=None):
    if valid_user():
      badge = get_badge(valid_user(),badgeID)
      logging.info(badge.checkpoints)
      self.render('badge_creator.html', badge = get_badge(valid_user(),badgeID), icon_array = the_list, badges_active = "active")
  def post(self, badgeID=None):
    if valid_user():
      edit_badge(
        badgeID = badgeID,
        icon = self.request.get("icon"),
        icon_color = self.request.get("icon_color"), 
        border_color = self.request.get("border_color"), 
        background = self.request.get("background"), 
        name = self.request.get("badge_name"),
        requirement = self.request.get("requirement"), 
        value = self.request.get("badge_value"),
        teacher = valid_user(),
        checkpoints = self.request.get_all("checkpoint_options")
        )
      self.redirect('/badges')

class simplePages(MainHandler):
  def get(self, pageName):
    if pageName in ['front']:
      self.render('%s.html' % pageName)
    else:
      self.redirect('/')

class link(MainHandler):
  def get(self):    
    current_google_user = users.get_current_user()
    if not existing_user(current_google_user):
      self.render('link.html')
    else:
      self.redirect('/profile')

  def post(self):
    current_google_user = users.get_current_user()
    if current_google_user:
      formalName = self.request.get('formalName')
      new_user(current_google_user, formalName)
      self.redirect('/profile')

class editCourse(MainHandler):
  def get(self, courseID = None):
    if valid_user():
      logging.info(courseID)
      self.render('edit_course.html', course = existing_course(courseID, valid_user()))
    else:
      self.redirect('/link')

  def post(self, courseID = None):
    if valid_user():
      course_name = self.request.get('course_name')
      course_code = self.request.get('course_code')
      edit_course(course_name = course_name, course_code = course_code, courseID = courseID, user = valid_user())
    self.redirect('/profile')

class profile(MainHandler):
  def get(self):
    if valid_user():
      self.render('profile.html', profile_active ="active")
    else:
      self.redirect('/front')

class course(MainHandler):
  def get(self, courseID):
    if valid_user():
      this_course = get_user_courses(valid_user(), courseID)
      self.render('course.html', 
        course = this_course, 
        registrations = get_registrations(this_course), 
        checkpoints = get_course_checkpoints(this_course),
        courseID = int(courseID),
        badges = get_all_badges(valid_user()))
    else:
      self.redirect('/front')

class home(MainHandler):
  def get(self):
    current_google_user = users.get_current_user()
    if current_google_user:
      self.render('base.html')
    else:
      self.redirect('/front')

class listBadges(MainHandler):
  def get(self):
    if valid_user():
      self.render('badges.html', badges = get_all_badges(valid_user()), badges_active = "active")

class register(MainHandler):
  def get(self):
    if valid_user():
      self.render('register.html')

  def post(self):
    if valid_user():
      teacher_email = self.request.get('teacher_email')
      course_code = self.request.get('course_code')
      if teacher_email:
        teacher = get_user_by_email(teacher_email)
        if teacher:
          success = register_for_course(student = valid_user(), teacher = teacher, course_code = course_code)
          if success:
            self.redirect('/profile')
          else:
            self.redirect('/register?error=invalid course code')
        else:
          self.redirect('/register?error=that teacher email does not exist in the system')
      else:
        self.redirect('/register?error=you cannot leave the teacher email field blank')

class completeRegistration(MainHandler):
  def get(self, courseID, studentID, action):
    if valid_user():
      edit_registration(courseID = courseID, teacher = valid_user(), action = action, studentID = studentID)
    self.redirect('/course/%s' % courseID)

class studentProfile(MainHandler):
  def get(self, teacherID, courseID):
    if valid_user():
      course = get_student_course(courseID = courseID, student = valid_user(), teacherID = teacherID)
      self.render('student_profile.html', course = course, teacherID=int(teacherID), courseID = int(courseID))

class newCheckpoint(MainHandler):
  def get(self, courseID):
    if valid_user():
      course = existing_course(courseID = courseID, user = valid_user())
      if course:
        self.render('edit_checkpoint.html', course = course, new_checkpoint = True)

  def post(self, courseID):
    if valid_user():
      course = existing_course(courseID = courseID, user = valid_user())
      if course:        
        name = self.request.get('checkpoint_name')
        description = self.request.get('description')
        create_new_checkpoint(name = name, description = description, course = course)

    self.redirect('/course/%s' % courseID)

class singleBadge(MainHandler):
  def get(self, badgeID):
    if valid_user():
      self.render('single_badge.html', badge = get_badge(valid_user(),badgeID))





app = webapp2.WSGIApplication([
  ('/badge_creator', badgeCreator),
  ('/badge_creator/(\w+)', badgeCreator),
  ('/student_profile/(\w+)/(\w+)', studentProfile),
  #('/student_course/(\w+)', studentCourse),
  ('/complete_registration/(\w+)/(\w+)/(\w+)', completeRegistration),
  ('/link', link),
  ('/register', register),
  ('/profile', profile),
  ('/badges', listBadges),
  ('/badge/(\w+)', singleBadge),
  ('/edit_course', editCourse),
  ('/edit_course/(\w+)', editCourse),
  ('/achievementHandler', achievementHandler),
  ('/course/(\w+)/new_checkpoint', newCheckpoint),
  ('/course/(\w+)', course),
  ('/(\w+)', simplePages),
  ('.*', home)
], debug=False)
