"""Lucky number models."""
import datetime
import random

from sqlalchemy import Column, Integer, SmallInteger, Date
from sqlalchemy import func, desc

from sis.model.meta import Base, Session
from sis.model import Student, GroupMembership, Group


class LuckyNumber(Base):
    """
    Lucky number!

    :ivar date: Date of the lucky number
    :type date: datetime.date

    :ivar number: The lucky number
    :type number: int

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
    def current(cls, change_hour, now=None):
        """
        Return current lucky number.

        If the current hour is less than ``change_hour`` try to fetch lucky
        number for the same date. Otherwise fetch the closest lucky number.

        :param change_hour: The hour that defines the end of the day.
        :type change_hour: :class:`int`

        :param now: Fetch lucky number relatively to given datetime. If value
                    is set to None it will use real current datetime.
        :type now: :class:`datetime.datetime` or :class:`NoneType`

        """
        if now is None:
            now = datetime.datetime.now()

        if now.hour >= change_hour:
            start_date = now.date() + datetime.timedelta(1)
        else:
            start_date = now.date()

        lucky = Session.query(cls).\
                    filter(cls.date >= start_date).\
                    order_by(cls.date).first()
        return lucky

    @classmethod
    def current_week(cls, change_hour, now=None):
        """
        Return ``current week``'s lucky numbers.

        ``current week`` is defined based on the given ``now`` and
        ``change_hour`` If there are no more lucky numbers in the
        ``current week`` fetch lucky numbers from the next available week.

        :param change_hour: The hour that defines the end of the day.
        :type change_hour: :class:`int`

        :param now: One of the ``current week``'s days. If value is set to
                    None it will use real current datetime.
        :type now: :class:`datetime.datetime` or :class:`NoneType`

        """
        if now is None:
            now = datetime.datetime.now()

        if now.hour >= change_hour:
            closest_day = now.date() + datetime.timedelta(1)
        else:
            closest_day = now.date()
        closest_weekday = datetime.date.weekday(closest_day)

        # Retrieve the date of the first day in the week
        start_date = closest_day - datetime.timedelta(closest_weekday)
        first_week_end = start_date + datetime.timedelta(7)
        second_week_end = start_date + datetime.timedelta(14)

        q = Session.query(cls).filter(cls.date >= start_date)

        # Optmization. If the ``closest_day`` is 0 it is already new week,
        # no need to query next two weeks, only one.
        if closest_weekday == 0:
            q = q.limit(7)
        else:
            q = q.limit(14)

        # Fetch numbers from the database
        numbers = q.all()

        first_week = []
        second_week = []

        for number in numbers:
            if number.date < first_week_end:
                first_week.append(number)
            else:
                if len(second_week) == 0:
                    second_week_end = number.date + datetime.timedelta(7)
                if number.date < second_week_end:
                    second_week.append(number)

        # Check whether first week any more lucky numbers relatively to
        # the current closest day.
        if len(first_week) > 0 and first_week[-1].date >= closest_day:
            return first_week
        else:
            return second_week

    @classmethod
    def last(cls):
        """
        Return most recent lucky number.

        """
        return Session.query(cls).order_by(desc(cls.date)).first()

    @classmethod
    def left(cls):
        """
        Get left lucky numbers, not used before, sorted.

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
        left = list(all.difference(past))
        left.sort()
        return left

    @classmethod
    def draw(cls):
        """
        Draw left lucky numbers, shuffled

        """
        left = cls.left()
        random.shuffle(left)
        return left
