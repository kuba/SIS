import re

from school.model import Educator


class TeachersParser(object):
    def __init__(self, file, autoload=True):
        self.d = file.read()

        if autoload:
            self.parse()
    
    def parse(self):
        f = re.findall(r'#(?P<short>.*)\n(?P<title>.*)\n(?P<first>.*)\n(?P<last>.*)\n(?P<gender>M|F)', self.d)
        self.teachers = {}
        
        for short, title, first, last, gender in f:
            gender = gender == 'M' and True or False
            self.teachers[short] = Educator(title, first, last, gender)
