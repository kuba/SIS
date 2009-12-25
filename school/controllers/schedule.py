import logging
log = logging.getLogger(__name__)

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from school.lib.base import BaseController, render

from school.model import Lesson, Educator, Group, Group
from school.model import meta

import datetime

from sqlalchemy import or_


class ScheduleController(BaseController):

    def index(self):
        return render('schedule/index.xml')

    def translate_weekday(self, name):
        days = {'mon' : 0,
                'tue' : 1,
                'wed' : 2,
                'thu' : 3,
                'fri' : 4,
                None : datetime.datetime.weekday(datetime.datetime.today())
                }
        try:
            day = days[name]
        except KeyError:
            day = None
        return day

    def get_teacher_schedule(self, teacher_name, day_name=None):
        day = self.translate_weekday(day_name)
        if day is None:
            return 'Bad day!'

        last_name = teacher_name.capitalize()

        q = meta.Session.query(Lesson).\
                join(Lesson.teacher).\
                filter(Educator.last_name == last_name).\
                filter(Lesson.day == day).\
                order_by(Lesson.order)

        lessons = []
        for lesson in q:
            while len(lessons) + 1 < lesson.order:
                lessons.append(None)
            if not len(lessons) == lesson.order:
                lessons.append([])
            lessons[-1].append(lesson)
        c.lessons = lessons
        return render('schedule/teacher.xml')

    def get_group_schedule(self, group_name, day_name=None, course=None):
        day = self.translate_weekday(day_name)
        if day is None:
            return 'Bad day!'

        if course:
            course = group_name[0] + course

        q = meta.Session.query(Lesson).\
                join(Lesson.group).\
                filter(or_(Group.name == group_name, Group.name == course)).\
                filter(or_(Lesson.part == None, Lesson.part == 1, Lesson.part == 2)).\
                filter(Lesson.day == day).\
                order_by(Lesson.order).\
                order_by(Lesson.part)

        lessons = []
        for lesson in q:
            while len(lessons) + 1 < lesson.order:
                lessons.append(None)
            if not len(lessons) == lesson.order:
                lessons.append({})
            if lesson.part is None:
                lessons[-1] = lesson
            else:
                lessons[-1][lesson.part] = lesson

        c.lessons = lessons
        return render('schedule/group.xml')
