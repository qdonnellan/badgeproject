from google.appengine.api import memcache
from database import *

class course_class():
  def __init__(self, course, studentID = None):
    self.course = course
    self.name = course.course_name
    self.code = course.course_code
    self.teacher = course.key.parent().get()
    if studentID:
      self.student = get_student(studentID)
    self.checkpoints = []
    for indiv_checkpoint in get_course_checkpoints(course):
      self.checkpoints.append(get_cached_checkpoint(indiv_checkpoint, studentID))

    if studentID:
      requests = get_badge_requests(course, self.student)
    else:
      requests = get_badge_requests(course)
    if requests:
      self.requests = []
      for request in requests:
        self.requests.append(request_class(request, self.teacher))
    else:
      self.requests = None
    self.enrolled_students = get_enrolled_students(course)
    self.registrations = get_registrations(course)
    self.number_of_badge_requests = get_number_of_badge_requests(course)
    self.number_of_pending_registrations = get_number_of_pending_registrations(course)
    self.number_of_notifications = self.number_of_pending_registrations + self.number_of_badge_requests

class checkpoint_class():
  def __init__(self, checkpoint, studentID = None):
    self.checkpoint = checkpoint
    self.name = checkpoint.name
    self.featured = checkpoint.featured
    self.description = checkpoint.description
    course = checkpoint.key.parent().get()
    teacher = course.key.parent().get()
    all_teacher_badges = get_all_badges(teacher)
    self.badges = []
    for badge in all_teacher_badges:
      if studentID:
        logging.info('student does exist!')
        if badge_in_checkpoint(badge, checkpoint):
          logging.info('bla bla bla')
          self.badges.append(student_badge_class(badge, checkpoint, studentID))
      else:
        if badge_in_checkpoint(badge, checkpoint):
          self.badges.append(badge)
    if studentID:
      student = get_student(studentID)
      self.percent_complete = get_checkpoint_percent_completion(course, student, all_teacher_badges, checkpoint)

class request_class():
  def __init__(self, request, teacher):
    self.status = request.status
    self.badge_id = request.badge_id
    self.badge = get_badge(teacher, request.badge_id)

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

def get_cached_checkpoint(checkpoint, studentID = None, refresh = False):
  course = checkpoint.key.parent().get()
  teacher = course.key.parent().get()
  if studentID:
    cache_key = "checkpoint:%s_%s_%s_%s" % (teacher.key.id(), course.key.id(), checkpoint.key.id(), studentID)
  else:
    cache_key = "checkpoint:%s_%s_%s" % (teacher.key.id(), course.key.id(), checkpoint.key.id())
  cached_checkpoint = memcache.get(cache_key)
  if refresh or not cached_checkpoint:
    cached_checkpoint = checkpoint_class(checkpoint=checkpoint, studentID=studentID)
    memcache.set(cache_key, cached_checkpoint)
    if not studentID:
      for student in get_enrolled_students(course):
        cache_key = "checkpoint:%s_%s_%s_%s" % (teacher.key.id(), course.key.id(), checkpoint.key.id(), student.key.id())
        memcache.delete(cache_key)
  return cached_checkpoint


def get_cached_course(course, studentID=None, refresh=False):
  teacher = course.key.parent().get()
  if studentID:
    cache_key = "course:%s_%s_%s" % (teacher.key.id(), course.key.id(), studentID)
  else:
    cache_key = "course:%s_%s" % (teacher.key.id(), course.key.id())

  cached_course = memcache.get(cache_key)

  if refresh or not cached_course:
    reset_all_students_cache(course)
    cached_course = course_class(course, studentID)
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
        cached_courses.append(get_cached_course(course))

      return cached_courses
    else:
      return None
  else:
    return None




