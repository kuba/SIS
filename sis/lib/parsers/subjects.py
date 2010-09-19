"""Subjects parser."""
from xml.etree.ElementTree import ElementTree
from sis.model import Subject

class SubjectsParser(object):
    """Subjects file parser."""
    def __init__(self, path):
        self.tree = ElementTree()
        self.tree.parse(path)

    def __iter__(self):
        for subject in self.tree.getiterator('subject'):
            long = subject.find('long').text
            short = subject.find('short').text
            yield Subject(long, short)
