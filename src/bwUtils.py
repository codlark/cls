
from dataclasses import dataclass
import re
from collections.abc import Mapping
from types import SimpleNamespace
from typing import *

from PySide6.QtGui import QImage


class bWError(Exception):
    '''base class for errors raised by brikWork'''
    def __init__(self, msg:str, /, **kwargs):
        '''msg will be formated with kwargs'''
        if 'origin' in kwargs:
            self.msg = "error in {origin}:\n\t"+msg
        elif 'layout' in kwargs:
            self.msg = "error in layout '{layout}':\n\t"+msg
        elif 'file' in kwargs:
            self.msg = "error in file '{file}':\n\t"+msg
        elif 'prop' in kwargs:
            self.msg = "error in property '{prop}' of element '{elem}:'\n\t"+msg
        elif 'elem' in kwargs:
            self.msg = "error in element '{elem}':\n\t"+msg
        else:
            self.msg = "error from unknown source:\n\t"+msg
        self.kwargs = kwargs

    @property
    def message(self):
        return self.msg.format(**self.kwargs)

class InvalidValueError(bWError):
    def __init__(self, elem, prop, value):
        super().__init__("'{value}' is not a valid value for '{prop}' property",
        elem=elem, prop=prop, value=value
        )

class InvalidArgError(bWError):
    def __init__(self, elem, prop, brik, arg, value):
        super().__init__("'{value}' is not a valid {arg} argument for brik [{brik}| ]",
        elem=elem, prop=prop, brik=brik, arg=arg, value=value
        )

class UnclosedBrikError(bWError):
    def __init__(self, elem, prop, source):
        super().__init__("'{source}' has an unclosed brik in '{prop}' property",
        elem=elem, prop=prop, source=source
        )
        
class bWSyntaxError(bWError):
    def __init__(self, msg, /, **kwargs):
        if 'origin' in kwargs:
            self.msg = "syntax error in {origin}:\n\t"+msg
        elif 'elem' in kwargs:
            self.msg = "syntax error in element '{elem}' from file '{file}':\n\t"+msg
        elif 'file' in kwargs:
            self.msg = "syntax error in file '{file}':\n\t"+msg
        else:
            self.msg = "syntax error from unknown source:\n\t"+msg
        self.kwargs = kwargs

class NoValueError(bWSyntaxError):
    def __init__(self, file, elem, name):
        super().__init__("'{name}' has no value or section",
        file=file, elem=elem, name=name)

class UnexpectedEOFError(bWSyntaxError):
    def __init__(self, file, name):
        super.__init__("unexpected EOF in '{name}'",
        file=file, name=name)

class Collection(SimpleNamespace):
    '''Used to hold generated elements'''
    def _set(self, name:str, value:Any):
        self.__dict__[name] = value
    def _get(self, name:str) -> Any:
        return self.__dict__[name]

class AttrDict():
    """AttrDict maps item access to its attributes"""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    def __repr__(self):
        return repr(self.__dict__)
    def __getitem__(self, key):
        return self.__dict__[key]
    def __setitem__(self, key, value):
        self.__dict__[key] = value
    def __contains__(self, key):
        return key in self.__dict__
    def items(self):
        return self.__dict__.items()
    def copy(self):
        "return a shallow copy of this AttrDict"
        copy = AttrDict()
        copy.__dict__.update(self.__dict__)
        return copy

class ImageGetter():
    """A static class that holds a cache of images"""
    cache = {}
    
    @staticmethod
    def getImage(name) -> QImage:
        if name not in ImageGetter.cache:
            ImageGetter.cache[name] = QImage(name)
        return ImageGetter.cache[name]
    
    @staticmethod
    def clearCache():
        ImageGetter.cache = {}

@dataclass
class Unit():
    '''Unit represents a unitized number'''
    sign: str
    num: int
    unit: str
    def toFloat(self, **data) -> float:
        'return the number as an int according to type'
        if self.unit == 'in':
            if 'dpi' in data:
                return self.num*data['dpi']
            else:
                return self.num
        elif self.unit == 'mm':
            if 'dpi' in data:
                return (self.num/25.4)*data['dpi']
            else:
                return self.num
        elif self.unit == '%':
            if 'whole' in data:
                return self.num/100*data['whole']
            else:
                return self.num
        else:
            return self.num
    
    def toInt(self, **data) -> int:
        return int(self.toFloat(**data))

    @staticmethod
    def fromStr(string, signs='-+', units=('px', 'in', 'mm')):
        """Generate a Unit from a string.
        Passing the string 'all' to units will allow the number to match any unit
        """
        #TODO use the string "any" for units to match anything
        if units == 'all':
            units = ('px', 'pt', 'in', 'mm', '%', 'x', 'deg')

        signs = r'^(?P<sign>['+signs+r']?)'
        unitRe = r'(?P<unit>(?:' + '|'.join(units) + r')?)$'
        whole = signs + r'(?P<num>\d+)' + unitRe
        flt = signs + r'(?P<num>\d*\.\d+)' + unitRe
        frac = signs + r'(?P<whole>\d+)[\./ ](?P<numer>\d+)/(?P<denom>\d+)' + unitRe
        fracOnly = signs + r'(?P<numer>\d+)/(?P<denom>\d+)' + unitRe

        if (match := re.match(whole, string)) or (match := re.match(flt, string)):
            sign = match.group('sign')
            num = float(match.group('num'))
            unit = match.group('unit')
        elif match := re.match(fracOnly, string):
            sign = match.group('sign')
            numer = match.group('numer')
            denom = match.group('denom')
            unit = match.group('unit')
            num = (int(numer)/int(denom))
        elif match := re.match(frac, string):
            sign = match.group('sign')
            whole = match.group('whole')
            numer = match.group('numer')
            denom = match.group('denom')
            unit = match.group('unit')
            num = int(whole)+(int(numer)/int(denom))
        else:
            return None
        
        if unit == '':
            unit = units[0]
        if sign == '-' and unit != '%':
            num *= -1
        return Unit(sign, num, unit)

trues = 'yes on true'.split()
falses = 'no off false 0'.split()
falses.extend((0, ''))
def asBool(string:str, err:bWError = False) -> Union[bool, Literal[None]]:
    '''tries to turn a toggle into a bool
    if a toggle isn't found raise an error if present else return None'''
    folded = string.lower()
    if folded in trues:
        return True
    elif folded in falses:
        return False
    else:
        if err:
            raise err
        else:
            return None

expansions = {
    '\\': '\\', 'n': '\n',
    't': '\t', 's': ' ',
}

def evalEscapes(string:str) -> str:
    '''converts the escape sequences in a string into their unescaped counterparts'''
    pos = 0
    accum = []
    while pos < len(string):
        char = string[pos]
        if char == '\\':
            pos += 1
            char = string[pos]
            if char in expansions:
                accum.append(expansions[char])
            else:
                accum.append(char)
        else:
            accum.append(char)
        pos += 1
    
    return build(accum)



def deepUpdate(self:Mapping, other:Mapping):
    '''like update, but if a given index is a mapping in both self and other we recurse'''
    for k, v in other.items():
        if isinstance(v, Mapping):
            if k in self and isinstance(self[k], Mapping):
                deepUpdate(self[k], other[k])
            else:
                self[k] = {}
                deepUpdate(self[k], other[k])
        else:
            self[k] = other[k]

def build(accum:list) -> str:
    '''collapse a string builder'''
    return ''.join(accum).strip()

def commaSplit(string) -> str:
    accum = []
    ret = []
    pos = 0
    char = ''
    while pos < len(string):
        char = string[pos]
        if char == '\\':
            accum.append(string[pos:pos+2])
            pos += 1
        elif char == ',':
            ret.append(build(accum))
            accum = []
        else:
            accum.append(char)
        pos += 1
    ret.append(build(accum))
    return ret

class CSVParser():
    '''Parse a csv file'''
    def __init__(self, source:str):
        '''source is the source text of a csv file to parse'''
        self.pos = 0
        self.source = source

    def processEscape(self, line, pos):
        char = line[pos+1]
        #commas get unescaped, where as all others get passed through
        #this is basically why lists don't use commas in briks
        if char == ',':
            return char
        else:
            return line[pos:pos+2]

    def parseRow(self, line):
        record = []
        pos = 0
        accum = []

        while pos < len(line):
            char = line[pos]

            if char == '\\':
                accum.append(self.processEscape(line,pos))
                pos += 1
            
            elif char == ',':
                record.append(build(accum))
                accum = []
            
            else:
                accum.append(char)
            
            pos += 1
        
        record.append(build(accum))

        return record
    
    def parseHeaders(self, line):
        headers = []
        char = ''
        accum = []
        pos = 0
        while pos < len(line):
            char = line[pos]

            if char == ',':
                name = build(accum)
                if name != '':
                    headers.append(name)
                accum = []
            
            else:
                accum.append(char)
            
            pos += 1
        
        name = build(accum)
        if name != '':
            headers.append(name)

        return headers

    
    def parseCSV(self):

        lines = self.source.splitlines()
        headers = None
        rows = []

        for line in lines:
            #skip blank lines and commas
            if re.match(r'^\s*#', line):
                continue
            elif re.match(r'^\s*$', line):
                continue

            elif headers is None:
                headers = self.parseHeaders(line)
            
            else:
                row = self.parseRow(line)
                while len(row) < len(headers):
                    row.append('')
                rows.append(row)
        
        if len(rows) == 0:
            return None
        
        sheet = []
        for row in rows:
            sheet.append(dict(zip(headers, row)))
        return sheet

        #return self.sheet

class LayoutParser():
    '''parse a layout file'''
    def __init__(self, source, filename):

        lines = source.splitlines()
        newLines = []
        for line in lines:
            if (not re.match(r'\s*#', line)) and line != '':
                newLines.append(line)
        source = '\n'.join(newLines)

        self.pos = 0
        self.string = source
        self.filename = filename



    def parseValue(self, prop):
        '''parses a single value and returns when it's ended'''
        #takes over after a :
        accum = []
        char = ''

        while self.pos < len(self.string):
            char = self.string[self.pos]

            if char == '\\':
                accum.append(self.string[self.pos:self.pos+2])
                self.pos += 1
            
            elif char in '\n;':
                if len(accum) == 0:
                    return ''
                value = build(accum)
                return value
            
            elif char == '}':
                value = build(accum)
                self.pos -= 1 #OH NO A BCKTRACK
                return value
            
            else:
                accum.append(char)

            self.pos += 1
        
        raise UnexpectedEOFError(self.filename, prop)

    def parseSection(self, elem):
        '''parses the contents of a section
        parsing includes both properties and sub sections
        don't call directly'''
        accum = []
        char = ''
        section = dict(children={})
        name = ''

        while self.pos < len(self.string):
            char = self.string[self.pos]

            if char == ':':
                name = build(accum)
                accum = []
                self.pos += 1
                section[name] = self.parseValue(name)

            elif char == '{':
                name = build(accum)
                self.pos += 1
                section['children'][name] = self.parseSection(name)
                accum = []

            elif char == '}':
                name = build(accum)
                if name != '':
                    raise NoValueError(self.filename, elem, name)
                return section
            
            elif char == '=':
                name = build(accum)
                raise bWSyntaxError("'{elem}' section can not define briks",
                elem=elem, file=self.filename)
        
            else:
                accum.append(char)

            self.pos += 1
        raise UnexpectedEOFError(self.filename, elem)

    def parseProps(self, elem):
        '''parses property only sections'''
        
        section = {}
        accum = []
        name = ''
        while self.pos < len(self.string):
            char = self.string[self.pos]

            if char == ':':
                name = build(accum)
                accum = []
                self.pos += 1
                section[name] = self.parseValue(name)
            
            elif char == '{':
                raise bWSyntaxError("'{elem}' cannot contain subsections",
                file=self.filename, elem=elem)
            
            elif char == '}':
                name = build(accum)
                if name != '':
                    raise NoValueError(self.filename, elem, name)
                return section
            
            elif char == '=':
                name = build(accum)
                raise bWSyntaxError("'{elem}' section can not define briks",
                elem=elem, file=self.filename)
            
            else:
                accum.append(char)
            
            self.pos += 1
        
        raise UnexpectedEOFError(self.filename, elem)
        

    def parseUserBriks(self):

        names = {}
        accum = []
        name = ''

        while self.pos < len(self.string):
            char = self.string[self.pos]

            if char == '=':
                name = build(accum)
                accum = []
                self.pos += 1
                names[name] = self.parseValue(name)
            
            elif char == '}':
                name = build(accum)
                if name != '':
                    raise NoValueError(self.filename, 'briks', name)
                return names
            
            elif char == ':':
                raise bWSyntaxError("'{elem}' cannot conaint properties",
                file=self.filename, elem='briks')
            
            elif char == '{':
                raise bWSyntaxError("'{elem}' cannot contain subsections",
                file=self.filename, elem='briks')

            else:
                accum.append(char)
            
            self.pos += 1
        
        raise UnexpectedEOFError(self.filename, 'briks')

    def parseNil(self, elem):
        '''parse nothing, return a string'''

        accum = []
        name = ''

        while self.pos < len(self.string):
            char = self.string[self.pos]

            if char == '\\':
                accum.append(self.string[self.pos:self.pos+2])
                self.pos += 1
            
            elif char == '}':
                return build(accum)
            
            else:
                accum.append(char)
            
            self.pos += 1
        raise UnexpectedEOFError(self.filename, elem)


    def parseLayoutFile(self) -> dict:
        """returns a parsed layout file as a dict with three items
        ['props'] holds the properties of the layout section
        ['sections'] holds the special sections
        ['elements'] holes the elements
        """

        accum = []
        layout = dict(props={}, elements={}, sections={})
        name = ''

        while self.pos < len(self.string):
            char = self.string[self.pos]
            
            if char == '{':
                name = build(accum)
                self.pos += 1
                accum = []
                if name == 'layout':
                    layout['props'] = self.parseProps(name)
                elif name in ('defaults', 'csv'):
                    layout['sections'][name] = self.parseProps(name)
                elif name == 'briks':
                    layout['sections'][name] = self.parseUserBriks()
                elif name == 'export':
                    layout['sections'][name] = self.parseSection(name)
                elif name == 'data':
                    layout['sections'][name] = self.parseNil(name)
                else:
                    layout['elements'][name] = self.parseSection(name)

            elif char == ':':
                raise bWSyntaxError("properties not allowed at the top level of a layout file",
                file=self.filename, name=build(accum))

            elif char == '=':
                raise bWSyntaxError("brik definitions not allowed at the top level of a layer file",
                file=self.filename, name=build(accum))
            
            elif char == '}':
                raise bWSyntaxError("unexpected }} near '{name}'",
                file=self.filename, name=build(accum))
            
            else:
                accum.append(char)

            self.pos += 1
        
        if len(build(accum)) > 0:
            raise bWSyntaxError("'{elem}' has no section",
            file=self.filename, elem=build(accum))
        
        return layout

class ListParser():
    '''parse a list'''

    def __init__(self, source):
        
        self.string = source.strip()
        self.pos = 1

    def parseItem(self):
        accum = []
        innerStack = []

        while self.pos < len(self.string):
            char = self.string[self.pos]

            if char == '\\':
                accum.append(self.string[self.pos:self.pos+2])
                self.pos += 1

            elif char == '(':
                innerStack.append(self.pos)
                accum.append(char)

            elif char in ':)':
                if len(innerStack) == 0:
                    return build(accum)
                else:
                    #we preserve nested lists
                    if char == ')':
                        innerStack.pop()
                    accum.append(char)

            else:
                accum.append(char)

            self.pos += 1
        #return build(accum)
        raise bWError("list '{list}' failed to propperly parse", list=self.string)

    def parse(self):
        '''turn a brikWork list into a python list, nested lists are left as text'''
        if self.string == ':':
            return []
        if self.string[0] != '(' or self.string[-1] != ')':
            return None
        ret = []

        while self.pos < len(self.string):
            ret.append(self.parseItem())
            self.pos += 1

        return ret

def makeList(lst):
    '''turn a python list into a brikWork list'''
    if lst == []:
        return ':'
    else:
        return "({})".format(':'.join(lst))

if __name__ == '__main__':

    test = '(asdf: 564564()654: bad)'

    result = ListParser(test).parse()

    print(result)