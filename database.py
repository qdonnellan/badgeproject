from google.appengine.ext import ndb
import logging
from operator import attrgetter
import re

class User(ndb.Model):
  google_id = ndb.StringProperty(required = True)
  email = ndb.StringProperty(required = True)
  formalName = ndb.StringProperty(required = False)
  teacher = ndb.BooleanProperty(default = False)
  formalName_lower = ndb.ComputedProperty(lambda self: self.formalName.lower())

class Course(ndb.Model):
  course_name = ndb.StringProperty(required = True)
  course_code = ndb.StringProperty(required = True)

class Checkpoint(ndb.Model):
  name = ndb.StringProperty(required = False)
  description = ndb.TextProperty(required = False)
  featured = ndb.BooleanProperty(default = False)

class Registrations(ndb.Model):
  student_id = ndb.StringProperty(required = True)
  status = ndb.StringProperty(required = True)

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
  last_modified = ndb.DateTimeProperty(required = True, auto_now = True)


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
    new_user_object = User(google_id = str(google_user.user_id()), formalName = formalName, email = google_user.email())
    new_user_object.put()

def edit_user(user, formalName):
  if user:
    user.formalName = formalName
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
      if course_code == course.course_code:
        if not courseID:
          verification = False
        elif str(courseID) != str(course.key.id()):
          verification = False
  return verification

def edit_course(course_name, course_code, courseID, user):
  course_object = existing_course(courseID, user)
  if course_object:
    course_object.course_name = course_name
    course_object.course_code = course_code
    course_object.put()
  else:
    course_object = Course(course_name = course_name, course_code = course_code, parent = user.key)
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
  the_course = Course.query(Course.course_code == course_code, ancestor = teacher.key).get()
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
  return Course.query(Course.course_code == course_code, ancestor = teacher.key).get()

def edit_registration(courseID, teacher, studentID, action):
  course = existing_course(courseID, teacher)
  if course:
    registration_object = Registrations.query(Registrations.student_id == studentID, ancestor = course.key).get()
    if registration_object:
      registration_object.status = action
      registration_object.put()


def get_registrations(course):
  total_registrations = Registrations.query(ancestor = course.key)
  if total_registrations.count() > 0:
    return total_registrations
  else:
    return None

def get_number_of_pending_registrations(course):
  total_registrations = get_registrations(course)
  total = 0
  if total_registrations:
    for item in total_registrations:
      if item.status == 'pending':
        total += 1
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
  if badgeID and teacher:
    the_badge = ndb.Key(Badge, int(badgeID), parent = teacher.key).get()
  else:
    the_badge = default_badge()
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

def get_all_badges(teacher):
  return Badge.query(ancestor = teacher.key).order(Badge.name)

def create_new_checkpoint(name, description, course, featured):
  if featured == 'true':
    featured = True
  else:
    featured = False
  new_checkpoint = Checkpoint(name= name, description = description, featured = featured, parent = course.key)
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
  checkpoints = Checkpoint.query(ancestor = course.key)
  if checkpoints:
    return sort_by_name(checkpoints)
  else:
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

def get_number_of_badge_requests(course, indiv_student=None, denied_on = False):
  if course:
    teacher = course.key.parent().get()
    badges = get_all_badges(teacher)
    total = 0
    for badge in badges:
      if indiv_student:
        possible_achievement = achievement_status(indiv_student, badge, teacher, course)
        if possible_achievement == 'requested':
          total += 1
        if denied_on and possible_achievement == 'denied':
          total += 1
      else:
        students = get_enrolled_students(course)
        for student in students:
          possible_achievement = achievement_status(student, badge, teacher, course)
          if possible_achievement == 'requested':
            total += 1
    return total

def get_badge_requests(course, indiv_student=None):
  if course:
    teacher = course.key.parent().get()
    badges = get_all_badges(teacher)
    all_requests = []
    for badge in badges:
      if indiv_student:
        possible_achievement = fetch_achievement(indiv_student, badge, teacher, course)
        if possible_achievement:
          all_requests.append(possible_achievement)
      else:
        students = get_enrolled_students(course)
        for student in students:
          possible_achievement = fetch_achievement(student, badge, teacher, course)
          if possible_achievement:
            all_requests.append(possible_achievement)

    if all_requests == []:
      return None
    else:
      return all_requests


def user_is_teacher(course, user):
  if user.teacher:
    if user.key.id() == course.key.parent().get().key.id():
      return True
    else:
      return False
  else:
    return False

def get_checkpoint_percent_completion(course, student, badges, checkpoint):
  total_possible_points = 0
  student_points = 0
  for badge in badges:
    checkpoint_key = "%s_%s" % (course.key.id(), checkpoint.key.id())
    if badge.checkpoints and (checkpoint_key in badge.checkpoints):
      total_possible_points += badge.value
      if achievement_status(student, badge, course.key.parent().get(), course) == 'awarded':
        student_points += badge.value

  if total_possible_points == 0:
    raw_score = 0
  else:
    raw_score = (100.0 * student_points) / total_possible_points
  rounded_score = int(raw_score)
  return rounded_score


def badge_in_checkpoint(badge, checkpoint):
  course = checkpoint.key.parent().get()
  logging.info(badge.checkpoints)
  checkpoint_key = "%s_%s" % (course.key.id(), checkpoint.key.id())
  if badge.checkpoints and (checkpoint_key in badge.checkpoints):
    return True
  else:
    return False

def get_total_number_notifications(course):
  return  get_number_of_badge_requests(course) + get_number_of_pending_registrations(course)

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




