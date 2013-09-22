import webapp2
from handlers import MainHandler
from icon_list import the_list
import re, logging
from google.appengine.api import users
from database import *
from ajax import *
from useful import valid_user
from cached_objects import *
import json

class badgeCreator(MainHandler):
  def get(self, badgeID=None):
    if valid_user() and valid_user().teacher:
      badge = get_badge(valid_user(),badgeID)
      checkpointID = self.request.get('checkpointID')
      courseID = self.request.get('courseID')
      badge_creator_active = 'active'
      if checkpointID.isdigit() and courseID.isdigit():
        checkpointID = int(checkpointID)
        courseID = int(courseID)
        badge_creator_active = ""
      self.render('badge_creator.html', 
        badge = get_badge(valid_user(),badgeID), 
        icon_array = the_list, 
        badge_creator_active = badge_creator_active,
        checkpointID = checkpointID,
        courseID = courseID,
        get_course_checkpoints = get_course_checkpoints)
  def post(self, badgeID=None):
    if valid_user() and valid_user().teacher:
      teacher = valid_user()
      teacherID = valid_user().key.id()
      old_checkpoints=[]
      if badgeID:
        old_badge = get_badge(teacher, badgeID)
        if old_badge:
          old_checkpoints = old_badge.checkpoints
      checkpoint_keys = self.request.get_all("checkpoint_options")
      badgeID = edit_badge(
        badgeID = badgeID,
        icon = self.request.get("icon"),
        icon_color = self.request.get("icon_color"), 
        border_color = self.request.get("border_color"), 
        background = self.request.get("background"), 
        name = self.request.get("badge_name"),
        requirement = self.request.get("requirement"), 
        value = self.request.get("badge_value"),
        teacher = teacher,
        checkpoints = checkpoint_keys
        )

      #remove badge from old checkpoints if applicable
      for old_checkpoint_key in old_checkpoints:
        if old_checkpoint_key not in checkpoint_keys:
          old_courseID, old_checkpointID = old_checkpoint_key.split('_')
          remove_badge_from_checkpoint(badgeID, old_checkpointID, old_courseID, teacherID)

      #add badge to new checkpoints in applicable
      for checkpoint_key in checkpoint_keys:
        courseID, checkpointID = checkpoint_key.split('_')
        if courseID:
          delete_cached_course(courseID, teacherID)
        if checkpointID and courseID:
          delete_cached_checkpoint(checkpointID, courseID, teacherID)
          add_badge_to_checkpoint(badgeID, checkpointID, courseID, teacherID)
          self.redirect('/course/%s#%s' % (courseID, checkpointID))
      else:
        self.redirect('/badge/%s' % badgeID)

class front(MainHandler):
  def get(self):
    if valid_user():
      self.redirect('/profile')
    else:
      self.render('front.html')

class changeUser(MainHandler):
  def get(self):
    if valid_user():
      self.render('change_user.html', profile_active = 'active')

  def post(self):
    if valid_user():
      formalName = self.request.get('formalName')
      edit_user(valid_user(), formalName = formalName)
    self.redirect('/profile')

class link(MainHandler):
  def get(self):   
    if valid_user():
      self.redirect('/profile')
    else:
      self.render('link.html')

  def post(self):
    current_google_user = users.get_current_user()
    if current_google_user:
      formalName = self.request.get('formalName')
      new_user(current_google_user, formalName)
      self.redirect('/profile')

class editCourse(MainHandler):
  def get(self, courseID = None):
    if valid_user():
      self.render('edit_course.html', course = existing_course(courseID, valid_user()))
    else:
      self.redirect('/link')

  def post(self, courseID = None):
    if valid_user():
      course_name = self.request.get('course_name')
      course_code = self.request.get('course_code')
      if verify_unique_course_code(course_code, valid_user(), courseID = courseID):
        course = edit_course(course_name = course_name, course_code = course_code, courseID = courseID, user = valid_user())
        self.redirect('/profile')
      else:
        self.redirect('/edit_course?error=you are already using that course code in another course')

class profile(MainHandler):
  def get(self):
    if valid_user():
      self.render('profile.html', profile_active ="active")
    else:
      self.redirect('/front')

class course(MainHandler):
  def get(self, courseID):
    if valid_user():
      teacher = valid_user()
      teacherID = teacher.key.id()
      html_cache_key = "html_course:%s_%s" % (teacherID, courseID)
      cached_html = None #get_cached_html_page(html_cache_key)
      if cached_html:
        self.write(cached_html)
      else:
        course = existing_course(courseID, teacher)
        raw_html = self.render('course.html', 
          course = course,
          registrations = get_registered_students(course),
          number_of_pending_registrations = get_number_of_pending_registrations(course),
          checkpoints = get_course_checkpoints(course),
          courseID = int(courseID),
          teacherID = int(teacherID),
          teacher = teacher,
          json = json,
          active_tab = self.request.get('active_tab'))
        logging.info('start set memcache html course')
        memcache.set(html_cache_key, raw_html)
        logging.info('end set memcache html course')
    else:
      self.redirect('/front')

  def post(self, courseID):
    if valid_user():
      course_name = self.request.get('course_name')
      course_code = self.request.get('course_code')
      delete_cached_course(courseID, valid_user().key.id())
      if verify_unique_course_code(course_code,valid_user(), courseID = courseID):
        course = edit_course(course_name = course_name, course_code = course_code, courseID = courseID, user = valid_user())
        self.redirect('/course/%s' % courseID)
      else:
        self.redirect('/course/%s?active_tab=settings&error=you are already using that course code in another course' % courseID)

class home(MainHandler):
  def get(self):
    if valid_user():
      self.redirect("/profile")
    else:
      self.redirect('/front')

class listBadges(MainHandler):
  def get(self):
    if valid_user():
      self.render('badges.html', 
        badges = get_all_badges(valid_user()), 
        badges_active = "active",
        get_checkpoints_for_badge = get_checkpoints_for_badge)

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
            course = get_course_by_code(teacher=teacher, course_code = course_code)
            delete_cached_course(course.key.id(), teacher.key.id())
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
      delete_cached_course(courseID, valid_user().key.id())
    self.redirect('/course/%s?active_tab=students' % courseID)

class studentProfile(MainHandler):
  def get(self, teacherID, courseID):
    if valid_user():
      if courseID:
        teacher = get_teacher(teacherID)
        student = valid_user()
        course = existing_course(courseID, teacher)
        self.render('course.html', 
          course = course,
          checkpoints = get_course_checkpoints(course),
          teacherID = int(teacherID), 
          get_badge = get_badge,
          courseID = int(courseID),
          student_profile = True, 
          student = student,
          teacher = teacher,
          get_checkpoint_badges = get_checkpoint_badges,
          badge_achieved = badge_achieved,
          get_checkpoint_percent_completion = get_checkpoint_percent_completion
          )
      else:
        self.write('You are not registered for this course...')

class teacherViewStudentProfile(MainHandler):
  def get(self, studentID, courseID):
    if valid_user():
      if courseID:
        teacher = valid_user()
        student = get_student(studentID)
        course = existing_course(courseID, teacher)
        teacherID = teacher.key.id()
        self.render('course.html', 
          course = course,
          checkpoints = get_course_checkpoints(course),
          teacherID= int(teacherID), 
          courseID = int(courseID),
          student = student,
          get_badge = get_badge,
          teacher_view_student_profile = True,
          active_tab = self.request.get('active_tab'),
          get_checkpoint_badges = get_checkpoint_badges,
          badge_achieved = badge_achieved,
          get_checkpoint_percent_completion = get_checkpoint_percent_completion
          )

class studentBadge(MainHandler):
  def get(self, teacherID, courseID, badgeID):
    if valid_user():
      teacher = get_teacher(teacherID)
      course = existing_course(courseID, teacher)
      student = valid_user()
      badge = get_badge(teacher, badgeID)
      this_badge_status = achievement_status(student = student, course = course, badge = badge, teacher = teacher)
      self.render('single_badge.html', 
        badge = badge,
        achievement_status = this_badge_status,
        student_badge = True,
        courseID = courseID,
        course = course, 
        teacher = teacher,
        student = valid_user(),
        teacherID = int(teacherID),
        get_checkpoints_for_badge = get_checkpoints_for_badge,
        evidence = get_evidence(badge, student.key.id())
        )
  def post(self, teacherID, courseID, badgeID):
    if valid_user():
      if courseID:
        teacher = get_teacher(teacherID)
        badge = get_badge(teacher, badgeID)
        content = self.request.get('content')
        create_evidence(valid_user().key.id(), badge, content, teacher=False)
    self.redirect('/student_badge/%s/%s/%s' % (teacherID, courseID, badgeID))

class teacherViewStudentBadge(MainHandler):
  def get(self, studentID, courseID, badgeID):
    if valid_user():
      teacher = valid_user()
      course = existing_course(courseID, teacher)
      if course:
        student = get_student(studentID)
        badge = get_badge(teacher, badgeID)
        this_badge_status = achievement_status(student = student, course = course, badge = badge, teacher = teacher)
        self.render('single_badge.html',
          badge = badge,
          achievement_status = this_badge_status,
          teacher_view_student_badge = True,
          student = student,
          course = course, 
          courseID = courseID,
          teacher = teacher,
          teacherID = int(teacher.key.id()),
          get_checkpoints_for_badge = get_checkpoints_for_badge, 
          evidence = get_evidence(badge, studentID)
          )

  def post(self, studentID, courseID, badgeID):
    if valid_user():
      if courseID:
        badge = get_badge(valid_user(), badgeID)
        content = self.request.get('content')
        create_evidence(studentID, badge, content, teacher=True)
    self.redirect('/student_badge/%s/%s/%s/teacher_view' % (studentID, courseID, badgeID))

class newCheckpoint(MainHandler):
  def get(self, courseID):
    if valid_user():
      course = existing_course(courseID = courseID, user = valid_user())
      if course:
        self.render('edit_checkpoint.html', course = course, new_checkpoint = True, courseID = int(courseID))

  def post(self, courseID):
    if valid_user():
      teacher = valid_user()
      course = existing_course(courseID = courseID, user = teacher)
      if course:        
        name = self.request.get('checkpoint_name')
        description = self.request.get('description')
        featured = self.request.get('featured_checkpoint')
        create_new_checkpoint(name = name, description = description, course = course, featured = featured)
        teacherID = teacher.key.id()
        delete_cached_course(courseID, teacherID)
    self.redirect('/course/%s' % courseID)

class editCheckpoint(MainHandler):
  def get(self, courseID, checkpointID):
    if valid_user():
      teacher = valid_user()
      course = existing_course(courseID = courseID, user = teacher)
      if course:
        self.render('edit_checkpoint.html', 
          course = course, 
          courseID = int(courseID),
          new_checkpoint = False, 
          checkpoint = get_single_checkpoint(course, checkpointID))

  def post(self, courseID, checkpointID):
    if valid_user():
      teacher = valid_user()
      course = existing_course(courseID = courseID, user = teacher)
      if course:        
        name = self.request.get('checkpoint_name')
        description = self.request.get('description')
        featured = self.request.get('featured_checkpoint')
        update_checkpoint(checkpointID = checkpointID, name = name, description = description, course=course, featured = featured)
        checkpoint = get_single_checkpoint(course, checkpointID)
        teacherID = teacher.key.id()
        delete_cached_course(courseID, teacherID)
    self.redirect('/course/%s' % courseID)

class singleBadge(MainHandler):
  def get(self, badgeID):
    if valid_user():
      self.render('single_badge.html', 
        badge = get_badge(valid_user(),badgeID), 
        achievement_status = achievement_status, 
        teacher=valid_user(),
        badges_active = 'active',
        get_checkpoints_for_badge = get_checkpoints_for_badge,
        active_course = self.request.get('active_course'),
        get_section_string = get_section_string,
        active_section = self.request.get('active_section'),
        get_registered_students = get_registered_students
        )

class singleCheckpoint(MainHandler):
  def get(self, courseID, checkpointID):
    if valid_user():
      teacher = valid_user()
      teacherID = teacher.key.id()
      html_cache_key = "html_checkpoint:%s_%s_%s" % (teacherID, courseID, checkpointID)
      cached_html = get_cached_html_page(html_cache_key)
      if cached_html:
        self.write(cached_html)
      else:
        course = existing_course(courseID, teacher)
        checkpoint = get_single_checkpoint(course, checkpointID)
        raw_html = self.render('single_checkpoint.html',  
          checkpoint = checkpoint, 
          badges = get_checkpoint_badges(checkpoint),
          registrations = get_registered_students(course),
          get_checkpoint_percent_completion = get_checkpoint_percent_completion,
          course= course,
          courseID = int(courseID), 
          checkpointID = int(checkpointID),
          badge_achieved = badge_achieved,
          section_string = get_section_string(course)
          )
        memcache.set(html_cache_key, raw_html)

class deleteCheckpoint(MainHandler):
  def get(self, courseID, checkpointID):
    if valid_user():
      teacher = valid_user()
      teacherID = teacher.key.id()
      course = existing_course(courseID, teacher)
      checkpoint = get_single_checkpoint(course, checkpointID)
      self.render('delete_checkpoint.html',
        checkpoint = checkpoint, 
        course = course
        )

  def post(self, courseID, checkpointID):
    if valid_user():
      delete_phrase = self.request.get('delete_phrase')
      if delete_phrase == 'Delete':
        course = existing_course(courseID, valid_user())
        checkpoint = get_single_checkpoint(course, checkpointID)
        checkpoint.key.delete()
        delete_cached_course(courseID, valid_user().key.id())
        self.redirect('/course/%s' % courseID)
      else:
        self.redirect('/delete_checkpoint/%s/%s?error=You did not type "Delete" correctly' % (courseID, checkpointID))
    
class teacherAccessRequest(MainHandler):
  def get(self):
    if valid_user():
      self.render('request_teacher_access.html')

  def post(self):
    if valid_user():
      code = self.request.get('teacher_code')
      if code == 'matt_damon':
        valid_user().teacher = True
        valid_user().put()
        self.redirect('/profile')
      else:
        self.redirect('/request_teacher_access?error=invalid code')

class awardMiniBadge(MainHandler):
  def get(self, badgeID, studentID, courseID):
    if valid_user():
      teacher = valid_user()
      course = existing_course(courseID, teacher)
      badge = get_badge(teacher,badgeID)
      new_achievement(
        teacher = teacher, 
        student = get_student(studentID), 
        badge = badge, 
        course = course,
        status = 'awarded'
        )
      for course_checkpoint_key in badge.checkpoints:
        checkpointID = course_checkpoint_key.split('_')[1]
        logging.info(checkpointID)
        delete_cached_percent_completion(checkpointID ,courseID, teacher.key.id(), studentID)
      self.redirect('/student_profile/%s/%s/teacher_view' % (studentID, courseID))

app = webapp2.WSGIApplication([
  ('/badge_creator', badgeCreator),
  ('/request_teacher_access', teacherAccessRequest),
  ('/badge_creator/(\w+)', badgeCreator),
  ('/edit_profile', changeUser),
  ('/student_profile/(\w+)/(\w+)', studentProfile),
  ('/student_profile/(\w+)/(\w+)/teacher_view', teacherViewStudentProfile),
  ('/student_badge/(\w+)/(\w+)/(\w+)/teacher_view', teacherViewStudentBadge),
  ('/complete_registration/(\w+)/(\w+)/(\w+)', completeRegistration),
  ('/link', link),
  ('/delete_checkpoint/(\w+)/(\w+)', deleteCheckpoint),
  ('/award_mini_badge/(\w+)/(\w+)/(\w+)', awardMiniBadge),
  ('/register', register),
  ('/profile', profile),
  ('/badges', listBadges),
  ('/badge/(\w+)', singleBadge),
  ('/course/(\w+)/checkpoint/(\w+)', singleCheckpoint),
  ('/student_badge/(\w+)/(\w+)/(\w+)', studentBadge),
  ('/edit_course', editCourse),
  ('/edit_course/(\w+)', editCourse),
  ('/achievementHandler', achievementHandler),
  ('/ajax/award_badge', ajaxBadgeHandler),
  ('/ajax/change_section', ajaxSectionHandler),
  ('/course/(\w+)/new_checkpoint', newCheckpoint),
  ('/course/(\w+)/edit_checkpoint/(\w+)', editCheckpoint),
  ('/course/(\w+)', course),
  ('/front', front),
  ('.*', home)
], debug=True)
