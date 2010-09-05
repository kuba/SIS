"""Tools parsing teachers file."""
import re

from sis.lib.parsers.base import LineError
from sis.model import Educator


class TeachersParser(object):
    """
    Parser for teachers file.

    Teachers file must be maintained in following format::
        title LastName FirstName gender
    where ``gender`` is one of two values: "M" or "F",
    for man and woman respectively.

    :ivar pattern: Compiled pattern used for parsing
                   (matching) lines from input file.
    :type pattern: _sre.SRE_Pattern

    :ivar lines: Lines of the file
    :type lines: file-like object

    """
    pattern = re.compile(r"""
                          ([.\w-]+)\s # title
                          ([\w-]+)\s # last
                          ([\w-]+)\s # first
                          (M|F)\s    # gender
                          """, re.VERBOSE + re.UNICODE)
    def __init__(self, lines):
        self.lines = lines

    def parse_line(self, lnr, line):
        m = self.pattern.match(line)
        if not m:
            raise TeachersParserError("Line is not matching: %d. %s" \
                               % (lnr, line))
        title, last, first, gender = m.groups()

        if gender == 'M':
            is_male = True
        else:
            is_male = False

        return Educator(title, first, last, is_male)

    def __iter__(self):
        """
        Read the :attr:`filename` and parse it.

        Parsing means matching lines for :attr:`pattern` and
        populating new :class:`sis.model.Educator` objects.

        Raises :class:`TeachersParserError` when line is not matching.

        :retval: :class:`dict` of :class:`sis.model.Educator` objects

        """
        for lnr, line in enumerate(self.lines):
            yield self.parse_line(lnr + 1, line)
