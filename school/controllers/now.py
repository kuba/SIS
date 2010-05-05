from datetime import time, datetime

import logging
log = logging.getLogger(__name__)

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from school.lib.base import BaseController, render
from school.model import Student, Educator, Schedule
from school.model.meta import Session


class NowController(BaseController):

    def index(self):
        """
        Render index page or redirect to now or now_id actions if surname is
        available in the request's params.

        """
        if 'surname' in request.params:
            redirect_to('now_name', surname=request.params['surname'])
        else:
            return render('now/index.xml')

    def current_order(self):
        """
        Return the current lesson order.

        """
        schedule = [time(7,55),
                    time(8,55),
                    time(10,0),
                    time(10,55),
                    time(12,0),
                    time(12,55),
                    time(13,50),
                    time(14,45)]

        now = datetime.now().time()

        if now < schedule[0] or now > schedule[-1]:
            return

        order = 0
        for t in schedule:
            if now >= t:
                order += 1
            if now < t:
                break

        return order

    def now(self, surname):
        """
        Get the lesson for given person ``surname``.

        """
        current_order = self.current_order()
        if current_order is None:
            return render('now/now.xml')

        today = datetime.weekday(datetime.today())
        schedule = Schedule.current()

        c.year = schedule.year

        students = Session.query(Student).\
                filter(Student.last_name.like(surname)).all()
        teachers = Session.query(Educator).\
                filter(Educator.last_name.like(surname)).all()
        people = students + teachers

        if len(people) != 1:
            c.people = people
            return render('now/list.xml')

        c.lesson = people[0].lesson(today, current_order, schedule.id)
        return render('now/now.xml')

    def now_id(self, id):
        """
        Get the lesson for given person ``id``.

        """
        current_order = self.current_order()
        if current_order is None:
            return render('now/now.xml')

        today = datetime.weekday(datetime.today())
        schedule = Schedule.current()
        c.year = schedule.year

        person = Session.query(Student).get(id)
        if not person:
            person = Session.query(Educator).get(id)

        c.lesson = person.lesson(today, current_order, schedule.id)
        return render('now/now.xml')
