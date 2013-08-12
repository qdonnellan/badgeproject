from google.appengine.api import memcache
from database import *
from operator import attrgetter
from useful import valid_user

class course_class():
  def __init__(self, courseID, teacherID): 
    teacher = get_teacher(teacherID)
    course = existing_course(courseID, teacher)
    self.course = course
    self.name = course.course_name
    self.code = course.course_code
    self.teacher = teacher
    self.enrolled_students = get_enrolled_students(course)
    self.registrations = get_registered_students(course)
    self.number_of_badge_requests = get_number_of_badge_requests(course)
    self.number_of_pending_registrations = get_number_of_pending_registrations(course)
    self.number_of_notifications = self.number_of_pending_registrations + self.number_of_badge_requests

class checkpoint_class():
  def __init__(self, checkpoint):
    self.checkpoint = checkpoint
    self.name = checkpoint.name
    self.featured = checkpoint.featured
    self.description = checkpoint.description
    course = checkpoint.key.parent().get()
    teacher = course.key.parent().get()
    all_teacher_badges = get_all_badges(teacher)
    self.badges = []
    for badge in all_teacher_badges:
      if badge_in_checkpoint(badge, checkpoint):
        self.badges.append(badge)

class student_checkpoint_class():
  def __init__(self, checkpoint, studentID):
    self.badges = []
    for badge in checkpoint.badges:
      self.badges.append(student_badge_class(badge, checkpoint.checkpoint, studentID))
    self.percent_complete = get_checkpoint_percent_completion(studentID, checkpoint)


class registered_student_class():
  def __init__(self, registration_entry):
    self.student = get_student(registration_entry.student_id)
    self.registration = registration_entry
    self.status = registration_entry.status
    if self.status in ['revoked', 'denied', 'pending', None, '']:
      self.section = '0'
    else:
      self.section = registration_entry.section
    self.student_id = registration_entry.student_id
    formalName = self.student.formalName
    if ' ' in formalName:
      last_name = formalName.split(' ')[-1]
    else:
      last_name = formalName
    self.name = last_name

class course_requests_class():
  def __init__(self, courseID, teacherID = None, studentID = None):
    self.requests = []
    requests = None
    if teacherID:
      teacher = get_teacher(teacherID)
      course = existing_course(courseID, teacher)
      if course:
        requests = get_badge_requests(course)
    if studentID and teacherID:
      student = get_student(studentID)
      requests = get_badge_requests(course, student)
    if requests:
      for request in requests:
        self.requests.append(request_class(request, teacher))
      self.requests.sort(key = attrgetter('last_modified_raw'), reverse = True)
    self.number = get_number_of_badge_requests(course)

class request_class():
  def __init__(self, request, teacher):
    self.request = request
    self.student = request.key.parent().get()
    self.status = request.status
    self.badge_id = request.badge_id
    self.badge = get_badge(teacher, request.badge_id)
    self.last_modified = request.last_modified.strftime("%d %B %Y")
    self.last_modified_raw = request.last_modified

class student_badge_class():
  def __init__(self, badge, checkpoint, studentID):
    self.badge = badge
    self.icon_color = badge.icon_color
    self.background = badge.background
    self.icon = badge.icon
    self.name = badge.name
    self.requirement = badge.requirement
    self.value = badge.value
    course = checkpoint.key.parent().get()
    student = get_student(studentID)
    self.status = achievement_status(student, badge, course.key.parent().get(), course)

def get_registered_students(course):
  all_registrations = []
  registrations = get_registrations(course)
  if registrations:
    for item in registrations:
      all_registrations.append(registered_student_class(item))
  if all_registrations == []:
    return None
  else:
    all_registrations = sorted(all_registrations, key = attrgetter('name'), reverse = False)
    all_registrations = sorted(all_registrations, key = attrgetter('section'), reverse = False)
    return all_registrations

def get_section_string(course):
  all_registrations = get_registered_students(course)
  sections = ''
  for registration in all_registrations:
    if (registration.section in '12345678') and (registration.section not in sections):
      sections += registration.section
  return sections

def get_cached_checkpoint(checkpoint, courseID, teacherID, refresh = False, refresh_students = False):
  if checkpoint:
    cache_key = "checkpoint:%s_%s_%s" % (teacherID, courseID, checkpoint.key.id())
    cached_checkpoint = memcache.get(cache_key)
    if refresh or not cached_checkpoint:
      cached_checkpoint = checkpoint_class(checkpoint)
      memcache.set(cache_key, cached_checkpoint)
    if refresh_students:
      course = get_cached_course(courseID, teacherID)
      for student in course.enrolled_students:
        get_cached_student_checkpoint(cached_checkpoint, student.key.id(), refresh = True)
    return cached_checkpoint

def get_cached_teacher_requests(courseID, teacherID, refresh = False):
  cache_key = "teacher_requests:%s_%s" % (courseID, teacherID)
  cached_requests = memcache.get(cache_key)
  if refresh or not cached_requests:
    cached_requests = course_requests_class(courseID, teacherID = teacherID)
    memcache.set(cache_key, cached_requests)
  return cached_requests

def get_cached_student_requests(courseID, studentID, teacherID, refresh = False):
  cache_key = "student_requests:%s_%s_%s" % (courseID, teacherID, studentID)
  cached_requests = memcache.get(cache_key)
  if refresh or not cached_requests:
    cached_requests = course_requests_class(courseID, teacherID = teacherID, studentID = studentID)
    memcache.set(cache_key, cached_requests)
  return cached_requests


def get_cached_student_checkpoint(checkpoint, studentID, refresh = False):
  if checkpoint:
    course = checkpoint.checkpoint.key.parent().get()
    teacher = course.key.parent().get()
    cache_key = "checkpoint:%s_%s_%s_%s" % (teacher.key.id(), course.key.id(), checkpoint.checkpoint.key.id(), studentID)
    cached_student_checkpoint = memcache.get(cache_key)
    if refresh or not cached_student_checkpoint:
      cached_checkpoint = get_cached_checkpoint(checkpoint.checkpoint, course.key.id(), teacher.key.id())
      cached_student_checkpoint = student_checkpoint_class(cached_checkpoint, studentID)
      memcache.set(cache_key, cached_student_checkpoint)
    return cached_student_checkpoint

def get_cached_checkpoints(courseID, teacherID):
  course = get_cached_course(courseID, teacherID)
  course_checkpoints = get_course_checkpoints(course.course)
  cached_checkpoints = []
  for checkpoint in course_checkpoints:
    cached_checkpoints.append(get_cached_checkpoint(checkpoint, courseID, teacherID))
  if cached_checkpoints == []:
    cached_checkpoints = None
  return cached_checkpoints

def get_cached_course(courseID, teacherID, refresh=False):
  cache_key = "course:%s_%s" % (teacherID, courseID)
  cached_course = memcache.get(cache_key)
  if refresh or not cached_course:
    cached_course = course_class(courseID, teacherID)
    memcache.set(cache_key, cached_course)
  return cached_course

def reset_all_students_cache(course):
  if course:
    for student in get_enrolled_students(course):
      teacher = course.key.parent().get()
      cache_key = "course:%s_%s_%s" % (teacher.key.id(), course.key.id(), student.key.id())
      memcache.delete(cache_key)

def get_cached_user_courses(user):
  if user:
    all_courses = get_user_courses(user)
    cached_courses = []
    if all_courses:
      for course in all_courses:
        cached_courses.append(get_cached_course(course.key.id(), user.key.id()))
      return cached_courses
    else:
      return None
  else:
    return None




