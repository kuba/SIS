"""The application's model objects."""
from sis.model.meta import Session, Base

from sis.model.basic import Person, Educator, Subject, Group, Lesson, Student, \
        GroupMembership, SchoolYear, Schedule
from sis.model.subs import Substitution
from sis.model.lucky import LuckyNumber

from sis.model.auth import AuthUser, AuthGroup, AuthPermission

__all__ = [
    "Session", "Base", "Person", "Educator", "Subject", "Group", "Lesson",
    "Student", "GroupMembership", "SchoolYear", "Schedule", "Substitution",
    "LuckyNumber", "AuthUser", "AuthGroup", "AuthPermission"
]

def init_model(engine):
    """Call me before using any of the tables or classes in the model"""
    Session.configure(bind=engine)
