"""Setup the School application"""
from codecs import open

import logging
log = logging.getLogger(__name__)

from pylons import config

from school.config.environment import load_environment
from school.model import meta

from school.parsers import StudentsParser,\
                           parse_teachers,\
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

    # Parse students
    log.info("Parsing students...")
    students_lines = open(config['students_file'], 'r', 'utf-8').readlines()
    students_parser = StudentsParser(meta.Session, students_lines)
    students_parser.parse()
    log.info("Students parsed.")

    # Parse teachers data
    log.info("Parsing teachers data...")
    teachers = parse_teachers(open(config['teachers_file'], 'r', 'utf-8'))
    log.info("Teachers parsed.")

    # Parse schedule
    log.info("Parsing schedule...")
    parse_schedule(open(config['schedule_file'], 'r', 'utf-8'), teachers)
    log.info("Schedule parsed.")

    log.info("Commiting changes to database...")
    meta.Session.commit()
    log.info("Succesfully set up.")
