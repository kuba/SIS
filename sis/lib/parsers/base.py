"""Base parsing tools."""
import types
from codecs import open


class ParserError(Exception):
    """Base error for parsing."""
    def __init__(self, message):
        self.message = message
        super(ParserError, self).__init__()

    def __repr__(self):
        return "<%s('%s')>" % (self.__class__.__name__, self.message)

    def __str__(self):
        return self.message


class LineError(ParserError):
    """
    Line paring error.

    :ivar number: Number of the line.
    :type number: int

    :ivar line: The data.
    :type line: unicode

    """
    def __init__(self, number, line, message):
        self.number = number
        self.line = line
        super(LineError, self).__init__(message)

    def __repr__(self):
        name = self.__class__.__name__
        return "<%s(%d, '%s')>" % (name, self.number, self.message)

    def __str__(self):
        return "Line %d :: %s :: %s" % (self.number, self.message,
                                        self.line.encode('utf-8'))


class Parser(object):
    """Base parser."""
    def __init__(self, file, autoload=True, encoding='utf-8'):
        if type(file) is types.FileType:
            # Accept normal files
            self.lines = file.readlines()
        elif type(file) is types.StringType or \
             type(file) is types.UnicodeType:
                 # Open file from string
                 self.lines = open(file, 'r', encoding).readlines()
        elif type(file) is types.ListType:
            # Given lines
            self.lines = file
        else:
            raise ParserError('Unsupported file type.')

        if autoload:
            self.parse()

    def parse(self):
        for lnr, line in enumerate(self.lines):
            line = line.strip()
            try:
                self.parse_line(line)
            except ParserError as e:
                raise LineError(lnr, line, e)

    def parse_line(self, line):
        raise NotImplementedError()
