"""Substitution models."""
import datetime

from sqlalchemy import Column, Integer, Date, ForeignKey, Unicode, Boolean, \
        UniqueConstraint, not_, and_
from sqlalchemy.orm import relation

from sis.model.meta import Base, Session
from sis.model import Lesson


class Substitution(Base):
    """
    Schedule substitution.

    Substition resolves conflict caused by the schedule temporary change
    that happens eg. when a teacher cannot attend the lesson. Here the
    approach is a little bit different, ie. defined ``teacher`` is assigned
    a ``group`` at a given lesson ``order`` and ``date``.

    :ivar date: Date of the substitution.
    :ivar order: Lesson order.

    :ivar group: Group affected.
    :type group: :class:`sis.model.Group`

    :ivar part1: Whether or not the first part is affected by the substitution.
    :type part1: boolean

    :ivar part2: Whether or not the second part is affected by the substitution.
    :type part2: boolean

    :ivar teacher:
        Assigned educator. May be None, if the ``group`` is released
        to home instead of getting substituting educator.
    :type teacher: :class:`sis.model.Educator`

    :ivar comment: Suplementary comment.

    """
    __tablename__ = 'substitutions'
    __table_args__ = (
        # Substitution cannot be splitted when the same teacher
        UniqueConstraint('date', 'order', 'group_id', 'teacher_id'),
        UniqueConstraint('date', 'order', 'group_id', 'part1'),
        UniqueConstraint('date', 'order', 'group_id', 'part2'),
        {}
    )

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    order = Column(Integer, nullable=False)

    group_id = Column(ForeignKey('groups.id'), nullable=False)
    group = relation('Group')
    part1 = Column(Boolean, nullable=False)
    part2 = Column(Boolean, nullable=False)

    teacher_id = Column(ForeignKey('educators.id'), nullable=True)
    teacher = relation('Educator')

    comment = Column(Unicode)

    @property
    def part(self):
        """Part of the group."""
        if self.part1 and self.part2:
            return None
        elif self.part1:
            return 1
        elif self.part2:
            return 2
        else:
            return 0

    @part.setter
    def part(self, part):
        """Set part of the group."""
        if not part:
            self.part1 = True
            self.part2 = True
        elif part == 1:
            self.part1 = True
            self.part2 = False
        elif part == 2:
            self.part1 = False
            self.part2 = True
        else:
            raise ValueError


    def __init__(self, date, order, group, teacher=None,
                 part=None, comment=None):
        self.date = date
        self.order = order
        self.group = group
        self.part = part
        self.teacher = teacher
        self.comment = comment

    def group_lesson(self):
        """Get group's scheduled lesson."""
        day = datetime.date.weekday(self.date)
        query = Session.query(Lesson).\
                filter_by(day=day, order=self.order, group_id=self.group_id). \
                filter(not_(and_(Lesson.first_part == False,
                                 Lesson.second_part == False)))
        return query.all()

    def teacher_lesson(self):
        """Get teacher's scheduled lesson."""
        day = datetime.date.weekday(self.date)
        query = Session.query(Lesson).filter_by(
            day=day, order=self.order, teacher_id=self.teacher.id)
        return query.all()

    def __repr__(self):
        cls = self.__class__.__name__
        name = self.group.name + (self.part if self.part else '')
        return "<%s(%s, %d, %r, %r, comment=%r)>" % (cls, self.date,
            self.order, self.teacher.name_with_title, name, , self.comment)
