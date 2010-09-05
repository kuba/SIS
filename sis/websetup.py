"""Setup the SIS application."""
import logging
import os
import codecs
import datetime
import getpass

import pylons.test

from sqlalchemy.exc import IntegrityError

from sis.config.environment import load_environment
from sis.model.meta import Session, Base

from sis.model import SchoolYear, Base, Group, Educator

from sis.lib.parsers import TeachersParser, StudentsParser, \
        LuckyNumberParser, parse_schedule

from sis.model.auth import AuthUser, AuthGroup, AuthPermission

log = logging.getLogger(__name__)

def setup_admin():
    """Setup super admin account."""
    log.info("Creating super admin account...")

    default_username = getpass.getuser()
    username = raw_input("Super admin username [%s]: " % default_username)
    if len(username) == 0:
        username = default_username

    password = getpass.getpass("Password for super admin: ")

    user = AuthUser(username, password)
    Session.add(user)

    log.info("Created super admin account.")

def setup_app(command, conf, vars):
    """Setup the SIS application."""
    # Don't reload the app if it was loaded under the testing environment
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)

    # Create the tables if they don't already exist
    log.info("Creating tables...")
    Base.metadata.create_all(bind=Session.bind)
    log.info("Schema saved to the database.")

    # Create superadmin
    setup_admin()

    # Run parsers
    log.info("Running parsers...")

    # Parse teachers data
    log.info("Parsing teachers data...")
    teachers = {}
    teachers_file = codecs.open(conf['teachers_file'], 'r', 'utf-8')
    for teacher in TeachersParser(teachers_file):
        teachers[teacher.last_name] = teacher
        Session.add(teacher)
    log.info("Teachers parsed.")

    # Parse students
    log.info("Parsing students...")
    students_dir = conf['students_dir']
    for year in os.listdir(students_dir):
        students_lines = codecs.open(os.path.join(students_dir, year), 'r', 'utf-8').readlines()
        StudentsParser(students_lines)
    log.info("Students parsed.")

    q = Session.query(SchoolYear).order_by(SchoolYear.start).limit(3)
    school_years = {q[2]: '1', q[1]: '2', q[0]: '3'}

    # Parse lucky numbers
    log.info("Parsing lucky numbers...")
    lucky_numbers_file = codecs.open(conf['numbers_file'], 'r', 'utf-8')
    for number in LuckyNumberParser(lucky_numbers_file):
        Session.add(number)
    log.info("Lucky numbers parsed.")

    Session.commit()

    # Parse schedule
    log.info("Parsing schedule...")
    parse_schedule(codecs.open(conf['schedule_file'], 'r', 'utf-8'), teachers, school_years)
    log.info("Schedule parsed.")

    try:
        Session.commit()
    except IntegrityError as e:
        if not e.statement.startswith("INSERT INTO lessons"):
            raise

        schedule_id, group_id, first_part, second_part, subject_id, teacher_id, order, day, room = e.params

        Session.rollback()
        print Session.query(Group).get(group_id).full_name()
        print day
        print order

        raise
    log.info("Succesfully set up.")
