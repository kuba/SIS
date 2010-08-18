from sqlalchemy import Column, Integer, Date, \
        ForeignKey, Unicode, Boolean, UniqueConstraint
from sqlalchemy import not_, and_
from sqlalchemy.orm import relation

from sis.model.meta import Base, Session
from sis.model import Lesson, Educator

import datetime


class Substitution(Base):
    """
    Class for representing substitution.

    teacher_id can be None, if group is released to home

    """
    __tablename__ = 'substitutions'
    __table_args__ = (
            # Substitution cannot be splitted when the same teacher
            UniqueConstraint('date', 'order', 'group_id', 'teacher_id'),
            UniqueConstraint('date', 'order', 'group_id',
                'part1'),
            UniqueConstraint('date', 'order', 'group_id',
                'part2'),
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
        """
        Get corresponding group's lesson.

        """
        day = datetime.date.weekday(self.date)
        q = Session.query(Lesson).filter_by(day=day,\
                order=self.order, group_id=self.group_id)
        q = q.filter(not_(and_(Lesson.first_part == False,
                               Lesson.second_part == False)))
        return q.all()

    def teacher_lesson(self):
        """
        Get corresponding teacher's lesson.

        """
        day = datetime.date.weekday(self.date)
        q = Session.query(Lesson).filter_by(day=day,\
                order=self.order, teacher_id=self.teacher.id)
        return q.all()

    def __repr__(self):
        cls = self.__class__.__name__
        return "<%s('%s', '%d', '%s', '%s%s', comment='%s')>" % \
                (cls, self.date, self.order, self.teacher, self.group,
                self.part if self.part else '', self.comment)