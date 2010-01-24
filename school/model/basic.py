from sqlalchemy.ext.associationproxy import association_proxy

from sqlalchemy import Column, Integer, SmallInteger, \
                       Unicode, Boolean, Date, ForeignKey, \
                       UniqueConstraint
from sqlalchemy import func
from sqlalchemy.orm import relation, backref

from school.model.meta import Base, Session
from sqlalchemy import desc
from sqlalchemy.orm.exc import NoResultFound

import datetime


class Person(Base):
    """
    Basic class for representing people.

    """
    __tablename__ = 'people'

    id = Column(Integer, primary_key=True)
    first_name = Column(Unicode(256), nullable=False)
    second_name = Column(Unicode(256))
    last_name = Column(Unicode(256), nullable=False)
    is_male = Boolean(nullable=False)

    def __init__(self, first_name, last_name, is_male=True, second_name=None):
        self.first_name = first_name
        self.second_name = second_name
        self.last_name = last_name
        self.is_male = is_male

    @property
    def name(self):
        """
        Get full name (concatenation of first and last names).

        """
        return "%s %s" % (self.first_name, self.last_name)

    def __repr__(self):
        cls = self.__class__.__name__
        return "<%s('%s')>" % (cls, self.name)


class Educator(Person):
    __tablename__ = 'educators'
    __mapper_args__ = {'polymorphic_identity' : 'educator'}

    id = Column(ForeignKey('people.id'), primary_key=True)
    title = Column(Unicode(16))

    def __init__(self, title, *args, **kwargs):
        super(Educator, self).__init__(*args, **kwargs)
        self.title = title

    @property
    def name_with_title(self):
        """
        Return name prefixed with educator's title.

        """
        return "%s %s" % (self.title, self.name)

    def lesson(self, day, order):
        """
        Get lesson for given day and order.

        """
        q = Session.query(Lesson).filter_by(day=day, order=order).\
                filter(Lesson.teacher.has(id=self.id))
        return q.all()

    def lessons_for_day(self, day):
        """
        Get lessons for given day.

        """
        q = Session.query(Lesson).filter_by(day=day).\
                filter(Lesson.teacher.has(id=self.id)).\
                order_by(Lesson.order)
        return q.all()

    def _process_schedule(self, day):
        """
        Returns a schedule for day.

        """
        schedule = []
        for lesson in day:
            while len(schedule) + 1 < lesson.order:
                # Pad empty lessons
                schedule.append(None)
            if not len(schedule) == lesson.order:
                # One teacher can take two groups at once
                schedule.append([])
            schedule[-1].append(lesson)
        return schedule

    def schedule(self):
        """
        Get full week schedule.

        """
        current = [s.id for s in Schedule.current()]
        q = Session.query(Lesson).filter(Lesson.teacher.has(id=self.id)).\
                filter(Lesson.schedule.has(Schedule.id.in_(current))).\
                order_by(Lesson.day, Lesson.order)
        days = {}
        for x in range(0,5):
            days[x] = []
        for lesson in q:
            days[lesson.day].append(lesson)
        schedule = []
        for day in days.values():
            schedule.append(self._process_schedule(day))
        return schedule

    def schedule_for_day(self, day):
        """
        Get schedule for given day.

        """
        return self._process_schedule(self.lessons_for_day(day))

    def __repr__(self):
        cls = self.__class__.__name__
        return "<%s('%s')>" % (cls, self.name_with_title)


class Subject(Base):
    __tablename__ = 'subjects'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(128), nullable=False)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        cls = self.__class__.__name__
        return "<%s('%s')>" % (cls, self.name)


class SchoolYear(Base):
    __tablename__ = 'school_years'

    id = Column(Integer, primary_key=True)
    start = Column(Date, nullable=False)
    end = Column(Date, nullable=True)

    def __init__(self, start, end):
        self.start = start
        self.end = end

    @classmethod
    def query_started(cls):
        """
        Query already started years and order
        it by date from newest to oldest.

        """
        q = Session.query(SchoolYear).\
                filter(SchoolYear.start <= func.date()).\
                order_by(desc(SchoolYear.start))
        return q

    @classmethod
    def recent(cls, count=3):
        """
        Return most recent already started years.

        """
        q = cls.query_started().limit(count)
        return q.all()

    @classmethod
    def current(cls):
        """
        Return current year.

        """
        q = cls.query_started()
        return q.first()

    @classmethod
    def by_index(cls, index):
        """
        Return a school year for given index.
        """
        q = cls.query_started().\
                limit(1).offset(index-1)
        return q.first()

    @property
    def index(self):
        """
        Return the order in which school year appears back in the history.

        """
        q = self.query_started().\
                filter(SchoolYear.start > self.start)
        return q.count() + 1

    @property
    def name(self):
        return "%s/%s" % (self.start.year, self.end.year)

    def __repr__(self):
        cls = self.__class__.__name__
        return "<%s('%s')>" % (cls, self.name)


class Schedule(Base):
    __tablename__ = 'schedules'

    id = Column(Integer, primary_key=True)
    year_id = Column(ForeignKey('school_years.id'), nullable=False)
    year = relation('SchoolYear')
    active = Column(Boolean, nullable=False)
    # TODO: schedule.name

    def __init__(self, year, active=True):
        self.year = year
        self.active = active

    @classmethod
    def current(cls):
        """
        Return current active schedules.

        """
        years = [s.id for s in SchoolYear.recent()]
        q = Session.query(Schedule).\
                filter(Schedule.year.has(SchoolYear.id.in_(years)))
        return q.all()

    def check_rooms(self):
        """
        Check for repetetive rooms, ie. when one room
        is occupied simultanously by two lessons.

        """
        return Session.query(func.count(Lesson.room), Lesson).\
                group_by(Lesson.room, Lesson.order, Lesson.day).\
                having(func.count(Lesson.room)>1).\
                filter(Lesson.room != 100).all()

    def __repr__(self):
        cls = self.__class__.__name__
        return "<%s('%s')>" % (cls, self.year.name)


class Group(Base):
    __tablename__ = 'groups'
    __table_args__ = (
            UniqueConstraint('name', 'year_id'),
            {}
            )

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(16), nullable=False)
    year_id = Column(ForeignKey('school_years.id'))
    year = relation('SchoolYear')

    members = relation('GroupMembership')
    students = association_proxy('members', 'student')

    def __init__(self, name, year):
        self.name = name
        self.year = year

    @property
    def full_name(self):
        return "%d%s" % (self.year.index, self.name)

    @classmethod
    def by_full_name(self, full_name):
        """
        Return group by full_name.

        TODO: how to do that without querying the database multiple times?
        """
        index = int(full_name[0])
        name = full_name[1:]

        year = SchoolYear.by_index(index)
        if year is None:
            return None
        try:
            group = Session.query(Group).filter_by(year=year, name=name).one()
        except NoResultFound:
            group = None
        return group

    def lesson(self, day, order):
        """
        Return lesson for specified day and order.

        """
        q = Session.query(Lesson).\
                filter_by(group_id=self.id, day=day, order=order).all()
        return q

    def _process_schedule(self, day):
        """
        Create schedule from given lessons padding with None where approriate.

        """
        schedule = []

        # We need to sort it
        day.sort()

        for lesson in day:
            while len(schedule) + 1 < lesson.order:
                schedule.append(None)
            if lesson.part is None:
                # Full group
                schedule.append(lesson)
            else:
                # Parted group
                if not len(schedule) == lesson.order:
                    schedule.append([])
                if len(schedule[-1]) == 0 and lesson.part == 2:
                    schedule[-1].append(None)
                schedule[-1].append(lesson)
        return schedule

    def schedule(self):
        """
        Get schedule for entire week.

        """
        current = [s.id for s in Schedule.current()]
        q = Session.query(Lesson).filter(Lesson.group.has(id=self.id)).\
                filter(Lesson.schedule.has(Schedule.id.in_(current))).\
                order_by(Lesson.day, Lesson.order, desc(Lesson.first_part))

        days = {}
        for x in range(0,5):
            days[x] = []
        for lesson in q:
            days[lesson.day].append(lesson)
        schedule = []
        for day in days.values():
            schedule.append(self._process_schedule(day))

        return schedule

    def schedule_for_day(self, day):
        """
        Get schedule for specific day.

        """
        current_schedule = Schedule.current()
        s = [x.id for x in current_schedule]

        q = Session.query(Lesson).filter_by(day=day).\
                filter(Lesson.group.has(id=self.id)).\
                filter(Lesson.schedule.has(Schedule.id.in_(s))).\
                order_by(Lesson.order, desc(Lesson.first_part))

        return self._process_schedule(q.all())

    def __repr__(self):
        cls = self.__class__.__name__
        return "<%s('%s')>" % (cls, self.name)


class GroupMembership(Base):
    __tablename__ = 'groups_memberships'

    student_id = Column(ForeignKey('students.id'), primary_key=True)
    student = relation('Student')

    group_id = Column(ForeignKey('groups.id'), primary_key=True)
    group = relation('Group')
    second_part = Column(Boolean, nullable=False)

    since = Column(Date, nullable=False)
    to = Column(Date, nullable=True)
    active = Column(Boolean, nullable=True)

    def __init__(self, group, part, student, since, to=None, active=True):
        self.group = group
        self.part = part
        self.student = student
        self.since = since
        self.to = to
        self.active = active

    @property
    def part(self):
        if self.second_part:
            return 2
        else:
            return 1

    @part.setter
    def part(self, part):
        if self.part == 1:
            self.second_part = False
        elif self.part == 2:
            self.second_part = True
        else:
            raise ValueError

    def full_group_name(self):
        return "%s%d" % (self.group.name, self.part)

    def __repr__(self):
        return "<GroupMembership('%s', '%s')>" \
                % (self.full_group_name, self.student)


class Student(Person):
    __tablename__ = 'students'
    __mapper_args__ = {'polymorphic_identity' : 'student'}

    id = Column(ForeignKey('people.id'), primary_key=True)
    groups_membership = relation('GroupMembership')
    groups = association_proxy('groups_membership', 'group')

    def lesson(self, day, order):
        """
        Get lesson for specified day and order.

        """
        #TODO check only active membership
        for group in self.groups:
            l = group.lesson(day, order)
            if l is not None:
                return l
        return None


class Lesson(Base):
    __tablename__ = 'lessons'
    __table_args__ = (
            UniqueConstraint('group_id', 'day', 'order',
                'schedule_id', 'first_part'),
            UniqueConstraint('group_id', 'day', 'order',
                'schedule_id', 'second_part'),
            {}
            )

    id = Column(Integer, primary_key=True)

    schedule_id = Column(ForeignKey('schedules.id'), nullable=False)
    schedule = relation('Schedule')

    group_id = Column(ForeignKey('groups.id'), nullable=False)
    group = relation('Group')
    first_part = Column(Boolean, nullable=False)
    second_part = Column(Boolean, nullable=False)

    subject_id = Column(ForeignKey('subjects.id'), nullable=False)
    subject = relation('Subject')

    teacher_id = Column(ForeignKey('educators.id'), nullable=False)
    teacher = relation('Educator')

    order = Column(Integer, nullable=False)
    day = Column(Integer, nullable=False)
    room = Column(Integer, nullable=False)

    def __init__(self, schedule, group, part, subject,
            teacher, day, order, room):
        self.schedule = schedule
        self.group = group
        self.part = part
        self.subject = subject
        self.teacher = teacher
        self.day = day
        self.order = order
        self.room = room

    def __cmp__(self, other):
        """
        Used for sorting.

        Sort by:
        1. day
        2. order
        3. group
        4. part

        """
        c = cmp(self.day, other.day)
        if c == 0:
            c = cmp(self.order, other.order)
            if c == 0:
                c = cmp(self.group, other.group)
                if c == 0:
                    c = cmp(self.part, other.part)
        return c

    @property
    def part(self):
        if self.first_part and self.second_part:
            return None
        elif self.first_part:
            return 1
        else:
            return 2

    @part.setter
    def part(self, part):
        if part is None:
            self.first_part = True
            self.second_part = True
        elif part == 1:
            self.first_part = True
            self.second_part = False
        elif part == 2:
            self.first_part = False
            self.second_part = True
        else:
            raise ValueError

    def __repr__(self):
        return "<Lesson('%r', '%s', '%s', '%s', '%s', '%s', '%s', '%s')>" % \
                (self.schedule, self.group, self.part, self.subject,
                        self.teacher, self.day, self.order, self.room)
