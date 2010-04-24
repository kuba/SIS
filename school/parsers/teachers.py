"""
Module for parsing teachers file.

"""
import re
import sys

from school.model import Educator


class TeachersParserError(Exception):
    pass


class TeachersParser(object):
    """
    Parser for teachers file.

    Teachers file must be maintained in following format:
        title LastName FirstName gender
    where Gender is one of two values: "M" or "F",
    for man and woman respectively.

    :ivar pattern: Compiled pattern used for parsing
                   (matching) lines from input file.
    :type pattern: _sre.SRE_Pattern

    :ivar filename: Path to parsable file
    :type filename: :class:`str`

    :ivar teachers: Dictionary of parsed teachers.
    :type teachers: :class:`dict` of :class:`school.model.Educator` objects

    """
    pattern = re.compile(r"""
                          ([.\w-]+)\s # title
                          ([\w-]+)\s # last
                          ([\w-]+)\s # first
                          (M|F)\s    # gender
                          """, re.VERBOSE + re.UNICODE)
    def __init__(self, filename):
        self.filename = filename
        self.teachers = {}

    def parse(self):
        """
        Read the :attr:`filename` and parse it.

        Parsing means matching lines for :attr:`pattern` and
        populating new :class:`school.model.Educator` objects.

        Raises :class:`TeachersParserError` when line is not matching.

        :retval: :class:`dict` of :class:`school.model.Educator` objects
        """
        self.lines = self.filename.readlines()
        for lnr, line in enumerate(self.lines):
            try:
                title, last, first, gender = self.pattern.match(line).groups()
            except AttributeError:
                raise TeachersParserError("Line is not matching: %d. %s" \
                                           % (lnr+1, line))
            if gender == 'M':
                is_male = True
            elif gender == 'F':
                is_male = False
            else:
                raise TeachersParserError("(%d) No such gender: %s. " + \
                        "Use 'M' or 'F' instead." % (lnr+1, gender))
            self.teachers[last] = Educator(title, first, last, is_male)
        return self.teachers
