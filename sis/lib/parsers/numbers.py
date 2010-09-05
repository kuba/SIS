"""Tools for parsing luky number files."""
import re
import datetime

from sis.model import LuckyNumber
from sis.lib.parsers.base import LineError


class LuckyNumberParser(object):
    """
    Parser for lucky numbers file.

    Each line of the file must be ``%Y-%m-%d - %(number)s``, eg::
        2010-12-28 - 1

    """
    pattern = re.compile('(\d{4}-\d{2}-\d{2}) - (\d+)')

    def __init__(self, lines):
        self.dates = []
        self.lines = lines

    def parse_line(self, lnr, line):
        """Parse single line."""
        m = self.pattern.match(line)
        if not m:
            raise LineError(lnr, line, "Doesn't match the format")
        raw_date, raw_number = m.groups()

        if raw_date in self.dates:
            raise LineError(lnr, line, "Date '%s' occured more than once" \
                            % raw_date)
        self.dates.append(raw_date)

        date = datetime.datetime.strptime(raw_date, '%Y-%m-%d').date()
        number = int(raw_number)

        return LuckyNumber(date, number)

    def __iter__(self):
        """Parse file."""
        for lnr, line in enumerate(self.lines):
            yield self.parse_line(lnr + 1, line)
