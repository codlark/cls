### data.py ###

from . import err
from . import util
import re
from dataclasses import dataclass

__all__ = ['Unit', 'ListParser', 'asBool', 'evalEscapes', 'makeList']


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
        elif self.unit == 'pt':
            if 'dpi' in data:
                return (self.num/72)*data['dpi']
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
def asBool(string:str, err:err.CLSError = False) -> bool | None:
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
    '<': '&lt;', '>': '&gt;', '&': '&amp;',
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
    
    return util.build(accum)


class ListParser():
    '''parse a list'''

    def __init__(self, source, elem, prop):
        
        self.string = source.strip()
        self.pos = 1
        self.elem = elem
        self.prop = prop

    def parseItem(self):
        accum = []
        innerStack = []

        while self.pos < len(self.string):
            char = self.string[self.pos]

            if char == '\\':
                accum.append(self.string[self.pos:self.pos+2])
                self.pos += 1

            elif char in '([':
                innerStack.append(char)
                accum.append(char)

            elif char == ']':
                if len(innerStack) == 0:
                    raise err.ImbalancedDelimError(self.elem, self.prop, self.string)
                opener = innerStack.pop()
                if opener == '(':
                    raise err.ImbalancedDelimError(self.elem, self.prop, self.string)
                accum.append(char)
                    
            elif char in ',)':
                if len(innerStack) == 0:
                    if self.pos != len(self.string)-1 and char == ')':
                        #if we see a ) without an opener and it's notthe last character of the string
                        raise err.ImbalancedDelimError(self.elem, self.prop, self.string)
                    
                    item = util.build(accum)
                    if char == ')' and item == '':
                        return None
                    else:
                        return item
                else:
                    #we preserve nested lists
                    if char == ')':
                        opener = innerStack.pop()
                        if   opener == '[':
                            raise err.ImbalancedDelimError(self.elem, self.prop, self.string)
                    accum.append(char)

            else:
                accum.append(char)

            self.pos += 1
        #return build(accum)
        raise err.ImbalancedDelimError(self.elem, self.prop, self.string)

    def parse(self):
        '''turn a CLS list into a python list, nested lists are left as text'''
        if self.string == ':':
            return []
        if self.string[0] != '(' or self.string[-1] != ')':
            return None
        contents = []

        while self.pos < len(self.string):
            item = self.parseItem()
            if item is not None:
                contents.append(item)
            self.pos += 1

        return contents

def makeList(lst):
    '''turn a python list into a CLS list'''
    if lst == []:
        return ':'
    else:
        return "({})".format(':'.join(lst))