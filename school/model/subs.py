from sqlalchemy import Column, Integer, Date, \
        ForeignKey, Unicode, Boolean
from sqlalchemy.orm import relation

from school.model.meta import Base


class Substitution(Base):
    """
    Class for representing substitution.

    teacher_id can be None, if group is released to home

    """
    __tablename__ = 'substitutions'

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
        else:
            return 2

    @part.setter
    def part(self, part):
        if part is None:
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


    def __init__(self, date, order, group, teacher=None, part=None, comment=None):
        self.date = date
        self.order = order
        self.group = group
        self.part = part
        self.teacher = teacher
        self.comment = comment

    def __repr__(self):
        cls = self.__class__.__name__
        return "<%s('%s', '%d', '%s', '%s%s', comment='%s')>" % (cls, self.date,
                self.order, self.teacher.name, self.group,
                self.part if self.part else '', self.comment)
