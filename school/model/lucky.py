import random

from sqlalchemy import Column, Integer, SmallInteger, Date
from sqlalchemy import func, desc

from school.model.meta import Base, Session
from school.model import Student, GroupMembership, Group


class LuckyNumber(Base):
    """
    Lucky number!

    """
    __tablename__ = 'lucky_numbers'

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, unique=True)
    number = Column(SmallInteger, nullable=False)

    def __init__(self, date, number):
        self.date = date
        self.number = number

    def __repr__(self):
        cls = self.__class__.__name__
        return "<%s(%s, %s)>" % (cls, self.date, self.number)

    @classmethod
    def last(cls):
        return Session.query(cls).order_by(desc(cls.date)).first()

    @classmethod
    def draw(cls):
        """
        Draw lucky numbers, not used before, shuffled.

        """
        student_count = func.count(Student.id).label('student_count')
        stmt =  Session.query(student_count, Student).\
                        join(GroupMembership).\
                        join(Group).group_by(Group.id).subquery()
        max = Session.query(func.max(stmt.c.student_count)).first()[0]
        count = Session.query(func.count(LuckyNumber.id)).first()[0]
        past = Session.query(LuckyNumber.number).\
                       order_by(desc(LuckyNumber.date)).\
                       limit(count % max).all()

        all = set(range(1, max + 1))
        past = set(x[0] for x in past)
        d = list(all.difference(past))
        random.shuffle(d)
        return d
