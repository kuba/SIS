import re
import sys
from calendar import day_abbr
from codecs import open

from school.parsers.parser import Parser, ParserError

from school.model import Group, Subgroup, Subject, Lesson, Educator
from school.model.meta import Session


class ScheduleParser(Parser):
    day_names = {
            day_abbr[0].lower() : 0,
            day_abbr[1].lower() : 1,
            day_abbr[2].lower() : 2,
            day_abbr[3].lower() : 3,
            day_abbr[4].lower() : 4
            }
    redata = NotImplemented

    def __init__(self, *args, **kwargs):
        self.sections = {}
        self.section = None
        self.day = None
        super(ScheduleParser, self).__init__(*args, **kwargs)

    def parse_line(self):
        if self.line.startswith('#'):
            # New section block begins
            self.process_section_line(self.line[1:])
        elif self.line.startswith('@'):
            # New weekday block begins
            self.process_day_line(self.line[1:])
        elif self.redata.match(self.line):
            self.process_data_line(self.line)
        elif len(self.line) == 0:
            # Pass empty line
            pass
        elif self.line == '-':
            if self.order is not None:
                self.order += 1
        else:
            raise ParserError("Line is not matching any pattern")

    def process_section_line(self, line):
        self.section_name = line
        self.section = self.sections[self.section_name] = {}
        self.day = None

    def process_day_line(self, line):
        if self.section is None:
            raise ParserError(
                    "Weekday block begun, while no " + \
                    "section has been registered yet."
                    )
        try:
            self.day_number = self.day_names[line]
        except KeyError:
            raise ParserError(
                    ("Day (%s) was not recognised." + \
                     "Possible values: %r") \
                    % (day_name, self.day_names)
                    )
        # Start lesson order counter
        self.order = 1
        self.day = self.section[self.day_number] = {}

    def process_data_line(self, line):
        if self.section is None or self.day is None:
            raise ParserError("Data block, while no section" + \
                              "has been registered yet.")
        m = self.redata.match(line).groupdict()
        self.process_data_match(m)
        self.order += 1

    def process_data_match(self, match):
        raise NotImplementedError()


class TeacherScheduleParser(ScheduleParser):
    redata = re.compile(r'[123]\w+[123]?[12]?(/[123]\w+[123]?[12]?)*')

    def __init__(self, teachers, lessons, *args, **kwargs):
        self.teachers = teachers
        self.lessons = lessons
        super(TeacherScheduleParser, self).__init__(*args, **kwargs)

    def process_data_line(self, line):
        groups = line.split('/')
        for g in groups:
            self.process_group(g)
        self.order += 1

    def process_group(self, group_name):
        part = None
        if not self.lessons.has_key(group_name):
            part = int(group_name[-1])
            group_name = group_name[:-1]
            if not self.lessons.has_key(group_name):
                raise ParserError('No such group: %s nor %s' \
                        % (group_name, group_name + part))
        l = self.lessons[group_name][self.day_number][self.order]
        if part is not None:
            l[part-1].teacher = self.teachers[self.section_name]
        else:
            l.teacher = self.teachers[self.section_name]


class ClassScheduleParser(ScheduleParser):
    # Following matches:
    #  pol 45
    #  bio/chem 84/87
    #  ang/- 34/-
    #  - -
    #  -/- -/-
    # but this NOT:
    # rel/ros -/34
    redata = re.compile(r"""
                        (?:(?P<sub1>\w+)|(?P<sub1none>-))
                        (?:/((?P<sub2>\w+)|(?P<sub2none>-)))?\s+
                        (?(sub1none)-|(?P<room1>\w+))
                        (?(sub2none)/-|(?(sub2)/(?P<room2>\w+)))$""",
                        re.UNICODE + re.VERBOSE)


    def __init__(self, subjects, groups, subgroups, *args, **kwargs):
        self.subjects = subjects
        self.groups = groups
        self.subgroups = subgroups
        super(ClassScheduleParser, self).__init__(*args, **kwargs)

    def process_section_line(self, line):
        super(ClassScheduleParser, self).process_section_line(line)
        self.group = self.groups[self.section_name]

    def process_lesson(self, sub, room, part=None):
        sub = self.subjects[sub]
        teacher = None
        room = room == 'h' and 1000 or room
        l = Lesson(self.group, part, sub, teacher,
                self.day_number, self.order, room)
        Session.add(l)
        return l

    def process_data_match(self, m):
        if m['sub2'] is None and m['sub2none'] is None:
            # Entire group (no parts)
            self.day[self.order] = self.process_lesson(m['sub1'], m['room1'])
        else:
            # Lesson is split into groups
            if m['sub1'] is not None:
                subgroup = self.subgroups[self.group.name][1]
                part1 = self.process_lesson(m['sub1'], m['room1'], subgroup)
            else:
                part1 = None
            if m['sub2'] is not None:
                subgroup = self.subgroups[self.group.name][2]
                part2 = self.process_lesson(m['sub2'], m['room2'], subgroup)
            else:
                part2 = None
            self.day[self.order] = (part1, part2)


def parse(file, teachers_info, school_years):
    #lines = file.readlines()
    d = file.read()
    c, t = re.search(r'!classes(.*)!teachers(.*)', d, re.DOTALL).groups()
    groups = {}
    from sqlalchemy import or_
    q = Session.query(Group).filter(or_(Group.year_id == school_years.keys()[0].id, Group.year_id == school_years.keys()[1].id, Group.year_id == school_years.keys()[2].id)).order_by(Group.year_id).all()
    for g in q:
        pr = school_years[g.year]
        groups[pr + g.name] = g

    q2 = Session.query(Subgroup).all()
    subgroups = {}
    for subgroup in q2:
        if not subgroups.has_key(subgroup.group.name):
            subgroups[subgroup.group.name] = {}
        subgroups[subgroup.group.name][subgroup.name] = subgroup

    subjects = [u'mat',
                u'pol',
                u'bio',
                u'chem',
                u'fiz',
                u'geo',
                u'hist',
                u'inf',
                u'wf',
                u'ang',
                u'ros',
                u'fr',
                u'niem',
                u'rel',
                u'muz',
                u'zwo',
                u'plast',
                u'wos',
                u'plast',
                u'tech',
                u'po',
                u'eko',
                u'wok']
    subs = {}
    for s in subjects:
        subs[s] = Subject(s)

    classes = ClassScheduleParser(subs, groups, subgroups, c.split('\n'))
    teachers = TeacherScheduleParser(teachers_info, classes.sections, t.split('\n'))

    return (classes.sections, teachers.sections)
