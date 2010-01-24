import logging
log = logging.getLogger(__name__)

from pylons import request, response, session, tmpl_context as c
from pylons.decorators.cache import beaker_cache
from pylons.controllers.util import abort, redirect_to

from school.lib.base import BaseController, render

from school.model import Lesson, Educator, Group, Group, SchoolYear, Schedule
from school.model import meta

import datetime

from sqlalchemy import or_
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound


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

    def get_teacher(self, teacher_name, day_name=None):
        day = self.translate_weekday(day_name)
        if day is None:
            return 'Bad day!'

        try:
            teacher = meta.Session.query(Educator).\
                    filter(Educator.last_name.like(teacher_name)).one()
        except MultipleResultsFound:
            # TODO: how to do that properly?
            return """Hey, too much teachers with given surname were found.
                      Please report it to administrator!"""
        except NoResultFound:
            return "No such teacher!"

        c.year = SchoolYear.current()
        c.lessons = teacher.schedule_for_day(day)
        return render('schedule/teacher.xml')

    def get_group(self, group_name, day_name=None, course=None):
        group = Group.by_full_name(group_name)
        if not group:
            return 'No such group!'

        day = self.translate_weekday(day_name)
        if day is None:
            return 'Bad day!'

        gs = group.schedule_for_day(day)
        if course is not None:
            course = Group.by_full_name(group_name[0]+course)
            if course is None:
                return "No such course!"
            else:
                cs = course.schedule_for_day(day)
                for o, lesson in enumerate(cs):
                    if lesson is not None:
                        gs[o] = lesson

        c.lessons = gs
        return render('schedule/group.xml')

    @beaker_cache(expire=86400)
    def get_teachers(self):
        """
        Get full current teachers schedule (every teacher and every weekday)

        """
        educators = []
        q = meta.Session.query(Educator).order_by(Educator.last_name)
        for e in q:
            s = e.schedule()
            educators.append((e, s))
        c.year = SchoolYear.current()
        c.educators = educators
        
        return render('schedule/teacher/full_table.xml')
