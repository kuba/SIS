import re
import sys

from codecs import open

from school.model import Group, Subgroup, Subject, Lesson, Educator
from school.model import meta


class IncosistentError(Exception):
    pass


class ScheduleParser(object):
    day_names = {'mon':0, 'tue':1, 'wed':2, 'thu':3, 'fri':4}
    redata = NotImplemented

    def __init__(self, lines):
        self.lines = lines
        self.sections = {}
        # FLAGS
        self.section = None
        self.day = None

    def parse(self):
        for lnr, line in enumerate(self.lines):
            self.lnr = lnr
            self.line = line
            try:
                if line.startswith('#'):
                    # New secton block begins
                    self.process_section_line(line)
                elif line.startswith('@'):
                    # New weekday block begins
                    self.process_day_line(line)
                elif self.redata.match(line):
                    # New data line
                    self.process_data_line(line)
                elif len(line) == 0:
                    pass
                elif line == '-':
                    self.order += 1
                else:
                    raise IncosistentError("Line is not matching: %s" % line)
            except IncosistentError as e:
                raise IncosistentError("%d (%s) :: %s" % (lnr, line, e))

    def process_section_line(self, line):
        self.section = line[1:]
        self.sections[self.section] = {}

    def process_day_line(self, line):
        # New weekday begins
        if self.section is None:
            raise IncosistentError("Weekday block, while no " + \
                                   "section has been registered yet.")
        day_name = line[1:]
        try:
            self.day = self.day_names[day_name]
        except KeyError:
            raise IncosistentError(("Day (%s) was not recognised." + \
                                    "Possible values: %r")
                                    % (day_name, self.day_names))
        # Start lesson order counter
        self.order = 1
        self.sections[self.section][self.day] = {}

    def process_data_line(self, line):
        if self.section is None or self.day is None:
            raise IncosistentError("Data block, while no section" + \
                                   "has been registered yet.")
        m = self.redata.match(line).groupdict()
        self.process_data_match(m)
        self.order += 1

    def process_data_match(self, match):
        raise NotImplementedError("process_data_match() must be " + \
                                  "implemented in child class!")


class ClassScheduleParser(ScheduleParser):
    # Following matches:
    #  pol 45
    #  bio/chem 84/87
    #  ang/- 34/-
    #  - -
    #  -/- -/-
    # but this NOT:
    # rel/ros -/34
    redata = re.compile(r'(?:(?P<sub1>\w+)|(?P<sub1none>-))(?:/((?P<sub2>\w+)|(?P<sub2none>-)))?\s+(?(sub1none)-|(?P<room1>\w+))(?(sub2none)/-|(?(sub2)/(?P<room2>\w+)))$')
    subjects = [u'mat', u'pol', u'bio', u'chem', u'fiz', u'geo', u'hist', u'inf', u'wf', u'ang', u'ros', u'fr', u'niem', u'rel', u'muz', u'zwo', u'plast', u'wos', u'plast', u'tech', u'po', u'eko', u'wok']

    def __init__(self, session, groups, subgroups, *args, **kwargs):
        super(ClassScheduleParser, self).__init__(*args, **kwargs)
        self.groups = groups
        self.subgroups = subgroups
        self.session = session
        # subjects
        subjects = {}
        for s in self.subjects:
            subjects[s] = Subject(s)
        self.subjects = subjects

    def process_section_line(self, line):
        super(ClassScheduleParser, self).process_section_line(line)
        self.group = self.groups[self.section]

    def process_lesson(self, sub, room, part=None):
        sub = self.subjects[sub]
        teacher = None
        room = room == 'h' and 1000 or room
        l = Lesson(self.group, part, sub, teacher, self.day, self.order, room)
        self.session.add(l)
        return l

    def process_data_match(self, m):
        if m['sub2'] is None and m['sub2none'] is None:
            # Entire Class
            self.sections[self.section][self.day][self.order] = self.process_lesson(m['sub1'], m['room1'])
        else:
            # Split
            if m['sub1'] is not None:
                l1 = self.process_lesson(m['sub1'], m['room1'], self.subgroups[self.group.name]['1'])
            else:
                l1 = None
            if m['sub2'] is not None:
                l2 = self.process_lesson(m['sub2'], m['room2'], self.subgroups[self.group.name]['2'])
            else:
                l2 = None
            self.sections[self.section][self.day][self.order] = (l1, l2)


class TeacherScheduleParser(ScheduleParser):
    redata = re.compile(r'(?P<g1>[123]\w+[123]?[12]?)(?P<g2>/[123]\w+[123]?[12]?)?')
    redata = re.compile(r'[123]\w+[123]?[12]?(/[123]\w+[123]?[12]?)*')

    def __init__(self, lines, classes, teachers, groups):
        super(TeacherScheduleParser, self).__init__(lines)
        self.classes = classes
        self.teachers = teachers

    def process_data_line(self, line):
        groups = line.split('/')
        for g in groups:
            if not self.classes.has_key(g):
                name = g[:-1]
                subgroup = int(g[-1]) - 1
                try:
                    self.classes[name][self.day][self.order][subgroup].teacher = self.teachers[self.section]
                except (AttributeError, KeyError, TypeError):
                    sys.exit('%s :: %s :: %s (%s)' % (self.section, self.day, self.order, self.line))
            else:
                try:
                    self.classes[g][self.day][self.order].teacher = self.teachers[self.section]
                except (AttributeError, KeyError, TypeError):
                    sys.exit('%s :: %s :: %s (%s)' % (self.section, self.day, self.order, self.line))
        self.order += 1


def parse(file, teachers_info):
    #lines = file.readlines()
    d = file.read()
    c, t = re.search(r'!classes(.*)!teachers(.*)', d, re.DOTALL).groups()
    groups = {}
    q = meta.Session.query(Group).all()
    for g in q:
        groups[g.name] = g

    q2 = meta.Session.query(Subgroup).all()
    subgroups = {}
    for subgroup in q2:
        if not subgroups.has_key(subgroup.group.name):
            subgroups[subgroup.group.name] = {}
        subgroups[subgroup.group.name][subgroup.name] = subgroup

    classes = ClassScheduleParser(meta.Session, groups, subgroups, c.split('\n'))
    classes.parse()
    teachers = TeacherScheduleParser(t.split('\n'), classes.sections, teachers_info, groups)
    teachers.parse()
    return (classes.sections, teachers.sections)
