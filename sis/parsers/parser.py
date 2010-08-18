import types
from codecs import open


class ParserError(Exception):
    pass


class LineError(ParserError):
    def __init__(self, line_number, data, e=None):
        print data
        self.line_number = line_number
        self.data = data
        self.e = e

    def __str__(self):
        s = "%d. (%s)" % (self.line_number, self.data)
        if self.msg:
            s += " :: %r" % self.e
        return s


class Parser(object):
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
            self.lnr = lnr
            self.line = line.strip()
            try:
                self.parse_line()
            except ParserError as e:
                raise LineError(self.lnr, self.line, e)

    def parse_line(self):
        raise NotImplementedError()
