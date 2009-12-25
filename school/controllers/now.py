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
from school.model import Person, Student, Lesson, GroupMembership
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


schedule = [time(7,55),
            time(8,55),
            time(10,0),
            time(10,55),
            time(12,0),
            time(12,55),
            time(13,50),
            time(14,45)]

def fetch_lesson(session, person, weekday, order):
    # Fetch person
    if isinstance(person, Person):
        pass
    elif isinstance(person, types.IntType):
        person = session.query(Person).\
                with_polymorphic(Student).\
                get(person)
    elif isinstance(person, types.UnicodeType):
        matching_people = session.query(Person).\
                with_polymorphic(Student).\
                filter(Person.last_name == person.capitalize()).\
                all()
        if len(matching_people) > 1:
            raise MultiplePeopleFoundError(matching_people)
        else:
            person = matching_people[0]

    # Fetch lessson
    groups_membership = session.query(GroupMembership).\
            join(GroupMembership.student).\
            filter(Student.id == person.id).all()
    if groups_membership:
        # Student
        lessons = []
        for membership in groups_membership:
            q = session.query(Lesson).\
                        filter(Lesson.group_id == membership.group.id).\
                        filter(or_(Lesson.part == None, Lesson.part == membership.part)).\
                        filter(Lesson.day == weekday).\
                        filter(Lesson.order == order).\
                        all()
            lessons.extend(q)
    else:
        # Teacher
        lessons = session.query(Lesson).\
                          filter(Lesson.teacher_id == person.id).\
                          filter(Lesson.day == weekday).\
                          filter(Lesson.order == order).\
                          all()

    if len(lessons) > 1:
        raise MultipleLessonsFound
    elif len(lessons) == 0:
        raise NoLessonFound
    else:
        return lessons[0]


def fetch_current_lesson(session, student):
    today = datetime.today()
    weekday = datetime.weekday(today)
    now = datetime.time(today)

    order = 0
    for lesson_order, t in enumerate(schedule):
        if now < schedule[0]:
            raise TooEarlyError("Before 8 o'clock, stupid!")
        elif t <= now and lesson_order + 1 < len(schedule) \
                and not schedule[lesson_order + 1] <= now:
            order = lesson_order + 1
            break
    if order == 0:
        raise TooLateError("Kidding me? After school, go and have fun!")

    return fetch_lesson(session, student, 0, 2)


class NowController(BaseController):

    def index(self):
        return render('now/index.xml')

    def now(self, surname):
        try:
            c.lesson = fetch_current_lesson(meta.Session, surname)
            return render('now/now.xml')
        except MultiplePeopleFoundError as e:
            c.people = e.people
            return render('now/list.xml')
        except NowError as e:
            return repr(e)

    def now_id(self, id):
        return self.now(int(id))
