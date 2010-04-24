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
    def draw(cls):
        stmt =  Session.query(func.count(Student.id).label('student_count'),
                              Student).\
                        join(GroupMembership).\
                        join(Group).group_by(Group.id).subquery()
        max = Session.query(func.max(stmt.c.student_count)).first()[0]
        count = Session.query(func.count(LuckyNumber.id)).first()[0]
        past = [x[0] for x in Session.query(LuckyNumber.number).\
                order_by(desc(LuckyNumber.date)).limit(count % max).all()]

        all = range(1, max + 1)
        random.shuffle(all)
        for number in all:
            if number in past:
                all.remove(number)
        return all
