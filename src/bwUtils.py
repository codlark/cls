
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

def parseCSV(string:str):
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

def parseValue(ps):
    #takes over after a :
    accum = []

    char = ''

    while ps.pos < len(ps.string):
        char = ps.string[ps.pos]

        if char == '\\':
            accum.append(ps.string[ps.pos:ps.pos+2])
            ps.pos += 1
        
        elif char in '\n;':
            value = ''.join(accum).strip()
            return value
        
        else:
            accum.append(char)

        ps.pos += 1

def parseSection(ps):
    #takes over after a {
    accum = []
    char = ''
    braceStack = []

    while ps.pos < len(ps.string):
        char = ps.string[ps.pos]
        

def parseComplex(source:str, filename, elem=None):
    ps = Collection()
    ps.string = source
    ps.file = filename
    ps.elem = elem
    ps.pos = 0
    accum = []
    section = dict(children = {})
    name = ''

    char = ''

    while ps.pos < len(ps.string):
        char = ps.string[ps.pos]

        if char == '\\':
            accum.append(ps.string[ps.pos:ps.pos+2])
            ps.pos += 1

        elif char == ':':
            name = ''.join(accum).strip()
            ps.pos += 1
            section[name] = parseValue(ps)
            accum = []
        
        elif char == '{':
            name = ''.join(accum).strip()
            ps.pos += 1
            section['children'][name] = parseSection(ps)
            accum = []
        
        else:
            accum.append(char)
        
        ps.pos += 1
    return section


def parseProps(source:str, filename, elem):
    pos = 0
    char = ''
    accum = []
    lines = []
    section = {}

    #print(source)
    while pos < len(source):

        char = source[pos]
        if char == '\\':
             accum.append(source[pos:pos+2])
             pos += 1
        
        elif char in '\n;':
            line = ''.join(accum)
            if line.strip() != '':
                lines.append(line)
            accum = []
        
        else:
            accum.append(char)
        pos += 1

    if len(accum) > 0:
        line = ''.join(accum)
        if line.strip != '':
            lines.append(line)

    for line in lines:
        if ':' not in line:
            raise bWError("line '{line}' is not a valid property",
            line=line, elem=elem
            )
        name, value = line.split(':', maxsplit=1)
        section[name.strip()] = value.strip()


    return section

def parseUserBriks(source:str, filename:str):

    lines = source.splitlines()
    briks = {}

    for line in lines:
        if '=' not in line:
            raise bWError("line '{line}' is not a valid brik definition",
            line=line, layout=filename)
        name, value = line.split('=', maxsplit=1)
        #down the line this is where parametized user briks would be defined as well
        briks[name.strip()] = value.strip()

    return briks


def parseLayoutFile(source:str, filename:str) -> dict:
    lines = source.splitlines()
    newLines = []
    for line in lines:
        if (not re.match(r'\s*#', line)) and line != '':
            newLines.append(line)
    source = '\n'.join(newLines)

    #section: name "{" lines "}"
    #layout: section+

    pos = 0 #pos in string
    char = '' #current char
    name = '' #section name
    inSection = False #if we're in a section
    accum = [] #the string currently being built
    storage = {} # where we stick sections after they're built
    braceStack = [] #used to keep track of curly brace pairs found in sections

    while pos < len(source):
        char = source[pos]

        if inSection:
            if char == '\\':
                #escape
                accum.append(source[pos:pos+2])
                pos += 1
            elif char == '{':
                #keep track of braces to make sure they're balanced
                braceStack.append(pos)
                accum.append(char)
            elif char == '}':
                if len(braceStack) == 0:
                    #end of section
                    storage[name] = ''.join(accum).strip()
                    accum = []
                    name = ''
                    inSection = False
                else:
                    braceStack.pop()
                    accum.append(char)

            else:
                accum.append(char)
        
        else:
            if char == '\\':
                #escape
                accum.append(source[pos:pos+2])
                pos += 1
            elif char == '{':
                #begin section
                name = ''.join(accum).strip()
                accum = []
                inSection = True
            else:
                #anything else
                accum.append(char)
        
        pos += 1
    if len(braceStack) != 0 or name != '':
        raise bWError("section '{name}' is not closed",
        layout=filename, name=name)
    elif len(storage) == 0:
        raise bWError("could not find a layout in this file",
        file=filename)

    layout = {}

    for name, data in storage.items():
        if name == 'layout':
            layout[name] = parseProps(data, filename, name)
        elif name == 'briks':
            layout[name] = parseUserBriks(data, filename)
        elif name == 'data':
            layout[name] = data
        else:
            layout[name] = parseProps(data, filename, name)
    
    return layout

