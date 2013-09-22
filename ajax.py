from database import *
from handlers import MainHandler
from useful import valid_user
from cached_objects import *

class achievementHandler(MainHandler):
  def post(self):
    teacher = valid_user()
    student_id = self.request.get('student_id')
    course_id = self.request.get('course_id')
    badge_id = self.request.get('badge_id')
    status = self.request.get('status')
    student = get_student(student_id)
    course = existing_course(user = teacher, courseID = course_id)
    badge = get_badge(teacher, badge_id)
    new_achievement(teacher = teacher, student =student, badge = badge, course = course, status = status)
    courses = get_user_courses(teacher)
    html = self.render_str('badge_course_list.html', 
      courses = get_cached_user_courses(teacher),  
      badge = badge, 
      active_course = course_id,
      teacher = teacher, 
      achievement_status = achievement_status)
    get_cached_course(course, refresh = True)
    get_cached_course(course, studentID = student_id, refresh = True)
    self.response.out.write(html)

class ajaxBadgeHandler(MainHandler):
  def post(self):
    teacher = valid_user()
    if teacher:
      studentID = self.request.get('student_id')
      courseID = self.request.get('course_id')
      badgeID = self.request.get('badge_id')
      teacherID = teacher.key.id()
      badge_action = self.request.get('action')
      if badge_action == 'award':
        status = 'awarded'
      elif badge_action == 'revoke':
        status = 'revoked'
      elif badge_action == 'deny':
        status = 'denied'
      html = self.render_str('badge_actions.html', 
        studentID = studentID,
        courseID = courseID, 
        badgeID = badgeID,
        current_achievement_status = status,
        )
      self.response.out.write(html)
      
      if badge_action in ['award', 'revoke', 'deny']:
        course = existing_course(courseID, teacher)
        badge = get_badge(valid_user(),badgeID)
        new_achievement(
          teacher = teacher, 
          student = get_student(studentID), 
          badge = badge, 
          course = course,
          status = status
          )
        for course_checkpoint_key in badge.checkpoints:
          courseID, checkpointID = course_checkpoint_key.split('_')
          update_checkpoint_progress(studentID, badgeID, checkpointID, courseID, teacherID, status)
        
class ajaxSectionHandler(MainHandler):
  def post(self):
    teacher = valid_user()
    if teacher:
      courseID = self.request.get('course_id')
      studentID = self.request.get('student_id')
      teacherID = teacher.key.id()
      section_number = self.request.get('section_number')
      if section_number in '12345678':
        course = existing_course(courseID, teacher)
        change_section_number(course, studentID, section_number)
      html = self.render_str('section_list.html',
        studentID = studentID,
        section_number = section_number, 
        courseID = courseID
        )
      self.response.out.write(html)
      delete_cached_course(courseID, teacherID)

      










