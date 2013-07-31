from database import *
from handlers import MainHandler
from useful import valid_user

class achievementHandler(MainHandler):
  def post(self):
    teacher = valid_user()
    student_id = self.request.get('student_id')
    course_id = self.request.get('course_id')
    badge_id = self.request.get('badge_id')
    status = self.request.get('status')
    student = get_student(student_id)
    course = existing_course(teacher, course_id)
    badge = get_badge(teacher, badge_id)
    new_achievement(teacher = teacher, student =student, badge = badge, course = course, status = status)
    courses = get_user_courses(teacher)
    html = self.render_str('badge_course_list.html', 
      courses = courses, 
      badge = badge, 
      get_enrolled_students = get_enrolled_students,
      active_course = course_id,
      teacher = teacher, 
      achievement_status = achievement_status)
    self.response.out.write(html)