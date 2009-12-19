import re, datetime
from math import ceil

from school.model import meta
from school.model import Student, Group, Subgroup,\
                         SubgroupMembership, SchoolYear

#from schedule import IncosistentError


class StudentsParser(object):
    restudent = re.compile(r"""(?P<last>\w+)\s+           # last name
                               (?P<first>\w+)\s+          # first name
                               (?:(?P<second>\w+)|-)\s+   # second name
                                                          # or '-' for none
                               (?P<gender>M|F)(?:\s+      # sex
                               (?P<course>\w))?$""", re.UNICODE + re.VERBOSE)

    def __init__(self, session, lines):
        meta = lines[0]
        try:
            m = re.match(r'@(?P<start>\d{2}\.\d{2}\.\d{4})-(?P<end>\d{2}\.\d{2}\.\d{4})', meta).groupdict()
        except AttributeError:
            raise IncosistentError('No start/end dates provided!')
        start = datetime.datetime.strptime(m['start'], '%d.%m.%Y')
        end = datetime.datetime.strptime(m['end'], '%d.%m.%Y')
        self.year = SchoolYear(start, end)
        self.lines = lines[1:]
        self.session = session
        self.section = None
        self.courses = {}
        self.students = {}

    def parse(self):
        for lnr, line in enumerate(self.lines):
            self.lnr = lnr
            self.line = line = line[:-1]
            if line.startswith('#'):
                self.process_section_line(line)
            elif self.restudent.match(line):
                self.process_data_line(line)
            elif len(line) == 0:
                pass
            else:
                raise IncosistentError(self.lnr, self.line)

        for group in self.students:
            l = len(self.students[group])
            last_first = ceil(l/2.0)
            first_part = Subgroup(group, '1')
            second_part = Subgroup(group, '2')
            for order, student in enumerate(self.students[group]):
                if order < last_first:
                    student.subgroup = first_part
                else:
                    student.subgroup = second_part
                self.session.add(student)

    def process_section_line(self, line):
        group_name = line[1:].split()[0].lower()
        self.section = Group(group_name, self.year)
        self.students[self.section] = []

    def process_data_line(self, line):
        if self.section is None:
            raise IncosistentError

        m = self.restudent.match(line).groupdict()

        is_male = m['gender'] == 'M' and True or False
        student = Student(m['first'], m['last'], is_male)

        membership = SubgroupMembership()
        membership.student = student
        membership.since = datetime.datetime.now()
        membership.active = True
        self.students[self.section].append(membership)

        if m['course'] is not None:
            course_name = self.section.name[0] + m['course'].lower()
            if not self.courses.has_key(course_name):
                self.courses[course_name] = Group(course_name, self.year)

            course = SubgroupMembership()
            group = self.courses[course_name]
            course.student = student
            course.since = datetime.datetime.now()
            course.active = True
            if not self.students.has_key(group):
                self.students[group] = []
            self.students[group].append(course)
