import re, datetime
from math import ceil

from sis.parsers.parser import Parser, ParserError
from sis.model import SchoolYear, Group, Student, \
                         Group, GroupMembership

from sis.model.meta import Session


RESTUDENT = re.compile(r"""
                        (?P<last>\w+)\s+           # last name
                        (?P<first>\w+)\s+          # first name
                        (?:(?P<second>\w+)|-)\s+   # second name
                                                   # or '-' for none
                        (?P<gender>M|F)(?:\s+      # sex
                        (?P<course>\w))?$          # language course
                        """, re.UNICODE + re.VERBOSE)


class StudentsParser(Parser):
    def __init__(self, *args, **kwargs):
        self.section = None
        self.students = {}
        super(StudentsParser, self).__init__(*args, **kwargs)


    def parse(self):
        # Retrieve schoolyear's start/end dates
        meta = self.lines.pop(0).strip()
        try:
            start_str, end_str = meta[1:].split('-')
            start = datetime.datetime.strptime(start_str, '%d.%m.%Y')
            end = datetime.datetime.strptime(end_str, '%d.%m.%Y')
        except ValueError:
            raise ParserError("""File has no schoolyear's
                    start/end dates or is invalid""")
        self.year = SchoolYear(start, end)

        super(StudentsParser, self).parse()

        # Add students to appropriate group
        # parts (determined by surname's order)
        for group_name, membership in self.students.items():
            membership.sort(key=lambda o: o.student.last_name)
            group_count = len(membership)
            last_first = ceil(group_count/2.0)
            group = Group(group_name, self.year)
            for order, student in enumerate(membership):
                student.group = group
                if order < last_first:
                    student.part = 1
                else:
                    student.part = 2
                Session.add(student)

    def parse_line(self):
        if self.line.startswith('#'):
            self.process_section_line(self.line[1:])
        elif RESTUDENT.match(self.line):
            self.process_data_line(self.line)
        elif len(self.line) == 0:
            pass
        else:
            raise ParserError('Line is neither section nor data.')

    def process_section_line(self, line):
        group_name = line.split(' ', 1)[0]
        # TODO: Teacher name
        if not self.students.has_key(group_name):
            self.students[group_name] = []
        self.section = self.students[group_name]

    def process_data_line(self, line):
        if self.section is None:
            raise ParserError("Section hasn't been defined before.")

        m = RESTUDENT.match(line).groupdict()
        gender = m['gender'].lower()
        first_name = m['first']
        last_name = m['last']
        course_name = m['course']

        if gender == 'm':
            is_male = True
        elif gender == 'f':
            is_male = False
        else:
            raise ParserError("No such gender, try one of %r" % gender)

        student = Student(first_name, last_name, is_male)
        membership = GroupMembership(None, None, student, self.year.start)
        self.section.append(membership)

        if course_name is not None:
            course_name = course_name.lower()
            if not self.students.has_key(course_name):
                self.students[course_name] = []
            course_membership = GroupMembership(None, None, student, self.year.start)
            self.students[course_name].append(course_membership)
