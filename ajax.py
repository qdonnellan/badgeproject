from database import *
from handlers import MainHandler
from useful import valid_user
from cached_objects import get_cached_course, get_cached_user_courses

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