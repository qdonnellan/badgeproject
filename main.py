import webapp2
from handlers import MainHandler
from icon_list import the_list
import re, logging
from google.appengine.api import users
from database import *
from ajax import *
from useful import valid_user
from cached_objects import *

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
        get_cached_checkpoints = get_cached_checkpoints)
  def post(self, badgeID=None):
    if valid_user() and valid_user().teacher:
      badgeID = edit_badge(
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

      for checkpoint in get_checkpoints_for_badge(get_badge(valid_user(), badgeID), valid_user()):
        courseID = checkpoint.key.parent().get().key.id()
        teacherID = valid_user().key.id()
        get_cached_checkpoint(checkpoint, courseID, teacherID, refresh = True, refresh_students = True)

      checkpointID = self.request.get('checkpointID')
      courseID = self.request.get('courseID')
      if checkpointID and courseID:
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
      if verify_unique_course_code(course_code,valid_user(), courseID = courseID):
        course = edit_course(course_name = course_name, course_code = course_code, courseID = courseID, user = valid_user())
        if courseID:
          get_cached_course(courseID, teacherID, refresh = True)
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
      teacherID = valid_user().key.id()
      course = get_cached_course(courseID, teacherID)
      self.render('course.html', 
        course = course,
        registrations = get_registered_students(course.course),
        checkpoints = get_cached_checkpoints(courseID, teacherID),
        teacher_requests = get_cached_teacher_requests(courseID, teacherID),
        courseID = int(courseID),
        active_tab = self.request.get('active_tab'))
    else:
      self.redirect('/front')

  def post(self, courseID):
    if valid_user():
      course_name = self.request.get('course_name')
      course_code = self.request.get('course_code')
      if verify_unique_course_code(course_code,valid_user(), courseID = courseID):
        course = edit_course(course_name = course_name, course_code = course_code, courseID = courseID, user = valid_user())
        get_cached_course(courseID, valid_user().key.id(), refresh = True)
        self.redirect('/course/%s?active_tab=settings' % courseID)
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
            get_cached_course(course.key.id(), teacher.key.id(), refresh = True)
          else:
            self.redirect('/register?error=invalid course code')
        else:
          self.redirect('/register?error=that teacher email does not exist in the system')
      else:
        self.redirect('/register?error=you cannot leave the teacher email field blank')

class changeSection(MainHandler):
  def get(self, courseID, studentID, section_number):
    if valid_user():
      if section_number in '12345678':
        course = existing_course(courseID, valid_user())
        change_section_number(course, studentID, section_number)
    self.redirect('/course/%s?active_tab=students' % courseID)
    get_cached_course(courseID, valid_user().key.id(), refresh = True)

class completeRegistration(MainHandler):
  def get(self, courseID, studentID, action):
    if valid_user():
      edit_registration(courseID = courseID, teacher = valid_user(), action = action, studentID = studentID)
      get_cached_course(courseID, valid_user().key.id(), refresh = True)
    self.redirect('/course/%s?active_tab=students' % courseID)

class studentProfile(MainHandler):
  def get(self, teacherID, courseID):
    if valid_user():
      if courseID:
        self.render('course.html', 
          course = get_cached_course(courseID, teacherID),
          checkpoints = get_cached_checkpoints(courseID, teacherID),
          get_student_checkpoint = get_cached_student_checkpoint,
          teacherID=int(teacherID), 
          courseID = int(courseID),
          student_profile = True, 
          student = valid_user(),
          student_requests = get_cached_student_requests(courseID, valid_user().key.id(), teacherID)
          )
      else:
        self.write('You are not registered for this course...')

class teacherViewStudentProfile(MainHandler):
  def get(self, studentID, courseID):
    if valid_user():
      if course:
        teacherID = valid_user().key.id()
        self.render('course.html', 
          course = get_cached_course(courseID, teacherID),
          checkpoints = get_cached_checkpoints(courseID, teacherID),
          get_student_checkpoint = get_cached_student_checkpoint,
          teacherID= int(teacherID), 
          courseID = int(courseID),
          student = get_student(studentID),
          teacher_view_student_profile = True,
          active_tab = self.request.get('active_tab'),
          student_requests = get_cached_student_requests(courseID, studentID, teacherID)
          )

class studentBadge(MainHandler):
  def get(self, teacherID, courseID, badgeID):
    if valid_user():
      course = get_student_course(courseID = courseID, student = valid_user(), teacherID = teacherID)
      teacher = get_teacher(teacherID)
      student = valid_user()
      badge = get_badge(teacher, badgeID)
      this_badge_status = achievement_status(student = student, course = course, badge = badge, teacher = teacher)
      self.render('single_badge.html', 
        badge = badge,
        achievement_status = this_badge_status,
        student_badge = True,
        courseID = course.key.id(),
        course = course, 
        teacher = teacher,
        teacherID = int(teacherID),
        get_checkpoints_for_badge = get_checkpoints_for_badge
        )

class teacherViewStudentBadge(MainHandler):
  def get(self, studentID, courseID, badgeID):
    if valid_user():
      course = get_user_courses(valid_user(), courseID)
      if course:
        student = get_student(studentID)
        teacher = valid_user()
        badge = get_badge(valid_user(), badgeID)
        this_badge_status = achievement_status(student = student, course = course, badge = badge, teacher = teacher)
        self.render('single_badge.html',
          badge = badge,
          achievement_status = this_badge_status,
          teacher_view_student_badge = True,
          student = student,
          course = course, 
          courseID = course.key.id(),
          teacher = teacher,
          teacherID = int(teacher.key.id()),
          get_checkpoints_for_badge = get_checkpoints_for_badge, 
          evidence = get_evidence(badge, studentID)
          )

  def post(self, studentID, courseID, badgeID):
    if valid_user():
      course = get_user_courses(valid_user(), courseID)
      if courseID:
        badge = get_badge(valid_user(), badgeID)
        content = self.request.get('content')
        create_evidence(studentID, badge, content)
    self.redirect('/student_badge/%s/%s/%s/teacher_view' % (studentID, courseID, badgeID))

class teacherViewAwardBadge(MainHandler):
  def get(self, studentID, courseID, badgeID, status):
    if valid_user():
      if status in ['awarded', 'revoked', 'denied']:
        course = existing_course(courseID, valid_user())
        badge = get_badge(valid_user(),badgeID)
        new_achievement(
          teacher = valid_user(), 
          student = get_student(studentID), 
          badge = badge, 
          course = course,
          status = status
          )
        teacherID = valid_user().key.id()
        get_cached_teacher_requests(courseID, teacherID, refresh = True)
        for checkpoint in get_checkpoints_for_badge(badge, valid_user()):
          cached_checkpoint = get_cached_checkpoint(checkpoint, courseID, teacherID)
          get_cached_student_checkpoint(cached_checkpoint, studentID, refresh = True)
        get_cached_course(courseID, teacherID, refresh = True)
        get_cached_student_requests(courseID, studentID, teacherID, refresh = True)
        student_requests = get_cached_student_requests(courseID, studentID, teacherID)
        if self.request.get('back_to_course') == 'true':
          self.redirect('/course/%s?active_tab=requests' % courseID)
        elif self.request.get('single_badge') == 'true':
          self.redirect('/badge/%s?active_course=%s' % (badgeID, courseID))
        else:
          self.redirect('/student_badge/%s/%s/%s/teacher_view' % (studentID, courseID, badgeID))

class requestBadge(MainHandler):
  def get(self, teacherID, courseID, badgeID):
    if valid_user():
      teacher = get_teacher(teacherID)
      student = valid_user()
      badge = get_badge(teacher, badgeID)
      course = existing_course(courseID, teacher)
      edit_achievement(student, badge, teacher, course)
      get_cached_teacher_requests(courseID, teacherID, refresh = True)
      get_cached_student_requests(courseID, valid_user().key.id(), teacherID, refresh = True)
      self.redirect('/student_badge/%s/%s/%s' % (teacherID, courseID, badgeID))
      get_cached_course(courseID, teacherID, refresh = True)


class newCheckpoint(MainHandler):
  def get(self, courseID):
    if valid_user():
      course = existing_course(courseID = courseID, user = valid_user())
      if course:
        self.render('edit_checkpoint.html', course = course, new_checkpoint = True, courseID = int(courseID))

  def post(self, courseID):
    if valid_user():
      course = existing_course(courseID = courseID, user = valid_user())
      if course:        
        name = self.request.get('checkpoint_name')
        description = self.request.get('description')
        featured = self.request.get('featured_checkpoint')
        create_new_checkpoint(name = name, description = description, course = course, featured = featured)
        teacherID = valid_user().key.id()
        get_cached_course(courseID, teacherID, refresh = True)
    self.redirect('/course/%s' % courseID)

class editCheckpoint(MainHandler):
  def get(self, courseID, checkpointID):
    if valid_user():
      course = existing_course(courseID = courseID, user = valid_user())
      if course:
        self.render('edit_checkpoint.html', 
          course = course, 
          courseID = int(courseID),
          new_checkpoint = False, 
          checkpoint = get_single_checkpoint(course, checkpointID))

  def post(self, courseID, checkpointID):
    if valid_user():
      course = existing_course(courseID = courseID, user = valid_user())
      if course:        
        name = self.request.get('checkpoint_name')
        description = self.request.get('description')
        featured = self.request.get('featured_checkpoint')
        update_checkpoint(checkpointID = checkpointID, name = name, description = description, course=course, featured = featured)
        checkpoint = get_single_checkpoint(course, checkpointID)
        teacherID = valid_user().key.id()
        get_cached_checkpoint(checkpoint, courseID, teacherID, refresh = True)
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
        active_course = self.request.get('active_course')
        )

class singleCheckpoint(MainHandler):
  def get(self, courseID, checkpointID):
    if valid_user():
      teacherID = valid_user().key.id()
      course = get_cached_course(courseID, teacherID)
      checkpoint = get_single_checkpoint(course.course, checkpointID)
      checkpoint = get_cached_checkpoint(checkpoint, courseID, teacherID)
      self.render('single_checkpoint.html',  
        checkpoint = checkpoint, 
        course= course,
        courseID = int(courseID), 
        checkpointID = int(checkpointID),
        badge_achieved = badge_achieved,
        get_student_checkpoint = get_cached_student_checkpoint
        )

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


app = webapp2.WSGIApplication([
  ('/badge_creator', badgeCreator),
  ('/request_teacher_access', teacherAccessRequest),
  ('/badge_creator/(\w+)', badgeCreator),
  ('/edit_profile', changeUser),
  ('/student_profile/(\w+)/(\w+)', studentProfile),
  ('/student_profile/(\w+)/(\w+)/teacher_view', teacherViewStudentProfile),
  ('/student_badge/(\w+)/(\w+)/(\w+)/teacher_view', teacherViewStudentBadge),
  ('/student_badge/(\w+)/(\w+)/(\w+)/teacher_view/award/(\w+)', teacherViewAwardBadge),
  #('/student_course/(\w+)', studentCourse),
  ('/complete_registration/(\w+)/(\w+)/(\w+)', completeRegistration),
  ('/link', link),
  ('/change_section/(\w+)/(\w+)/section/(\w+)', changeSection),
  ('/register', register),
  ('/profile', profile),
  ('/badges', listBadges),
  ('/badge/(\w+)', singleBadge),
  ('/course/(\w+)/checkpoint/(\w+)', singleCheckpoint),
  ('/student_badge/(\w+)/(\w+)/(\w+)', studentBadge),
  ('/request_badge/(\w+)/(\w+)/(\w+)', requestBadge),
  ('/edit_course', editCourse),
  ('/edit_course/(\w+)', editCourse),
  ('/achievementHandler', achievementHandler),
  ('/course/(\w+)/new_checkpoint', newCheckpoint),
  ('/course/(\w+)/edit_checkpoint/(\w+)', editCheckpoint),
  ('/course/(\w+)', course),
  ('/front', front),
  ('.*', home)
], debug=False)
