from sqlalchemy import Column, Integer, Date, \
        ForeignKey, Unicode
from sqlalchemy.orm import relation

from school.model.meta import Base


class Substitution(Base):
    """
    Class for representing substitution.

    teacher_id can be None, if group is released to home

    """
    __tablename__ = 'substitutions'

    id = Column(Integer, primary_key=True)
    day = Column(Date, nullable=False)
    order = Column(Integer, nullable=False)

    teacher_id = Column(ForeignKey('educators.id'), nullable=True)
    teacher = relation('Educator')

    comment = Column(Unicode)

    def __init__(self, day, order, teacher=None, comment=None):
        self.day = day
        self.order = order
        self.teacher = teacher
        self.comment = comment

    def __repr__(self):
        return "<%s('%s', '%d', '%s', comment='%s')>" % (self.__class__.__name__,
                self.day, self.order, self.teacher.name, self.comment)
