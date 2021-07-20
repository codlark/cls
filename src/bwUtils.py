
import re
import collections.abc
from collections import UserDict
from types import SimpleNamespace
from typing import *


class bWError(Exception):

    def __init__(self, msg, /, **kwargs):
        if 'origin' in kwargs:
            self.msg = "{origin}:\n\t"+msg
        elif 'layout' in kwargs:
            self.msg = "layout '{layout}':\n\t"+msg
        elif 'file' in kwargs:
            self.msg = "file '{file}':\n\t"+msg
        elif 'prop' in kwargs:
            self.msg = "property '{prop}' in element '{elem}:'\n\t"+msg
        elif 'elem' in kwargs:
            self.msg = "element '{elem}':\n\t"+msg
        else:
            self.msg = "unknown error source:\n\t"+msg
        self.kwargs = kwargs


    @property
    def message(self):
        return self.msg.format(**self.kwargs)

# I actually want to make this not even an error, it just gets ignored
class InvalidPropError(bWError):
    def __init__(self, elem, prop):
        super().__init__("'{prop}' is not a valid property for this element", 
        elem=elem, prop=prop
        )
    
class InvalidValueError(bWError):
    def __init__(self, elem, prop, value):
        super().__init__("'{value}' is not a valid value for this property",
        elem=elem, prop=prop, value=value
        )

class InvalidArgError(bWError):
    def __init__(self, elem, prop, brik, arg, value):
        super().__init__("'{value}' is not a valid {arg} argument for brik [{brik}| ]",
        elem=elem, prop=prop, brik=brik, arg=arg, value=value
        )

class UnclosedBrikError(bWError):
    def __init__(self, elem, prop, source):
        super().__init__("'{source}' has an unclosed brik",
        elem=elem, prop=prop, source=source
        )
        

class Collection(SimpleNamespace):
    '''Used to hold generated elements'''
    def _set(self, name:str, value:Any):
        self.__dict__[name] = value
    def _get(self, name:str) -> Any:
        return self.__dict__[name]


class AttrDict(UserDict):
    def __getattr__(self, attr):
        return self[attr]

def asNum(string:str, *, err:bWError = False) -> Union[int, Literal[None]]:
    if re.match(r'^-?\d+$', string):
        return int(string)
    elif re.match(r'^\d*(\.\d+)? *in$', string):
        #FIXME this uses a hardcoded dpi
        #I'll need to get context in here somehow lol
        return int(float(string[:-2].strip())*300)
    else:
        if err:
            raise err
        else:
            return None

trues = 'yes on true'.split()
falses = 'no off false 0'.split()
falses.extend((0, ''))
def asBool(string:str, err:Union[bool, bWError] = False) -> Union[bool, Literal[None]]:
    '''returns either a bool or None'''
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
    def repl(m):
        c = m.group(1)
        return expansions.get(c, c)
        #return self.expansions[m.group(0)]
    return re.sub(r'\\(.)', repl, string)

def deepUpdate(self, other):
    '''like update, but if any mappings are found in other their match in self
    is updated instead of overwritten'''
    for k, v in other.items():
        if isinstance(v, collections.abc.Mapping):
            if k in self and isinstance(self[k], collections.abc.Mapping):
                deepUpdate(self[k], other[k])
            else:
                self[k] = {}
                deepUpdate(self[k], other[k])
        else:
            self[k] = other[k]

def build(accum:list) -> str:
    '''collapse a string builder'''
    return ''.join(accum).strip()

def parseCSV(string:str) -> list:
    '''parses csv data according to the csv flavor used by brikWork'''
    lines = string.strip().split('\n')

    cleanLines = []
    for line in lines:
        if (not re.match(r'\s*#', line)) and line != '':
            cleanLines.append(line)

    if len(cleanLines) < 2:
        return None

    headerLine, *lines = cleanLines

    headers = [h.strip() for h in headerLine.split(',') if h != '']
    numHeaders = len(headers)
    sheet = []
    
    for line in lines:
        record = []
        c = 0
        char = ''
        cell = []
        
        if line == '':
            continue

        while c < len(line):
            char = line[c]
            
            if char == '\\':
                cell.append(line[c:c+2])
                c += 2

            elif char == ',':
                record.append(''.join(cell).strip())
                cell = []
                if len(record)+1 == numHeaders:
                    #we break early so thre rest of the text can become the final cell
                    break
                c += 1
            
            else:
                cell.append(char)
                c += 1

        record.append(line[c+1:].strip())
        if numHeaders > 1:
            sheet.append(dict(zip(headers, record)))
        else:
            sheet.append({headers[0]: line.strip()})
    return sheet

def parseValue(ps, prop):
    '''parses a single value and returns when it's ended'''
    #takes over after a :
    accum = []
    char = ''

    while ps.pos < len(ps.string):
        char = ps.string[ps.pos]

        if char == '\\':
            accum.append(ps.string[ps.pos:ps.pos+2])
            ps.pos += 1
        
        elif char in '\n;':
            value = build(accum)
            return value
        
        if char == '}':
            value = build(accum)
            ps.pos -= 1 #OH NO
            return value
        
        else:
            accum.append(char)

        ps.pos += 1
    
    raise bWError("syntax error, unexpected EOF while reading value '{value}' for '{name}'",
    file=ps.filename, value=build(accum), name=prop)

def parseSection(ps, elem, top=False):
    '''parses the contents of a section
    if top is True the section is ended at end of string
    if Flase, the default, the section is ended on }
    parsing includes both properties and sub sections
    don't call directly'''
    accum = []
    char = ''
    section = dict(children={})
    name = ''

    while ps.pos < len(ps.string):
        char = ps.string[ps.pos]

        if char == '\\':
            accum.append(ps.string[ps.pos:ps.pos+2])
            ps.pos += 1
        
        elif char == ':':
            name = build(accum)
            accum = []
            ps.pos += 1
            section[name] = parseValue(ps, name)

        elif char == '{':
            name = build(accum)
            ps.pos += 1
            section['children'][name] = parseSection(ps, name)
            accum = []

        elif char == '}':
            name = build(accum)
            if name != '':
                raise bWError("syntax error parsing '{elem}', '{name}' has no value or section",
                file=ps.filename, elem=elem, name=name)
            return section
    
        else:
            accum.append(char)

        ps.pos += 1
    if not top:
        raise bWError("syntax error parsing '{name}', unexpected EOF",
        file=ps.filename, name=elem)

def parseProps(ps, elem):
    '''parses property only sections'''
    
    section = {}
    accum = []
    name = ''
    while ps.pos < len(ps.string):
        char = ps.string[ps.pos]

        if char == '\\':
            accum.append(ps.string[ps.pos:ps.pos+2])
            ps.pos += 1
        
        elif char == ':':
            name = build(accum)
            accum = []
            ps.pos += 1
            section[name] = parseValue(ps, name)
        
        elif char == '{':
            name = build(accum)
            if len(name) > 0:
                raise bWError("syntax error parsing '{elem}', '{name}' has no value",
                file=ps.filename, elem=elem, name=name)
            raise bWError("syntax error, '{elem}' cannot contain subsections",
            file=ps.filename, elem=elem)
        
        elif char == '}':
            name = build(accum)
            if name != '':
                raise bWError("syntax error parsing '{elem}', '{name}' has no value",
                file=ps.filename, elem=elem, name=name)
            return section
        
        else:
            accum.append(char)
        
        ps.pos += 1
    
    raise bWError("syntax error parsing '{name}', unexpected EOF",
    file=ps.filename, name=elem)
      

def parseUserBriks(ps):

    names = {}
    accum = []
    name = ''

    while ps.pos < len(ps.string):
        char = ps.string[ps.pos]

        if char == '\\':
            accum.append(ps.string[ps.pos:ps.pos+2])
            ps.pos += 1
        
        elif char == '=':
            name = build(accum)
            accum = []
            ps.pos += 1
            names[name] = parseValue(ps, name)
        
        elif char == '}':
            name = build(accum)
            if name != '':
                raise bWError("syntax error parsing 'briks', '{name}' has no value",
                file=ps.filename, name=name)
            return names

        else:
            accum.append(char)
        
        ps.pos += 1
    
    raise bWError("syntax error parsing 'briks', unexpected EOF",
    file=ps.filename)

def parseNil(ps, elem):
    '''parse nothing, return a string'''

    accum = []
    name = ''

    while ps.pos < len(ps.string):
        char = ps.string[ps.pos]

        if char == '\\':
            accum.append(ps.string[ps.pos:ps.pos[1]])
            ps.pos += 1
        
        elif char == '}':
            return build(accum)
        
        else:
            accum.append(char)
        
        ps.pos += 1
    raise bWError("syntax error parsing '{elem}', unexpected EOF",
    file=ps.filename, elem=elem)


def parseLayoutFile(source, filename):
    lines = source.splitlines()
    newLines = []
    for line in lines:
        if (not re.match(r'\s*#', line)) and line != '':
            newLines.append(line)
    source = '\n'.join(newLines)

    ps = Collection(
        pos = 0,
        string = source,
        filename = filename,
    )

    accum = []
    layout = {}
    name = ''

    while ps.pos < len(ps.string):
        char = ps.string[ps.pos]

        if char == '\\':
            accum.append(ps.string[ps.pos:ps.pos+2])
            ps.pos += 1
        
        elif char == '{':
            name = build(accum)
            ps.pos += 1
            accum = []
            if name in ('layout', 'defaults'):
                layout[name] = parseProps(ps, name)
            elif name == 'briks':
                layout[name] = parseUserBriks(ps)
            elif name == 'data':
                layout[name] = parseNil(ps, name)
            else:
                layout[name] = parseProps(ps, name)

        elif char == ':':
            raise bWError("syntax error near '{name}', properties not allow at the top level of a layout file",
            file=ps.filename, name=build(accum))
        
        elif char == '}':
            raise bWError("syntax error near '{name}', unexpected }}",
            file=ps.filename, name=build(accum))
        
        else:
            accum.append(char)

        ps.pos += 1
    
    if len(build(accum)) > 0:
        raise bWError("syntax error, '{name}' has no section",
        file=ps.filename, name=build(accum))
    
    return layout


if __name__ == '__main__':
    test = '''
layout {
    width: 5
}
briks {
    foo = but
}
foo {
    x:2
}
data {
yes, no
yellow, everything else
}
'''
    test2 = '''{
    x: 1
    y:2
}
'''

    try:
        print(parseLayoutFile(test, '<test>'))
    except bWError as e:
        print(e.message)