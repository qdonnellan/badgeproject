from database import *
from handlers import MainHandler
from useful import valid_user

class achievementHandler(MainHandler):
  def post(self):
  	teacher = valid_user()
  	student_id = self.request.get('student_id')
  	logging.info(student_id)
  	course_id = self.request.get('course_id')
  	badge_id = self.request.get('badge_id')
  	status = self.request.get('status')
  	new_achievement(teacher = teacher, student_id = student_id, badge_id = badge_id, course_id = course_id, status = status)

  	self.response.out.write('Poopy pants')