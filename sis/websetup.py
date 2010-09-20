"""Setup the SIS application."""
import os
import sys
import codecs
import getpass
import logging

import pylons.test

from sqlalchemy.exc import IntegrityError

from sis.config.environment import load_environment

from sis.model import Session, Base, AuthUser, Group
from sis.lib.parsers import TeachersParser, StudentsParser, \
        LuckyNumberParser, FullScheduleParser, SubjectsParser

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

    log.info("Teachers parsed.")

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

    log.info("Students parsed.")

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

    log.info("Subjects parsed.")

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

    log.info("Lucky numbers parsed.")

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
    FullScheduleParser(schedule_file, current_year, groups, subjects,
                           teachers)

    log.info("Schedule parsed.")


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

    # Parse subjects
    subjects_file = conf.get('subjects_file', 'subjects.xml')
    subjects = parse_subjects(subjects_file)

    # Parse teachers
    teachers = parse_teachers(conf['teachers_file'])

    # Parse students
    students_dir = conf['students_dir']
    current_year, groups = parse_students(students_dir)


    # Parse lucky numbers
    parse_numbers(conf['numbers_file'])

    # Parse schedule
    parse_schedule(conf['schedule_file'], current_year, groups, subjects,
                   teachers)

    try:
        Session.commit()
    except IntegrityError as error:
        if not error.statement.startswith("INSERT INTO lessons"):
            raise

        schedule_id, group_id, first_part, second_part, subject_id, \
            teacher_id, order, day, room = error.params

        Session.rollback()
        print Session.query(Group).get(group_id).full_name()
        print day
        print order

        raise
    log.info("Succesfully set up.")
