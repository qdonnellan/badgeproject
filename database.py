from google.appengine.ext import ndb
import logging

class User(ndb.Model):
  google_id = ndb.StringProperty(required = True)
  email = ndb.StringProperty(required = True)
  formalName = ndb.StringProperty(required = False)

class Course(ndb.Model):
  course_name = ndb.StringProperty(required = True)
  course_code = ndb.StringProperty(required = True)

class Checkpoint(ndb.Model):
  name = ndb.StringProperty(required = False)
  description = ndb.TextProperty(required = False)

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

def existing_user(google_user):
  if google_user:
    user_object = User.query(User.google_id == str(google_user.user_id())).get()
    if user_object:
      return user_object
    else:
      logging.info('user not found in local database')
      return False
  else:
    logging.info('google user not found')
    return False

def new_user(google_user, formalName):
  if not existing_user(google_user):
    new_user_object = User(google_id = str(google_user.user_id()), formalName = formalName, email = google_user.email())
    new_user_object.put()

def existing_course(courseID, user):
  if courseID:
    theKey = ndb.Key(Course, int(courseID), parent = user.key)
    return theKey.get()
  else:
    return None

def edit_course(course_name, course_code, courseID, user):
  course_object = existing_course(courseID, user)
  if course_object:
    course_object.course_name = course_name
    course_object.course_code = course_code
    course_object.put()
  else:
    course_object = Course(course_name = course_name, course_code = course_code, parent = user.key)
    course_object.put()

def get_user_courses(user, courseID = None):
  if user:
    if courseID:
      return existing_course(courseID, user)
    else:
      return Course.query(ancestor = user.key)
  else:
    return None

def get_user_by_email(email):
  return User.query(User.email == email).get()

def register_for_course(student, teacher, course_code):
  the_course = Course.query(Course.course_code == course_code, ancestor = teacher.key).get()
  if the_course:
    new_registration = Registrations(student_id = str(student.key.id()), status = "pending", parent = the_course.key)
    new_registration.put()
    return True
  else:
    return False

def edit_registration(courseID, teacher, studentID, action):
  course = existing_course(courseID, teacher)
  if course:
    registration_object = Registrations.query(Registrations.student_id == studentID, ancestor = course.key).get()
    if registration_object:
      registration_object.status = action
      registration_object.put()


def get_registrations(course):
  return Registrations.query(ancestor = course.key)


def get_student_course(courseID, student, teacherID):
  teacher = ndb.Key(User, int(teacherID)).get()
  course = existing_course(courseID, teacher)
  registration = Registrations.query(Registrations.student_id == str(student.key.id()), ancestor = course.key).get()
  if registration is not None and registration.status == "approved":
    return course
  else:
    return None


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


def edit_badge(teacher, icon, icon_color, border_color, background, name, requirement, value, checkpoints, badgeID = None):
  if value.isdigit():
    value = int(value)
  else:
    value = 0
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
    the_badge.put()

  

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
  return Badge.query(ancestor = teacher.key)

def create_new_checkpoint(name, description, course):
  new_checkpoint = Checkpoint(name= name, description = description, parent = course.key)
  new_checkpoint.put()

def get_course_checkpoints(course):
  checkpoints = Checkpoint.query(ancestor = course.key)
  return checkpoints
