import re

from school.model import Educator


class TeachersParser(object):
    pattern = re.compile(r"""
                         \#(?P<short>.*)\n
                          (?P<title>.*)\n
                          (?P<first>.*)\n
                          (?P<last>.*)\n
                          (?P<gender>M|F)""", re.VERBOSE)
    def __init__(self, filename):
        self.filename = filename
        self.teachers = {}
    
    def parse(self):
        self.data = self.filename.read()
        teachers = self.pattern.findall(self.data)
        
        for short, title, first, last, gender in teachers:
            gender = gender == 'M' and True or False
            self.teachers[short] = Educator(title, first, last, gender)
        return self.teachers
