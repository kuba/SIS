from sqlalchemy.ext.associationproxy import association_proxy

from sqlalchemy import Column, Integer, SmallInteger, \
                       Unicode, Boolean, Date, ForeignKey, \
                       ForeignKeyConstraint
from sqlalchemy import func
from sqlalchemy.orm import relation, backref

from school.model.meta import Base, Session
from sqlalchemy import desc
import datetime


class Person(Base):
    __tablename__ = 'people'

    id = Column(Integer, primary_key=True)
    first_name = Column(Unicode, nullable=False)
    second_name = Column(Unicode)
    last_name = Column(Unicode, nullable=False)
    is_male = Boolean(nullable=False)

    def __init__(self, first_name, last_name, is_male, second_name=None):
        self.first_name = first_name
        self.second_name = second_name
        self.last_name = last_name
        self.is_male = is_male

    @property
    def name(self):
        return "%s %s" % (self.first_name, self.last_name)

    def __repr__(self):
        return "<Person('%s %s')>" % \
                (self.first_name, self.last_name)


class Educator(Person):
    __tablename__ = 'educators'
    __mapper_args__ = {'polymorphic_identity' : 'educator'}

    id = Column(ForeignKey('people.id'), primary_key=True)
    title = Column(Unicode)

    def __init__(self, title, *args, **kwargs):
        super(Educator, self).__init__(*args, **kwargs)
        self.title = title

    def __repr__(self):
        return "<Educator('%s %s')>" % \
                (self.title, self.name)


class Subject(Base):
    __tablename__ = 'subjects'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode, nullable=False)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Subject('%s')>" % self.name


class SchoolYear(Base):
    __tablename__ = 'school_years'

    id = Column(Integer, primary_key=True)
    start = Column(Date, nullable=False)
    end = Column(Date, nullable=True)

    query = Session.query_property()

    def __init__(self, start, end):
        self.start = start
        self.end = end

    @classmethod
    def getRecent(cls):
        now = datetime.datetime.now()
        return cls.query.filter(cls.start < now).\
                order_by(desc(cls.start)).limit(3)

    def __repr__(self):
        return "<SchoolYear('%s/%s')>" % (self.start.year, self.end.year)


class Schedule(Base):
    __tablename__ = 'schedules'

    id = Column(Integer, primary_key=True)
    year_id = Column(ForeignKey('school_years.id'), nullable=False)
    year = relation('SchoolYear')
    active = Column(Boolean, nullable=False)

    def __init__(self, year, active=True):
        self.year = year
        self.active = active

    def __repr__(self):
        return "<Schedule('%r')>" % (self.year)


class Group(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode, nullable=False)
    year_id = Column(ForeignKey('school_years.id'))
    year = relation('SchoolYear')

    members = relation('GroupMembership')
    students = association_proxy('members', 'student')

    @property
    def full_name(self):
        return str(Session.query(func.count(SchoolYear.id)).filter(SchoolYear.start > self.year.start).one()[0]+1) + self.name

    def __init__(self, name, year):
        self.name = name
        self.year = year

    def __repr__(self):
        return "<Group('%s')>" % self.name


class GroupMembership(Base):
    __tablename__ = 'groups_memberships'

    student_id = Column(ForeignKey('students.id'), primary_key=True)
    student = relation('Student')

    group_id = Column(ForeignKey('groups.id'), primary_key=True)
    group = relation('Group')
    part = Column(Integer, nullable=False)

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

    def __repr__(self):
        return "<GroupMembership('%s%s', '%s')>" % (self.group.name, self.part if self.part else '', self.student)


class Student(Person):
    __tablename__ = 'students'
    __mapper_args__ = {'polymorphic_identity' : 'student'}

    id = Column(ForeignKey('people.id'), primary_key=True)
    groups_membership = relation('GroupMembership')
    groups = association_proxy('groups_membership', 'group')

    def __repr__(self):
        return "<Student('%s %s')>" % (self.first_name, self.last_name)


class Lesson(Base):
    __tablename__ = 'lessons'

    id = Column(Integer, primary_key=True)

    schedule_id = Column(ForeignKey('schedules.id'), nullable=False)
    schedule = relation('Schedule')

    group_id = Column(ForeignKey('groups.id'), nullable=False)
    group = relation('Group')
    part = Column(Integer, nullable=True)

    subject_id = Column(ForeignKey('subjects.id'), nullable=False)
    subject = relation('Subject', backref=backref('lessons', order_by='id'))

    teacher_id = Column(ForeignKey('educators.id'), nullable=False)
    teacher = relation('Educator', backref=backref('lessons', order_by='id'))

    order = Column(Integer, nullable=False)
    day = Column(Integer, nullable=False)
    room = Column(Integer, nullable=False)

    def __init__(self, schedule, group, part, subject, teacher, day, order, room):
        self.schedule = schedule
        self.group = group
        self.part = part
        self.subject = subject
        self.teacher = teacher
        self.day = day
        self.order = order
        self.room = room

    def __repr__(self):
        return "<Lesson('%r', '%s', '%s', '%s', '%s', '%s', '%s', '%s')>" % \
                (self.schedule, self.group, self.part, self.subject,
                        self.teacher, self.day, self.order, self.room)
