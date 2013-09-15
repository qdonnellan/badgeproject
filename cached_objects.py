from google.appengine.api import memcache
from database import *
from operator import attrgetter
from useful import valid_user



class student_checkpoint_class():
  def __init__(self, checkpoint, studentID):
    self.badges = []
    for badge in get_checkpoint_badges(checkpoint):
      self.badges.append(student_badge_class(badge, checkpoint, studentID))
    self.percent_complete = get_checkpoint_percent_completion(studentID, checkpoint)



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


def get_section_string(course):
  all_registrations = get_registered_students(course)
  sections = ''
  if all_registrations:
    for registration in all_registrations:
      if registration.section:
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

def get_student_checkpoint(checkpoint, studentID):
  logging.info('start get_student_checkpoint')
  student_checkpoint = student_checkpoint_class(checkpoint, studentID)
  logging.info('end get_student_checkpoint')
  return student_checkpoint

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

def get_checkpoint_id_list(courseID, teacherID):
  cache_key = "checkpoint_list_for:%s_%s" % (courseID, teacherID)
  cached_id_list = memcache.get(cache_key)
  if not cached_id_list:
    cached_id_list = []
    course = get_cached_course(courseID, teacherID)
    course_checkpoints = get_course_checkpoints(course.course)
    for checkpoint in course_checkpoints:
      cached_id_list.append(str(checkpoint.key.id()))
    memcache.set(cache_key, cached_id_list)
  return cached_id_list

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

def delete_cached_course(courseID, teacherID):
  cache_key = "html_course:%s_%s" % (teacherID, courseID)
  memcache.delete(cache_key)

def delete_cached_teacher_requests(courseID, teacherID):
  cache_key = "teacher_requests:%s_%s" % (courseID, teacherID)
  memcache.delete(cache_key)

def delete_cached_checkpoint(checkpointID, courseID, teacherID):
  cache_key = "checkpoint:%s_%s_%s" % (teacherID, courseID, checkpointID)
  memcache.delete(cache_key)
  delete_cached_html_page("html_%s" % cache_key)

def delete_cached_student_checkpoint(checkpointID, studentID, courseID, teacherID):
  cache_key = "checkpoint:%s_%s_%s_%s" % (teacherID, courseID, checkpointID, studentID)
  memcache.delete(cache_key)

def delete_all_cached_checkpoints(courseID, teacherID):
  cached_id_list = get_checkpoint_id_list(courseID, teacherID)
  logging.info(cached_id_list)
  for checkpointID in cached_id_list:
    delete_cached_checkpoint(checkpointID, courseID, teacherID)

def delete_cached_student_requests(courseID, studentID, teacherID):
  cache_key = "student_requests:%s_%s_%s" % (courseID, teacherID, studentID)
  memcache.delete(cache_key)

def get_cached_html_page(cache_key):
  cached_template = memcache.get(cache_key)
  if cached_template:
    return cached_template
  else:
    return None

def delete_cached_html_page(cache_key):
  memcache.delete(cache_key)




