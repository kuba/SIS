"""Setup the SIS application."""
import os
import sys
import codecs
import getpass
import logging

import pylons.test

from sqlalchemy.exc import IntegrityError

from sis.config.environment import load_environment

from sis.model import Session
from sis.model import Base
from sis.model import AuthUser
from sis.model import Group
from sis.model import Subject

from sis.lib.parsers import TeachersParser
from sis.lib.parsers import StudentsParser
from sis.lib.parsers import LuckyNumberParser
from sis.lib.parsers import FullScheduleParser
from sis.lib.parsers import SubjectsParser

log = logging.getLogger(__name__)

def setup_admin():
    """Setup super admin account."""
    log.info("Creating super admin account...")

    # Prompt for the username, defaults to the system user
    default_username = getpass.getuser()
    username = raw_input("Super admin username [%s]: " % default_username)
    if len(username) == 0:
        username = default_username

    # Prompt for the password
    password = getpass.getpass("Password: ")
    password2 = getpass.getpass("Confirm password: ")
    if password != password2:
        log.error("Passwords do not match!")
        sys.exit()

    # Add super user do the database
    user = AuthUser(username, password)
    Session.add(user)
    Session.commit()

    log.info("Created super admin account.")

    return user

def parse_teachers(path):
    """
    Parse teachers file.

    :param path: Path to the parsable teachers file.

    """
    log.info("Parsing teachers...")

    teachers = {}
    teachers_file = codecs.open(path, 'r', 'utf-8')
    for teacher in TeachersParser(teachers_file):
        teachers[teacher.last_name] = teacher
        Session.add(teacher)

    Session.commit()

    log.info("Teachers parsed and committed.")

    return teachers

def parse_students(students_dir):
    """
    Parse directory with students files.

    :param students_dir: Directory with parsable students files.

    """
    log.info("Parsing students...")

    years = {}

    for path in os.listdir(students_dir):
        students_file = codecs.open(os.path.join(students_dir, path), 'r',
                                    'utf-8').readlines()
        parser = StudentsParser(students_file)
        years[parser.year] = parser.groups

        for students in parser.students.values():
            Session.add_all(students)

    groups = {}

    sorted_years = sorted(years.keys(), key=lambda y: y.start)
    for index, year in enumerate(reversed(sorted_years)):
        user_index = raw_input("Enter index for school year %d/%d [%d]: " \
                          % (year.start.year, year.start.year + 1, index+1))
        if user_index == '':
            user_index = str(index+1)

        for group in years[year]:
            groups[user_index+group.name] = group

    Session.commit()

    log.info("Students (and groupd) parsed and committed.")

    return sorted_years[-1], groups

def parse_subjects(path):
    """
    Parse subjects file.

    :param path: Path to parsable subjects file.

    """
    log.info("Parsing subjects...")

    subjects = {}
    for subject in SubjectsParser(path):
        subjects[subject.short] = subject
        Session.add(subject)

    Session.commit()

    log.info("Subjects parsed and committed.")

    return subjects

def parse_numbers(path):
    """
    Parse lucky numbers file.

    :param path: Path to parsable subjects file.

    """
    log.info("Parsing lucky numbers...")

    lucky_numbers_file = codecs.open(path, 'r', 'utf-8')
    for number in LuckyNumberParser(lucky_numbers_file):
        Session.add(number)
    Session.commit()

    log.info("Lucky numbers parsed and committed.")

def parse_schedule(path, current_year, groups, subjects, teachers):
    """
    Parse schedule file.

    :param path: Path to parsable schedule file

    :param current_year: Current school year.
    :type current_year: :class:`sis.model.SchoolYear`

    :param groups: Groups.
    :type groups: dictionary of (Group.full_name(), Group) key/value pair.

    :param subjects: Subjects.
    :type subjects: dictionary of (Subject.short, Subject) key/value pair.

    :param teachers: Teachers.
    :type teachers: dictionary of (Teacher.full_name, Teacher) key/value pair.

    """
    log.info("Parsing schedule...")

    schedule_file = codecs.open(path, 'r', 'utf-8')
    sp = FullScheduleParser(schedule_file, current_year, groups, subjects,
                           teachers)

    log.info("Schedule parsed.")
    return sp.schedule

def check_rooms(schedule):
    """Check rooms integrity."""
    log.info("Checking rooms...")
    conflicts = schedule.check_rooms(exclude=[100])
    if len(conflicts) == 0:
        log.info("Rooms checked.")
    else:
        error_msg = u"Rooms conflict(s) detected!"
        for c in conflicts:
            error_msg += u"\n\troom: {0}\n\tday: {1}\n\torder: {2}".format(
                c[0].room, c[0].day, c[0].order)
            for l in c:
                error_msg += u"\n\t\t# group: {0}\n\t\t  teacher: {1}".format(
                    l.group.full_name(),
                    l.teacher.name_with_title)
        log.error(error_msg.encode("utf-8"))

def setup_app(command, conf, vars):
    """Setup the SIS application."""
    # Don't reload the app if it was loaded under the testing environment
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)

    # Create the tables if they don't already exist
    log.info("Creating tables...")
    Base.metadata.create_all(bind=Session.bind)
    log.info("Schema saved to the database.")

    # Run parsers
    log.info("Running parsers...")

    # Parse lucky numbers
    parse_numbers(conf['numbers_file'])

    # Parse subjects
    subjects_file = conf.get('subjects_file', 'subjects.xml')
    subjects = parse_subjects(subjects_file)

    # Parse teachers
    teachers = parse_teachers(conf['teachers_file'])

    # Parse students
    students_dir = conf['students_dir']
    current_year, groups = parse_students(students_dir)

    # Parse schedule
    schedule = parse_schedule(conf['schedule_file'], current_year, groups, subjects,
                   teachers)

    try:
        Session.commit()
    except IntegrityError as error:
        if not error.statement.startswith("INSERT INTO lessons"):
            raise

        schedule_id, group_id, first_part, second_part, subject_id, \
            teacher_id, order, day, room = error.params

        # Rollback commit
        Session.rollback()

        group = Session.query(Group).get(group_id)
        subject = Session.query(Subject).get(subject_id)

        error_msg = (
            u"Integrity error: no teacher set!:\n"
            "   group: {0}\n"
            "   first_part: {1}\n"
            "   second_part: {2}\n"
            "   subject: {3}\n"
            "   day: {4}\n"
            "   order: {5}\n"
            "   room: {6}")
        log.error(error_msg.format(group.full_name(), first_part, second_part,
            subject.name, day, order, room).encode("utf-8"))

        sys.exit()

    # Check rooms, exclude gym
    check_rooms(schedule)

    # Create superadmin
    setup_admin()

    log.info("Succesfully set up.")
