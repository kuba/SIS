import re

from school.model import Educator


def parse_teachers(file):
    d = file.read()
    f = re.findall(r'#(?P<short>.*)\n(?P<title>.*)\n(?P<first>.*)\n(?P<last>.*)\n(?P<gender>M|F)', d)
    teachers = {}
    for short, title, first, last, gender in f:
        gender = gender == 'M' and True or False
        teachers[short] = Educator(title, first, last, gender)
    return teachers
