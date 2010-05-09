"""Setup the School application"""
import os
from codecs import open
import datetime
from getpass import getpass

import logging
log = logging.getLogger(__name__)

from pylons import config

from school.config.environment import load_environment
from school.model import meta

from school.model import SchoolYear

from school.parsers import TeachersParser,\
                           StudentsParser,\
                           parse_schedule,\
                           parse_numbers

from school.model.auth import AuthUser, AuthGroup, AuthPermission


def setup_app(command, conf, vars):
    """Place any commands to setup school here"""
    load_environment(conf.global_conf, conf.local_conf)

    # Create the tables if they don't already exist
    log.info("Creating tables...")
    meta.metadata.create_all(bind=meta.engine)
    log.info("Schema saved to the database.")

    # Create auth
    log.info("Creating super admin account...")
    u = AuthUser()
    u.user_name = 'admin'
    u.password = getpass("Password for super admin: ")
    meta.Session.add(u)
    meta.Session.commit()
    log.info("Createad super admin account.")

    # Run parsers
    log.info("Running parsers...")

    # Parse teachers data
    log.info("Parsing teachers data...")
    teachers_parser = TeachersParser(open(config['teachers_file'], 'r', 'utf-8'))
    teachers = teachers_parser.parse()
    log.info("Teachers parsed.")

    # Parse students
    log.info("Parsing students...")
    students_dir = config['students_dir']
    for year in os.listdir(students_dir):
        students_lines = open(os.path.join(students_dir, year), 'r', 'utf-8').readlines()
        StudentsParser(students_lines)
    log.info("Students parsed.")

    q = meta.Session.query(SchoolYear).order_by(SchoolYear.start).limit(3)
    school_years = {q[2]: '1', q[1]: '2', q[0]: '3'}

    # Parse schedule
    log.info("Parsing schedule...")
    parse_schedule(open(config['schedule_file'], 'r', 'utf-8'), teachers, school_years)
    log.info("Schedule parsed.")

    # Parse numbers
    log.info("Parsing numbers...")
    parse_numbers(open(config['numbers_file'], 'r', 'utf-8'))
    log.info("Numbers parsed.")

    log.info("Commiting changes to database...")
    meta.Session.commit()
    log.info("Succesfully set up.")
