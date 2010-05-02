import datetime

from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import Column, UniqueConstraint, ForeignKey,\
                       Integer, Unicode, Boolean, Date
from sqlalchemy import func, desc, not_
from sqlalchemy.orm import relation, eagerload

from school.model.meta import Base, Session


class Person(Base):
    """
    Basic class for representing people.

    """
    __tablename__ = 'people'

    id = Column(Integer, primary_key=True)
    first_name = Column(Unicode(256), nullable=False)
    second_name = Column(Unicode(256))
    last_name = Column(Unicode(256), nullable=False)
    is_male = Column(Boolean, nullable=False)

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
    """
    Person who has the abbility to teach.

    """
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

    def lesson(self, day, order, schedule_id=None, eager=True):
        """
        Get scheduled lesson for given day and order.

        :param day: The day
        :type day: :class:`int`

        :param order: The lesson order
        :type order: :class:`int`

        :param schedule_id: Schedule to work on
        :type schedule_id: :class:`int`

        :param eager: Whether or not eager load lesson's
                      group and group's year.
        :type eager: :class`bool`

        """
        q = Lesson.query_current(schedule_id)
        q = q.filter(Lesson.day == day).\
              filter(Lesson.order == order).\
              filter(Lesson.teacher_id == self.id)

        if eager:
            q = q.options(eagerload('group'), eagerload('group.year'))

        return q.all()

    def lessons_for_day(self, day, schedule_id=None, eager=True):
        """
        Get lessons for given day.

        :param day: The day
        :type day: :class:`int`

        :param schedule_id: Schedule to work on
        :type schedule_id: :class:`int`

        :param eager: Whether or not eager load lesson's
                      group and group's year.
        :type eager: :class`bool`

        """
        q = Lesson.query_current(schedule_id)
        q = q.filter(Lesson.day == day).\
              filter(Lesson.teacher_id == self.id)

        if eager:
            q = q.options(eagerload('group'), eagerload('group.year'))

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

    def schedule(self, schedule_id=None, eager=True):
        """
        Get educator's full week schedule.

        :param schedule_id: Optional schedule's id to work on.
        :type schedule_id: :class:`int`

        :param eager: Whether or not to eagerly load lesson's group
                      and group's year.
        :type eager: :class:`bool`

        """
        q = Lesson.query_current(schedule_id)
        q = q.filter(Lesson.teacher_id == self.id)

        if eager:
            q = q.options(eagerload('group'), eagerload('group.year'))

        days = {}
        for x in range(0,5):
            days[x] = []
        for lesson in q.all():
            days[lesson.day].append(lesson)
        schedule = []
        for day in days.values():
            schedule.append(self._process_schedule(day))
        return schedule

    def schedule_for_day(self, day, schedule_id=None):
        """
        Get educator's schedule for given day.

        :param schedule_id: Optional schedule's id to work on.
        :type schedule_id: :class:`int`

        """
        lessons = self.lessons_for_day(day, schedule_id, eager=True)
        return self._process_schedule(lessons)

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
    def query_started(cls, date=None):
        """
        Query already started years and sort it by date
        from the newest to the oldest.

        :param date: query relatively to the given date.
        :type date: :class:`datetime.date`

        """
        if date is None:
            date = func.date()
        q = Session.query(SchoolYear).\
                filter(SchoolYear.start <= date).\
                order_by(desc(SchoolYear.start))
        return q

    @classmethod
    def recent(cls, count=3, date=None):
        """
        Return most recent already started years.

        :param count: Number of school years to return.
        :type count: :class:`int`

        """
        q = cls.query_started(date).limit(count)
        return q.all()

    @classmethod
    def current(cls, date=None):
        """
        Return current year.

        """
        q = cls.query_started(date)
        return q.first()

    @classmethod
    def by_index(cls, index, date=None):
        """
        Return a school year for given index.

        """
        q = cls.query_started(date).\
                limit(1).offset(index-1)
        return q.first()

    def index(self, date=None):
        """
        Return the order in which school year appears back in the history.

        """
        q = self.query_started(date).\
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
    year = relation('SchoolYear', lazy=False)
    start = Column(Date, nullable=False)

    def __init__(self, year, start=None):
        self.year = year

        if start is None:
            start = datetime.datetime.now()
        self.start = start

    @classmethod
    def query_current(cls, year_id=None, date=None, q=None):
        """
        Query current active schedule.

        :param year_id: School year of the Schedule
        :type year_id: :class:`int`

        :param date: If year_id is None method queries already started
                     school years relatively to the given date
        :type date: :class:`datetime.date`

        """
        if q is None:
            q = Session.query(Schedule)

        if year_id is None:
            stmt = SchoolYear.query_started(date).limit(1).subquery()
            q = q.join((stmt, Schedule.year_id == stmt.c.id))
        else:
            q = q.filter_by(year_id=year_id)

        q = q.filter(Schedule.start <= func.date())
        return q

    @classmethod
    def current(cls, year_id=None, date=None, q=None):
        return cls.query_current(year_id, date, q).first()

    @classmethod
    def query_current_id(cls, year_id=None, date=None):
        q = Session.query(Schedule.id)
        return cls.query_current(year_id, date, q)

    @classmethod
    def current_id(cls, year_id=None, date=None):
        return cls.query_current_id().first()[0]

    def check_rooms(self, exclude=[]):
        """
        Check for repetetive rooms, ie. when one room
        is occupied simultanously by two lessons.

        :param exclude: You can exclude specific room, eg. gym.
        :type excelud: :class:`list` of :class:`int`

        """
        return Session.query(func.count(Lesson.room), Lesson).\
                group_by(Lesson.room, Lesson.order, Lesson.day,
                         Lesson.schedule_id).\
                having(func.count(Lesson.room)>1).\
                filter(not_(Lesson.room.in_(exclude))).all()

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

    def index(self, year=None):
        """
        Get the group index.

        If year is given the index is computed relatively.

        """
        if year is not None:
            return year.start.year - self.year.start.year + 1
        else:
            return self.year.index()

    def full_name(self, year=None):
        """
        Return full group name (with index).

        """
        return "%d%s" % (self.index(year), self.name)

    @classmethod
    def by_full_name(self, full_name, relative_year=None):
        """
        Return group by its full_name (index + name).

        Full name could be, eg. "1bch", "2inf1" or "2inf2".

        """
        if len(full_name) < 1:
            return None
        try:
            index = int(full_name[0])
        except ValueError:
            return None
        name = full_name[1:]

        year = SchoolYear.by_index(index, relative_year)

        group = Session.query(Group).filter_by(year=year, name=name).first()
        return group

    def lesson(self, day, order, schedule_id=None):
        """
        Return lesson for specified day and order.

        """
        q = Lesson.query_current(schedule_id)
        q = q.filter(Lesson.group_id == self.id).\
              filter(Lesson.day == day).\
              filter(Lesson.order == order).first()
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

    def schedule(self, schedule_id=None):
        """
        Get schedule for entire week.

        """
        q = Lesson.query_current(schedule_id)
        lessons = q.filter(Lesson.group_id == self.id).all()

        if len(lessons) == 0:
            return None

        days = {}
        for x in range(0,5):
            days[x] = []
        for lesson in lessons:
            days[lesson.day].append(lesson)
        schedule = []
        for day in days.values():
            schedule.append(self._process_schedule(day))

        return schedule

    def schedule_for_day(self, day, schedule_id=None):
        """
        Get schedule for specific day.

        """
        q = Lesson.query_current(schedule_id)
        q = q.filter(Lesson.day == day).\
              filter(Lesson.group_id == self.id)

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

    def lesson(self, day, order, schedule_id=None, eager=True):
        """
        Get scheduled lesson for specified day and order.

        :param schedule_id: Optional schedule's id to work on.
        :type schedule_id: :class:`int`

        :param eager: Whether or not to load eagerly lesson's group
                      and group's year.

        """
        q = Lesson.query_current(schedule_id)
        q = q.join((Group, Lesson.group_id == Group.id)).\
              join((GroupMembership, Group.id == GroupMembership.group_id)).\
              filter(GroupMembership.student_id == self.id).\
              filter(GroupMembership.active == True).\
              filter(Lesson.day == day).\
              filter(Lesson.order == order)

        if eager:
            q = q.options(eagerload('group'), eagerload('group.year'))
        return q.all()


class Lesson(Base):
    """
    Representation of school lesson.

    """
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
    subject = relation('Subject', lazy=False)

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

    @classmethod
    def query_current(cls, schedule_id=None):
        """
        Query (ordered) lessons according to current schedule.

        Order by: day, order, part.

        """
        q = Session.query(cls).\
                    order_by(cls.day, cls.order, desc(cls.first_part),
                             desc(cls.second_part))
        if schedule_id is None:
            stmt = Schedule.query_current_id().subquery()
            q = q.join((stmt, cls.schedule_id == stmt.c.id))
        else:
            q = q.filter_by(schedule_id=schedule_id)
        return q


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
        """
        Get the part of the group.

        """
        if self.first_part and self.second_part:
            return None
        elif self.first_part:
            return 1
        elif self.second_part:
            return 2
        else:
            return 0

    @part.setter
    def part(self, part):
        """
        Set the part of the group.

        :param part: Part of the group.
        :type part: :class:`NoneType` or 1 or 2

        """
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
