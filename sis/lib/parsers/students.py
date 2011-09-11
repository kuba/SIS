"""
Students parser.

Sample students file::

    Smith John - M A
    Kowalski Jan Andrzej M B rwos
    Nowak Janina - F

"""
import re
import datetime
from math import ceil

from sis.lib.parsers.base import Parser, ParserError
from sis.model import SchoolYear, Group, Student, Group, GroupMembership

class StudentsParser(Parser):
    restudent = re.compile(r"""
        (?P<last>[\w-]+)\s+         # last name
        (?P<first>\w+)\s+           # first name
        (?:(?P<second>\w+)|-)\s+    # second name or '-' if none
        (?P<gender>M|F)(?:\s+       # sex
        (?P<extensions>[\w\s]+))?$  # extensions (eg. language course)
                                    # separated by whitespace
        """, re.UNICODE + re.VERBOSE)

    def __init__(self, *args, **kwargs):
        self._section = None
        self.students = {}
        self.groups = []
        super(StudentsParser, self).__init__(*args, **kwargs)


    def parse(self):
        # Retrieve schoolyear's start/end dates
        meta = self.lines.pop(0).strip()
        try:
            start_str, end_str = meta[1:].split('-')
            start = datetime.datetime.strptime(start_str, '%d.%m.%Y')
            end = datetime.datetime.strptime(end_str, '%d.%m.%Y')
        except ValueError:
            raise ParserError("""Metadata line is not valid.""")

        self.year = SchoolYear(start, end)

        super(StudentsParser, self).parse()
        self.post_parse()

    def post_parse(self):
        # Add students to appropriate group
        # parts (determined by surname's order)
        for group_name, membership in self.students.items():
            membership.sort(key=lambda o: o.student.last_name)
            group_count = len(membership)
            last_first = ceil(group_count/2.0)
            group = Group(group_name, self.year)
            self.groups.append(group)
            for order, student in enumerate(membership):
                student.group = group
                if order < last_first:
                    student.part = 1
                else:
                    student.part = 2

    def parse_line(self, line):
        if line.startswith('#'):
            self.process_section_line(line[1:])
        elif self.restudent.match(line):
            self.process_data_line(line)
        elif len(line) == 0:
            pass
        else:
            raise ParserError('Line is neither section nor data.')

    def process_section_line(self, line):
        """Process section line."""
        group_name = line.split(' ')[0]
        # TODO: Teacher name
        if not self.students.has_key(group_name):
            self.students[group_name] = []
        self._section = self.students[group_name]

    def process_data_line(self, line):
        """Process data line."""

        if self._section is None:
            raise ParserError("Section hasn't been defined yet.")

        m = self.restudent.match(line).groupdict()
        first_name = m['first']
        second_name = m['second']
        last_name = m['last']
        gender = m['gender'].lower()
        extensions = m['extensions']

        if gender == 'm':
            is_male = True
        else:
            is_male = False

        student = Student(first_name, last_name, is_male, second_name)
        membership = GroupMembership(None, None, student, self.year.start)
        self._section.append(membership)

        # Parse extensions, eg. "A", "rwos", etc.
        if extensions is not None:
            for extension in extensions.lower().split(' '):
                if not self.students.has_key(extension):
                    self.students[extension] = []
                membership = GroupMembership(group=None, part=None,
                                             student=student,
                                             since=self.year.start)
                self.students[extension].append(membership)
