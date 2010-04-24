"""
Parse lucky numbers files.

Each line should be formatted as follows:
    %d.%m.%y - \d+
eg.:
    25.04.10 - 9

"""
import re, datetime

from school.model.meta import Session
from school.model import LuckyNumber


class ParserError(object):
    pass

pattern = re.compile('(\d{2}\.\d{2}\.\d{2}) - (\d+)')

def parse(file):
    for line in file:
        m = pattern.match(line)
        if not m:
            raise ParserError("Line doesn't match the format")

        raw_date, raw_number = m.groups()
        date = datetime.datetime.strptime(raw_date, '%d.%m.%y')
        number = int(raw_number)

        lucky = LuckyNumber(date, number)
        Session.add(lucky)
    Session.commit()
