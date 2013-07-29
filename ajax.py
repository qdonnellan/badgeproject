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
    new_achievement(teacher = teacher, student_id = student_id, badge_id = badge_id, course_id = course_id, status = status)
    courses = get_user_courses(teacher)
    badge = get_badge(teacher,badge_id)
    html = self.render_str('badge_course_list.html', 
      courses = courses, 
      badge = badge, 
      get_enrolled_students = get_enrolled_students,
      active_course = course_id,
      teacher = teacher, 
      achievement_status = achievement_status)
    self.response.out.write(html)