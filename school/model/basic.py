from sqlalchemy.ext.associationproxy import association_proxy

from sqlalchemy import Column, Integer, SmallInteger, \
                       Unicode, Boolean, Date, ForeignKey, \
                       ForeignKeyConstraint
from sqlalchemy.orm import relation, backref

from meta import Base


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


class Group(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode, nullable=False)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Group('%s')>" % self.name


class Subgroup(Base):
    __tablename__ = 'subgroups'

    id = Column(Integer, primary_key=True)
    members = relation('SubgroupMembership')
    students = association_proxy('members', 'student')
    group_id = Column(ForeignKey('groups.id'))
    group = relation('Group')
    name = Column(Unicode, nullable=False)
    
    @property
    def full_name(self):
        return self.group.name + self.name

    def __init__(self, group, name):
        self.group = group
        self.name = name

    def __repr__(self):
        return "<Subgroup('%s%s')>" % (self.group.name, self.name)


class Lesson(Base):
    __tablename__ = 'lessons'
    __table_args__ = (
            ForeignKeyConstraint(['group_id'], ['groups.id']),
            ForeignKeyConstraint(['group_id', 'subgroup_id'],
                ['subgroups.group_id', 'subgroups.id']),
            {}
            )

    id = Column(Integer, primary_key=True)
    
    group_id = Column(Integer)
    group = relation('Group')
    subgroup_id = Column(Integer)
    subgroup = relation('Subgroup')

    subject_id = Column(ForeignKey('subjects.id'), nullable=False)
    subject = relation('Subject', backref=backref('lessons', order_by='id'))

    teacher_id = Column(ForeignKey('educators.id'), nullable=False)
    teacher = relation('Educator', backref=backref('lessons', order_by='id'))

    order = Column(Integer, nullable=False)
    day = Column(Integer, nullable=False)
    room = Column(Integer, nullable=False)

    def __init__(self, group, subgroup, subject, teacher, day, order, room):
        self.group = group
        self.subgroup = subgroup
        self.subject = subject
        self.teacher = teacher
        self.day = day
        self.order = order
        self.room = room

    def __repr__(self):
        return "<Lesson('%s', '%s', '%s', '%s', '%s', '%s', '%s')>" % \
                (self.group, self.subgroup, self.subject,
                        self.teacher, self.day, self.order, self.room)


class Student(Person):
    __tablename__ = 'students'
    __mapper_args__ = {'polymorphic_identity' : 'student'}

    id = Column(ForeignKey('people.id'), primary_key=True)
    subgroups_membership = relation('SubgroupMembership')
    subgroups = association_proxy('subgroups_membership', 'subgroup')

    def __repr__(self):
        return "<Student('%s %s')>" % (self.first_name, self.last_name)


class SubgroupMembership(Base):
    __tablename__ = 'subgroups_memberships'

    student_id = Column(ForeignKey('students.id'), primary_key=True)
    student = relation('Student')

    subgroup_id = Column(ForeignKey('subgroups.id'), primary_key=True)
    subgroup = relation('Subgroup')

    since = Column(Date, nullable=False)
    to = Column(Date, nullable=True)
    active = Column(Boolean, nullable=True)

    def __repr__(self):
        return "<SubgroupMembership('%s%s', '%s')>" % \
                (self.subgroup.group.name, self.subgroup.name, self.student.name)
