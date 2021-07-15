
import re
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
    

def asNum(string:str, *, err:Union[bool, bWError] = False) -> Union[int, Literal[None]]:
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
