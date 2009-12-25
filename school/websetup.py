"""Setup the School application"""
import os
from codecs import open
import datetime

import logging
log = logging.getLogger(__name__)

from pylons import config

from school.config.environment import load_environment
from school.model import meta

from school.model import SchoolYear

from school.parsers import TeachersParser,\
                           StudentsParser,\
                           parse_schedule


def setup_app(command, conf, vars):
    """Place any commands to setup school here"""
    load_environment(conf.global_conf, conf.local_conf)

    # Create the tables if they don't already exist
    log.info("Creating tables...")
    meta.metadata.create_all(bind=meta.engine)
    log.info("Successfully set up.")

    # Run parsers
    log.info("Running parsers...")

    # Parse teachers data
    log.info("Parsing teachers data...")
    teachers_parser = TeachersParser(open(config['teachers_file'], 'r', 'utf-8'))
    teachers = teachers_parser.teachers
    log.info("Teachers parsed.")

    # Parse students
    log.info("Parsing students...")
    students_dir = config['students_dir']
    for year in os.listdir(students_dir):
        students_lines = open(os.path.join(students_dir, year), 'r', 'utf-8').readlines()
        StudentsParser(students_lines)
    log.info("Students parsed.")

    q = meta.Session.query(SchoolYear).order_by(SchoolYear.id).limit(3)
    school_years = {q[0]: '1', q[1]: '2', q[2]: '3'}

    # Parse schedule
    log.info("Parsing schedule...")
    parse_schedule(open(config['schedule_file'], 'r', 'utf-8'), teachers, school_years)
    log.info("Schedule parsed.")

    log.info("Commiting changes to database...")
    meta.Session.commit()
    log.info("Succesfully set up.")
