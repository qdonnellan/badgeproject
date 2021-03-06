from google.appengine.ext import ndb
from google.appengine.api import memcache
import logging
from operator import attrgetter
import re
import json 

class User(ndb.Model):
  google_id = ndb.StringProperty(required = True)
  email = ndb.StringProperty(required = True)
  name = ndb.StringProperty(required = False)
  formalName = ndb.StringProperty(required = False) #deprecated
  teacher = ndb.BooleanProperty(default = False)
  name_lower = ndb.ComputedProperty(lambda self: self.name.lower())

class Course(ndb.Model):
  name = ndb.StringProperty(required = True)
  course_name = ndb.StringProperty(required = False) #deprecated
  code = ndb.StringProperty(required = True)
  course_code = ndb.StringProperty(required = False) #deprecated

class Checkpoint(ndb.Model):
  name = ndb.StringProperty(required = False)
  description = ndb.TextProperty(required = False)
  featured = ndb.BooleanProperty(default = False)
  badges = ndb.JsonProperty(required = False)
  progress = ndb.JsonProperty(required = False)

class Registrations(ndb.Model):
  student_id = ndb.StringProperty(required = True)
  status = ndb.StringProperty(required = True)
  section = ndb.StringProperty(required = False)

class Badge(ndb.Model):
  icon = ndb.StringProperty(required = False)
  icon_color = ndb.StringProperty(required = False)
  border_color = ndb.StringProperty(required = False)
  background = ndb.StringProperty(required = False)
  name = ndb.StringProperty(required = False)
  requirement = ndb.TextProperty(required = False)
  value = ndb.IntegerProperty(required = False)
  checkpoints = ndb.JsonProperty(required = False)

class Achievement(ndb.Model):
  teacher_id = ndb.StringProperty(required = True)
  course_id = ndb.StringProperty(required = True)
  badge_id = ndb.StringProperty(required = True)
  status = ndb.StringProperty(required = True)
  last_modified = ndb.DateTimeProperty(auto_now = True)

class Evidence(ndb.Model):
  content = ndb.TextProperty(required = False)
  studentID = ndb.StringProperty(required = True)
  created = ndb.DateTimeProperty(auto_now_add = True)
  teacher = ndb.BooleanProperty(default = False)
  last_modified = ndb.DateTimeProperty(auto_now = True)


def existing_user(google_user):
  if google_user:
    user_object = User.query(User.google_id == str(google_user.user_id())).get()
    if user_object:
      return user_object
    else:
      return None
  else:
    return None

def new_user(google_user, formalName):
  if not existing_user(google_user):
    new_user_object = User(google_id = str(google_user.user_id()), name = formalName, email = google_user.email())
    new_user_object.put()

def edit_user(user, formalName):
  if user:
    user.name = formalName
    user.put()

def existing_course(courseID, user):
  if courseID:
    theKey = ndb.Key(Course, int(courseID), parent = user.key)
    return theKey.get()
  else:
    return None

def verify_unique_course_code(course_code, user, courseID=None):
  verification = True
  user_courses = get_user_courses(user)
  if user_courses:
    for course in user_courses:
      if course_code == course.code:
        if not courseID:
          verification = False
        elif str(courseID) != str(course.key.id()):
          verification = False
  return verification

def edit_course(course_name, course_code, courseID, user):
  course_object = existing_course(courseID, user)
  if course_object:
    course_object.name = course_name
    course_object.code = course_code
    course_object.put()
  else:
    course_object = Course(name = course_name, code = course_code, parent = user.key)
    course_object.put()

  return course_object

def get_user_courses(user, courseID = None):
  if user:
    if courseID:
      return existing_course(courseID, user)
    else:
      courses = Course.query(ancestor = user.key)
      total = 0
      for course in courses:
        total+=1
      if total == 0:
        return None
      else:
        return courses
  else:
    return None

def get_user_by_email(email):
  return User.query(User.email == email).get()

def register_for_course(student, teacher, course_code):
  the_course = Course.query(Course.code == course_code, ancestor = teacher.key).get()
  if the_course:
    existing_registration = Registrations.query(Registrations.student_id == str(student.key.id()), ancestor = the_course.key).get()
    if not existing_registration:
      new_registration = Registrations(student_id = str(student.key.id()), status = "pending", parent = the_course.key)
      new_registration.put()
      return True
    else:
      return False
  else:
    return False

def get_course_by_code(teacher, course_code):
  return Course.query(Course.code == course_code, ancestor = teacher.key).get()

def edit_registration(courseID, teacher, studentID, action, new=False):
  course = existing_course(courseID, teacher)
  if course:
    registration_object = Registrations.query(Registrations.student_id == studentID, ancestor = course.key).get()
    if registration_object:
      registration_object.status = action
      registration_object.put()

    if new:
      for checkpoint in get_course_checkpoints(course):
        checkpointID = checkpoint.key.id()
        teacherID = teacher.key.id()
        update_checkpoint_progress(studentID, 'init_progress', checkpointID, courseID, teacherID, 'blank')

def change_section_number(course, studentID, section_number):
  if course:
    registration_object = Registrations.query(Registrations.student_id == studentID, ancestor = course.key).get()
    if registration_object:
      registration_object.section = section_number
      registration_object.put()

def get_registrations(course):
  total_registrations = Registrations.query(ancestor = course.key)
  if total_registrations.count() > 0:
    return total_registrations
  else:
    return None

class registered_student_class():
  def __init__(self, registration_entry):
    self.student = get_student(registration_entry.student_id)
    self.registration = registration_entry
    self.status = registration_entry.status
    if self.status in ['revoked', 'denied', 'pending', None, '']:
      self.section = '0'
    else:
      self.section = registration_entry.section
    self.student_id = str(registration_entry.student_id)
    formalName = self.student.name
    if ' ' in formalName:
      last_name = formalName.split(' ')[-1]
    else:
      last_name = formalName
    self.name = last_name

def get_registered_students(course):
  logging.info('start get_registered_students')
  all_registrations = []
  registrations = get_registrations(course)
  if registrations:
    for item in registrations:
      all_registrations.append(registered_student_class(item))
  if all_registrations == []:
    logging.info('end get_registered_students')
    return None
  else:
    all_registrations = sorted(all_registrations, key = attrgetter('name'), reverse = False)
    all_registrations = sorted(all_registrations, key = attrgetter('section'), reverse = False)
    logging.info('end get_registered_students')
    return all_registrations

def get_number_of_pending_registrations(course):
  logging.info('start get_number_of_pending_registrations')
  total_registrations = get_registrations(course)
  total = 0
  if total_registrations:
    for item in total_registrations:
      if item.status == 'pending':
        total += 1
  logging.info('end get_number_of_pending_registrations')
  return total


def get_student_course(courseID, student, teacherID):
  teacher = ndb.Key(User, int(teacherID)).get()
  course = existing_course(courseID, teacher)
  registration = Registrations.query(Registrations.student_id == str(student.key.id()), ancestor = course.key).get()
  if registration is not None and registration.status == "approved":
    return course
  else:
    return None

def get_enrolled_students(course):
  approved_registrations = Registrations.query(Registrations.status == "approved", ancestor = course.key)
  students = []
  for registration in approved_registrations:
    students.append(get_student(registration.student_id))
  return students

def get_enrolled_courses(student):
  if student:
    registrations = Registrations.query(Registrations.student_id == str(student.key.id()))
    courses = []
    for item in registrations:
      courses.append({"course": item.key.parent().get(), "status" : item.status})
    if courses == []:
      return None
    else:
      return courses
  else:
    return None

def get_student(studentID):
  return ndb.Key(User, int(studentID)).get()

def get_teacher(teacherID):
  return ndb.Key(User, int(teacherID)).get()

def edit_badge(teacher, icon, icon_color, border_color, background, name, requirement, value, checkpoints, badgeID = None):
  if value.isdigit():
    value = int(value)
  else:
    value = 1
  badge_checkpoints = []
  if checkpoints:
    for item in checkpoints:
      badge_checkpoints.append(item)
  if badgeID:
    the_badge = ndb.Key(Badge, int(badgeID), parent = teacher.key).get()    
    the_badge.populate(
        icon = icon,
        icon_color = icon_color, 
        border_color = border_color, 
        background = background, 
        name = name,
        requirement = requirement, 
        value = value,
        checkpoints = badge_checkpoints
      )
    the_badge.put()
  else:
    the_badge = Badge(
        icon = icon,
        icon_color = icon_color, 
        border_color = border_color, 
        background = background, 
        name = name,
        requirement = requirement, 
        value = value,
        parent = teacher.key,
        checkpoints = badge_checkpoints
      )
    key = the_badge.put()
    badgeID = key.id()
  return badgeID

def get_badge(teacher=None, badgeID = None):
  logging.info("start get_badge")
  if badgeID and teacher:
    the_badge = ndb.Key(Badge, int(badgeID), parent = teacher.key).get()
  else:
    the_badge = default_badge()
  logging.info('end get_badge')
  return the_badge

class default_badge():
  icon = "globe"
  icon_color = "blue" 
  border_color = "#121212"
  background = "#f6f6f6"
  name = ''
  requirement = '' 
  value = ''
  checkpoints = []

def add_badge_to_checkpoint(badgeID, checkpointID, courseID, teacherID):
  teacher = get_teacher(teacherID)
  course = existing_course(courseID, teacher)
  checkpoint = get_single_checkpoint(course, checkpointID)
  badge = get_badge(teacher, badgeID)
  badge_dict = {
    'icon' : badge.icon,
    'icon_color' : badge.icon_color,
    'border_color' : badge.border_color,
    'background' : badge.background,
    'name' : badge.name,
    'requirement' : badge.requirement,
    'value' : badge.value
  }
  badgeID = str(badge.key.id())
  badges = checkpoint.badges
  if not badges:
    badges = {}
  badges[badgeID] = badge_dict
  checkpoint.badges = badges
  checkpoint.put()
  logging.info('just added this badge')

def remove_badge_from_checkpoint(badgeID, checkpointID, courseID, teacherID):
  teacher = get_teacher(teacherID)
  course = existing_course(courseID, teacher)
  checkpoint = get_single_checkpoint(course, checkpointID)
  badge = get_badge(teacher, badgeID)
  badgeID = str(badge.key.id())
  badges = checkpoint.badges
  del badges[badgeID]
  checkpoint.badges = badges
  checkpoint.put()

def update_checkpoint_progress(studentID, badgeID, checkpointID, courseID, teacherID, new_progress):
  teacher = get_teacher(teacherID)
  course = existing_course(courseID, teacher)
  checkpoint = get_single_checkpoint(course, checkpointID)
  progress = checkpoint.progress
  if not progress:
    progress = {}
  if studentID in progress:
    student_progress = progress[studentID]
  else:
    student_progress = {}
  student_progress[badgeID] = new_progress
  progress[studentID] = student_progress

  #calculate the percent completion for this student
  total_value = 0
  student_value = 0
  for badgeID in checkpoint.badges:
    badge_value = checkpoint.badges[badgeID]['value']
    total_value += badge_value
    if badgeID in student_progress:
      if student_progress[badgeID] == 'awarded':
        student_value += badge_value
  if total_value == 0:
    percent = 0
  else:
    percent = (100.0 * student_value) / total_value
  student_progress['percent_complete'] = int(percent)
  progress[studentID] = student_progress

  checkpoint.progress = progress
  checkpoint.put()

def update_percent_completions(checkpointID, courseID, teacherID):
  teacher = get_teacher(teacherID)
  course = existing_course(courseID, teacher)
  checkpoint = get_single_checkpoint(course, checkpointID)
  progress = checkpoint.progress
  for studentID in progress:
    student_progress = progress[studentID]
    total_value = 0
    student_value = 0
    for badgeID in checkpoint.badges:
      badge_value = checkpoint.badges[badgeID]['value']
      total_value += badge_value
      if badgeID in student_progress:
        if student_progress[badgeID] == 'awarded':
          student_value += badge_value
    if total_value == 0:
      percent = 0
    else:
      percent = (100.0 * student_value) / total_value
    student_progress['percent_complete'] = int(percent)
    progress[studentID] = student_progress

  checkpoint.progress = progress
  checkpoint.put()

def get_all_badges(teacher):
  return Badge.query(ancestor = teacher.key).order(Badge.name)

def create_new_checkpoint(name, description, course, featured):
  if featured == 'true':
    featured = True
  else:
    featured = False
  new_checkpoint = Checkpoint(
    name= name, 
    description = description, 
    featured = featured, 
    progress = {},
    parent = course.key)
  new_checkpoint.put()

def update_checkpoint(name, description, course, checkpointID, featured):
  if featured == 'true':
    featured = True
  else:
    featured = False
  the_checkpoint = get_single_checkpoint(course, checkpointID)
  if the_checkpoint:
    the_checkpoint.name = name
    the_checkpoint.featured = featured
    the_checkpoint.description = description
    the_checkpoint.put()

def get_course_checkpoints(course):
  logging.info('start get_course_checkpoints')
  checkpoints = Checkpoint.query(ancestor = course.key)
  if checkpoints:
    logging.info('end get_course_checkpoints')
    return sort_by_name(checkpoints)
  else:
    logging.info('end get_course_checkpoints')
    return None

def get_single_checkpoint(course, checkpointID):
  the_checkpoint = ndb.Key(Checkpoint, int(checkpointID), parent = course.key).get()
  return the_checkpoint

def new_achievement(student, teacher, badge, course, status):
  the_achievement = fetch_achievement(student, badge, teacher, course)
  if the_achievement:
    the_achievement.populate(status = status)
  else:
    if student:
      the_achievement = Achievement(
        teacher_id = str(teacher.key.id()), 
        badge_id = str(badge.key.id()),
        course_id = str(course.key.id()),
        status = status,
        parent = student.key
        )
  the_achievement.put()

def fetch_achievement(student, badge, teacher, course):
  the_achievement = Achievement.query(
    Achievement.teacher_id == str(teacher.key.id()), 
    Achievement.course_id == str(course.key.id()),
    Achievement.badge_id == str(badge.key.id()),
    ancestor = student.key)
  return the_achievement.get()

def edit_achievement(student, badge, teacher, course):
  the_achievement = fetch_achievement(student, badge, teacher, course)
  if the_achievement:
    if the_achievement.status != 'awarded':
      the_achievement.status = 'requested'
      the_achievement.put()
  else:
    new_achievement(student, teacher, badge, course, "requested")

def achievement_status(student, badge, teacher, course):
  the_achievement = fetch_achievement(student, badge, teacher, course)
  if the_achievement:
    return the_achievement.status
  else:
    return 'Not yet obtained'

def badge_achieved(badge, course, student):
  teacher = course.key.parent().get()
  the_achievement = fetch_achievement(student, badge, teacher, course)
  if the_achievement and the_achievement.status == 'awarded':
    return True
  else:
    return False

def user_is_teacher(course, user):
  if user.teacher:
    if user.key.id() == course.key.parent().get().key.id():
      return True
    else:
      return False
  else:
    return False

def get_checkpoint_percent_completion(studentID, checkpoint):
  logging.info('start get_checkpoint_percent_completion')
  studentID = str(studentID)
  course = checkpoint.key.parent().get()
  teacher = course.key.parent().get()
  cache_key = 'percent_complete_dict:%s_%s_%s' % (teacher.key.id(), course.key.id(), checkpoint.key.id())
  percent_complete_dict = memcache.get(cache_key)
  if not percent_complete_dict:
    percent_complete_dict = {}
  if studentID in percent_complete_dict:
    percent_complete = percent_complete_dict[studentID]
  else:
    total_possible_points = 0
    student_points = 0
    student = get_student(studentID)
    for badge in get_checkpoint_badges(checkpoint):
      total_possible_points += badge.value
      if achievement_status(student, badge, course.key.parent().get(), course) == 'awarded':
        student_points += badge.value
    if total_possible_points == 0:
      raw_score = 0
    else:
      raw_score = (100.0 * student_points) / total_possible_points
    percent_complete = int(raw_score)
    percent_complete_dict[studentID] = percent_complete
    memcache.set(cache_key, percent_complete_dict)
  logging.info('end get_checkpoint_percent_completion')
  return percent_complete

def get_checkpoint_badges(checkpoint):
  logging.info('start get_checkpoint_badges')
  course = checkpoint.key.parent().get()
  teacher = course.key.parent().get()
  cache_key = "badges_for_checkpoint:%s_%s_%s" % (teacher.key.id(), course.key.id(), checkpoint.key.id())
  badges = memcache.get(cache_key)
  if not badges:
    all_teacher_badges = get_all_badges(teacher)
    badges = []
    for badge in all_teacher_badges:
      if badge_in_checkpoint(badge, checkpoint):
        badges.append(badge)
    memcache.set(cache_key, badges)
  logging.info('end get_checkpoint_badges')
  return badges

def badge_in_checkpoint(badge, checkpoint):
  course = checkpoint.key.parent().get()
  checkpoint_key = "%s_%s" % (course.key.id(), checkpoint.key.id())
  if badge.checkpoints and (checkpoint_key in badge.checkpoints):
    return True
  else:
    return False

def get_total_number_notifications(course):
  return  get_number_of_pending_registrations(course)

def get_checkpoints_for_badge(badge, user):
  if badge:
    all_checkpoints = []
    for checkpoint_key in badge.checkpoints:
      if '_' in checkpoint_key:
        courseID, checkpointID = checkpoint_key.split('_')
        course = existing_course(courseID = courseID, user = user)
        the_checkpoint = get_single_checkpoint(course, checkpointID)
        all_checkpoints.append(the_checkpoint)
    return all_checkpoints

def natural_sort_key(key): 
    convert = lambda text: int(text) if text.isdigit() else text 
    return lambda s: [convert(c) for c in re.split('([0-9]+)', key(s))]

def sort_by_name(query_object):
  alist = []
  for indiv_object in query_object:
    alist.append(indiv_object)
  if alist != []:
    return sorted(alist, key=natural_sort_key(attrgetter('name')))
  else:
    return alist


def create_evidence(studentID, badge, content, teacher=False):
  evidence_object = Evidence(
    studentID = str(studentID), 
    content = content, 
    parent = badge.key, 
    teacher = teacher
    )
  evidence_object.put()

def get_evidence(badge, studentID):
  all_evidence = Evidence.query(Evidence.studentID == str(studentID), ancestor = badge.key).order(-Evidence.created)
  return all_evidence

