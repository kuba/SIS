import re, types
from datetime import time, datetime

import logging
log = logging.getLogger(__name__)

from sqlalchemy import or_, and_
from sqlalchemy.orm.exc import NoResultFound

from pylons import request, response, session, tmpl_context as c
from pylons import url
from pylons.controllers.util import abort, redirect_to

from school.lib.base import BaseController, render
from school.model import Student, Lesson, Educator
from school.model import meta


class NowError(Exception):
    pass

class MultiplePeopleFoundError(NowError):
    def __init__(self, people):
        super(Exception, self).__init__()
        self.people = people

class NoPersonFoundError(NowError):
    pass

class MultipleLessonsFound(NowError):
    pass

class NoLessonFound(NowError):
    pass

class TooEarlyError(NowError):
    pass

class TooLateError(NowError):
    pass


class NowController(BaseController):

    def index(self):
        return render('now/index.xml')

    def current_order(self):
        schedule = [time(7,55),
                    time(8,55),
                    time(10,0),
                    time(10,55),
                    time(12,0),
                    time(12,55),
                    time(13,50),
                    time(14,45)]

        today = datetime.today()
        weekday = datetime.weekday(today)
        now = datetime.time(today)

        if now < schedule[0]:
            raise TooEarlyError("Before 8 o'clock, stupid!")

        order = 0
        for lorder, ltime in enumerate(schedule):
            if ltime <= now and lorder + 1 < len(schedule) \
                    and not schedule[lorder + 1] <= now:
                order = lorder + 1
                break

        if order == 0:
            raise TooLateError("Kidding me? After school, go and have fun!")

        return order

    def _now_person(self, person):
        order = self.current_order()
        day = datetime.weekday(datetime.now())
        return person.lesson(day, order)

    def now(self, surname):
        try:
            students = meta.Session.query(Student).\
                    filter(Student.last_name.like(surname)).all()
            teachers = meta.Session.query(Educator).\
                    filter(Educator.last_name.like(surname)).all()
            people = students + teachers

            if len(people) > 1:
                raise MultiplePeopleFoundError(people)

        except MultiplePeopleFoundError as e:
            c.people = e.people
            return render('now/list.xml')

        try:
            c.lesson = self._now_person(people[0])
        except NowError as e:
            return repr(e)
        return render('now/now.xml')

    def now_id(self, id):
        person = meta.Session.query(Student).get(id)
        if not person:
            person = meta.Session.query(Teacher).get(id)
        try:
            c.lesson = self._now_person(person)
        except NowError as e:
            return repr(e)
        return render('now/now.xml')
