### parsers.py ###

import re
from utils import *

__all__ = ['CSVParser', 'LayoutParser']


class CSVParser():
    '''Parse a csv file'''
    def __init__(self, source:str):
        '''source is the source text of a csv file to parse'''
        self.pos = 0
        self.source = source

    def parseRow(self, line):
        record = []
        pos = 0
        accum = []
        stack = []

        while pos < len(line):
            char = line[pos]

            if char == '\\':
                accum.append(line[pos:pos+2])
                pos += 1

            elif char in '([':
                stack.append(char)
                accum.append(char)
            
            elif char in '])':
                stack.pop()
                accum.append(char)

            elif char == ',':
                if len(stack) == 0:
                    record.append(build(accum))
                    accum = []
                else:
                    accum.append(char)
            
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
        
        raise err.UnexpectedEOFError(self.filename, prop)

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
                    raise err.NoValueError(self.filename, elem, name)
                return section
            
            elif char == '=':
                name = build(accum)
                raise err.CLSSyntaxError("'{elem}' section can not define macros",
                elem=elem, file=self.filename)
        
            else:
                accum.append(char)

            self.pos += 1
        raise err.UnexpectedEOFError(self.filename, elem)

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
                raise err.CLSSyntaxError("'{elem}' cannot contain subsections",
                file=self.filename, elem=elem)
            
            elif char == '}':
                name = build(accum)
                if name != '':
                    raise err.NoValueError(self.filename, elem, name)
                return section
            
            elif char == '=':
                name = build(accum)
                raise err.CLSSyntaxError("'{elem}' section can not define macros",
                elem=elem, file=self.filename)
            
            else:
                accum.append(char)
            
            self.pos += 1
        
        raise err.UnexpectedEOFError(self.filename, elem)
        

    def parseUserMacros(self):

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
                    raise err.NoValueError(self.filename, 'macros', name)
                return names
            
            elif char == ':':
                raise err.CLSSyntaxError("'{elem}' cannot conaint properties",
                file=self.filename, elem='macros')
            
            elif char == '{':
                raise err.CLSSyntaxError("'{elem}' cannot contain subsections",
                file=self.filename, elem='macros')

            else:
                accum.append(char)
            
            self.pos += 1
        
        raise err.UnexpectedEOFError(self.filename, 'macros')

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
        raise err.UnexpectedEOFError(self.filename, elem)


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
                elif name == 'macros':
                    layout['sections'][name] = self.parseUserMacros()
                elif name == 'export':
                    layout['sections'][name] = self.parseSection(name)
                elif name == 'data':
                    layout['sections'][name] = self.parseNil(name)
                else:
                    layout['elements'][name] = self.parseSection(name)

            elif char == ':':
                raise err.CLSSyntaxError("properties not allowed at the top level of a layout file",
                file=self.filename, name=build(accum))

            elif char == '=':
                raise err.CLSSyntaxError("macro definitions not allowed at the top level of a layout file",
                file=self.filename, name=build(accum))
            
            elif char == '}':
                raise err.CLSSyntaxError("unexpected }} near '{name}'",
                file=self.filename, name=build(accum))
            
            else:
                accum.append(char)

            self.pos += 1
        
        if len(build(accum)) > 0:
            raise err.CLSSyntaxError("'{elem}' has no section",
            file=self.filename, elem=build(accum))
        
        return layout


