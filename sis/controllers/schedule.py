"""
Schedule management controller module.

"""
import datetime

import logging
log = logging.getLogger(__name__)

from pylons import request, response, session, tmpl_context as c, url
from pylons.decorators.cache import beaker_cache
from pylons.controllers.util import abort, redirect

from sqlalchemy import desc
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from sis.lib.base import BaseController, render

from sis.model import Educator, Group, SchoolYear, Schedule
from sis.model.meta import Session


class ScheduleController(BaseController):
    """
    Schedule management controller.

    """
    def index(self):
        """
        Render schedule management control panel. Handle POST redirects.

        """
        day = request.params.get('day', None)
        group_name = request.params.get('group_name', None)
        course_name = request.params.get('course_name', None)
        teacher_last_name = request.params.get('teacher_last_name', None)
        if group_name is not None:
            if course_name is not None:
                if day == 'week':
                    redirect(url('schedule_group_course_week',
                            group_name=group_name, course_name=course_name))
                elif day is not None:
                    redirect(url('schedule_group_course', day_name=day,
                            group_name=group_name, course_name=course_name))
                else:
                    redirect(url('schedule_group_course_today',
                        group_name=group_name, course_name=course_name))
            else:
                if day == 'week':
                    redirect(url('schedule_group_week', group_name=group_name))
                elif day is not None:
                    redirect(url('schedule_group', day_name=day,
                                 group_name=group_name))
                else:
                    redirect(url('schedule_group_today',
                        group_name=group_name))
        if teacher_last_name is not None:
            if day == 'week':
                redirect(url('schedule_teacher_week',
                        teacher_name=teacher_last_name))
            elif day is not None:
                redirect(url('schedule_teacher', day_name=day,
                        teacher_name=request.params.get('teacher_last_name')))
            else:
                redirect(url('schedule_teacher_today',
                        teacher_name=request.params.get('teacher_last_name')))

        schedule = Schedule.current()
        c.year = schedule.year

        groups = Group.query_active(schedule.id).\
                         join((SchoolYear, Group.year_id == SchoolYear.id)).\
                         order_by(desc(SchoolYear.start), Group.name).all()
        courses = []
        classes = []
        for g in groups:
            if len(g.name) == 1 and g.name not in courses:
                courses.append(g.name)
            elif len(g.name) != 1 and g.name not in classes:
                classes.append(g.full_name(schedule.year))
        courses.sort()
        classes.sort()

        teachers = Educator.query_active(schedule.id).\
                               order_by(Educator.last_name).all()

        c.groups = groups
        c.courses = courses
        c.classes = classes
        c.teachers = teachers
        return render('schedule/index.xml')

    def _translate_weekday(self, name):
        """
        Translate given short ``name`` to the weekday integer.

        """
        default = datetime.datetime.weekday(datetime.datetime.today())
        days = {
                'mon' : 0,
                'tue' : 1,
                'wed' : 2,
                'thu' : 3,
                'fri' : 4,
                None: default
                }
        try:
            day = days[name]
        except KeyError:
            day = None
        return day

    def teacher(self, teacher_name, day_name=None):
        """
        Render teacher's schedule for the given day.

        :param teacher_name: Surname of the teacher
        :param day_name: Name of the day

        """
        day = self._translate_weekday(day_name)
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

    def group(self, group_name, day_name=None, course_name=None):
        """
        Render group's schedule for the given day. Optionally with the course.

        :param group_name: Full name of the group (includeing year index)
        :param day_name: Name of the day
        :param course_name: Optional couse name

        """
        schedule = Schedule.current()
        year = schedule.year

        group = Group.by_full_name(group_name)
        if group is None:
            c.group_name = group_name
            return render('schedule/group/not_found.xml')

        day = self._translate_weekday(day_name)
        if day is None:
            return 'Bad day!'

        gs = group.schedule_for_day(day, schedule.id)

        if course_name is not None:
            course_full_name = group_name[0] + course_name
            course = Group.by_full_name(course_full_name)
            if course is None:
                c.group_name = course_full_name
                return render('schedule/group/not_found.xml')
            else:
                cs = course.schedule_for_day(day, schedule.id)
                for o, lesson in enumerate(cs):
                    while len(gs) < o + 1:
                        gs.append(None)
                    if gs[o] is None:
                        gs[o] = lesson
                    # TODO elif gs[o] is list
            c.course = course
        else:
            c.course = None

        c.group = group
        c.year = year
        c.lessons = gs
        return render('schedule/group.xml')

    def group_week(self, group_name, course_name=None):
        """
        Render group's schedule for entire week.

        :param group_name: Full name of the group (including year index)
        :pram course_name: Optional name of the course

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
            c.course = course
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
        else:
            c.course = None

        if len(group_name) != 2:
            # group is not course
            from sqlalchemy import func
            q = Group.query_active().filter(Group.year_id == group.year_id).\
                        filter(func.length(Group.name) == 1).\
                        order_by(Group.name)
            c.courses = q.all()

        c.group = group
        c.group_name = group_name
        c.year = schedule.year
        c.schedule = gs
        return render('schedule/group/week.xml')

    def teacher_week(self, teacher_name):
        """
        Render teacher's weekly schedule.

        :param teacher_name: Last name of the teacher

        """
        teachers = Session.query(Educator).\
                           filter(Educator.last_name.like(teacher_name)).all()

        if len(teachers) != 1:
            c.teachers = teachers
            return render('schedule/teacher/list.xml')

        schedule = Schedule.current()
        c.year = schedule.year
        c.teacher = teachers[0]
        c.schedule = c.teacher.schedule(schedule.id)
        return render('schedule/teacher/week.xml')

    @beaker_cache(expire=86400)
    def teachers(self):
        """
        Render full currently active teachers schedule table
        (every teacher and every weekday).

        """
        schedule = Schedule.current()
        q = Educator.query_active(schedule_id=schedule.id).\
                     order_by(Educator.last_name)
        educators = []
        for e in q.all():
            s = e.schedule()
            educators.append((e, s))

        c.year = schedule.year
        c.educators = educators
        return render('schedule/teacher/full_table.xml')

    @beaker_cache(expire=86400)
    def groups(self):
        """
        Render full currently active groups schedule
        (every group and every weekday).

        """
        schedule = Schedule.current()
        q = Group.query_active(schedule_id=schedule.id).\
                  join((SchoolYear, Group.year_id == SchoolYear.id)).\
                  order_by(desc(SchoolYear.start), Group.name)

        groups = []
        for g in q.all():
            s = g.schedule(schedule.id)
            groups.append((g, s))

        c.year = schedule.year
        c.groups = groups
        return render('schedule/group/full_table.xml')
