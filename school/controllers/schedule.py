import logging
log = logging.getLogger(__name__)

from pylons import request, response, session, tmpl_context as c
from pylons.decorators.cache import beaker_cache
from pylons.controllers.util import abort, redirect_to

from school.lib.base import BaseController, render

from school.model import Lesson, Educator, Group, Group, SchoolYear, Schedule
from school.model.meta import Session

import datetime

from sqlalchemy import desc
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound


class ScheduleController(BaseController):

    def index(self):
        day = request.params.get('day', None)
        group_name = request.params.get('group_name', None)
        teacher_last_name = request.params.get('teacher_last_name', None)
        if group_name is not None:
            if day == 'week':
                redirect_to('schedule_group_week', group_name=group_name)
            elif day is not None:
                redirect_to('schedule_group', day_name=day,
                        group_name=group_name)
            else:
                redirect_to('schedule_group_today',
                        group_name=request.params.get('group_name'))
        if teacher_last_name is not None:
            if day == 'week':
                redirect_to('schedule_teacher_week',
                        teacher_name=teacher_last_name)
            elif day is not None:
                redirect_to('schedule_teacher', day_name=day,
                        teacher_name=request.params.get('teacher_last_name'))
            else:
                redirect_to('schedule_teacher_today',
                        teacher_name=request.params.get('teacher_last_name'))
        
        schedule = Schedule.current()
        c.year = schedule.year
        c.days = ['mon', 'tue', 'wed', 'thu', 'fri']

        c.groups = Group.query_active(schedule.id).\
                         join((SchoolYear, Group.year_id == SchoolYear.id)).\
                         order_by(desc(SchoolYear.start), Group.name).all()
        c.teachers = Educator.query_active(schedule.id).\
                               order_by(Educator.last_name).all()
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
            teacher = Session.query(Educator).\
                    filter(Educator.last_name.like(teacher_name)).one()
        except MultipleResultsFound:
            # TODO: how to do that properly?
            return """Hey, too much teachers with given surname were found.
                      Please report it to administrator!"""
        except NoResultFound:
            return "No such teacher!"

        schedule = Schedule.current()
        c.teacher = teacher
        c.year = schedule.year
        c.lessons = teacher.schedule_for_day(day, schedule.id)
        return render('schedule/teacher.xml')

    def get_group(self, group_name, day_name=None, course=None):
        schedule = Schedule.current()
        year = schedule.year

        group = Group.by_full_name(group_name)
        if not group:
            return 'No such group!'

        day = self.translate_weekday(day_name)
        if day is None:
            return 'Bad day!'

        gs = group.schedule_for_day(day, schedule.id)
        if course is not None:
            course = Group.by_full_name(group_name[0]+course)
            if course is None:
                return "No such course!"
            else:
                cs = course.schedule_for_day(day, schedule.id)
                for o, lesson in enumerate(cs):
                    if lesson is not None:
                        gs[o] = lesson

        c.group_name = group.full_name(year)
        c.lessons = gs
        return render('schedule/group.xml')

    def group_week(self, group_name, course_name=None):
        """
        Render group's schedule for entire week.

        """
        schedule = Schedule.current()
        group = Group.by_full_name(group_name)
        if group is None:
            c.group_name = group_name
            return render('schedule/group/not_found.xml')

        gs = group.schedule(schedule.id)

        # Fetch the course schedule and merge it with group schedule
        if course_name is not None:
            course = Group.by_full_name(group_name[0]+course_name)
            if course is None:
                c.group_name = group_name[0]+course_name
                return render('schedule/group/not_found.xml')
            else:
                cs = course.schedule(schedule.id)
                if cs is not None:
                    for day_number, day in enumerate(cs):
                        for order, lesson in enumerate(day):
                            while len(gs[day_number]) < order + 1:
                                gs[day_number].append(None)
                            if gs[day_number][order] is None:
                                gs[day_number][order] = lesson
                c.group_name += '+%s' % course_name

        c.schedule = gs
        return render('schedule/group/week.xml')

    def teacher_week(self, teacher_name):
        """
        Render teacher's weekly schedule

        :param teacher_name: Last name of the teacher

        """
        q = Session.query(Educator).\
                    filter(Educator.last_name.like(teacher_name))
        teachers = q.all()
        if len(teachers) != 1:
            c.teachers = teachers
            # TODO
            return render('schedule/teacher/list.xml')

        schedule = Schedule.current()
        c.year = schedule.year
        c.teacher = teachers[0]
        c.schedule = c.teacher.schedule(schedule.id)
        return render('schedule/teacher/week.xml')

    @beaker_cache(expire=86400)
    def get_teachers(self):
        """
        Get full current teachers schedule (every teacher and every weekday).

        """
        educators = []
        q = Session.query(Educator).order_by(Educator.last_name)
        for e in q:
            s = e.schedule()
            educators.append((e, s))
        c.year = SchoolYear.current()
        c.educators = educators
        
        return render('schedule/teacher/full_table.xml')

    @beaker_cache(expire=86400)
    def get_groups(self):
        """
        Get full current groups schedule (every group and every weekday).

        """
        schedule = Schedule.current()
        groups = []
        q = Session.query(Group).join(SchoolYear).\
                         order_by(desc(SchoolYear.start)).\
                         order_by(Group.name)
        for g in q:
            s = g.schedule(schedule.id)
            if s is not None:
                groups.append((g, s))
        c.year = schedule.year
        c.groups = groups
        return render('schedule/group/full_table.xml')
