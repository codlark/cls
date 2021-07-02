
import re
from types import SimpleNamespace
from typing import *


class brikWorkError(Exception):
    def __init__(self, msg):
        self.message = msg
        super().__init__()

class Collection(SimpleNamespace):
    '''Used to hold generated elements'''
    def _set(self, name:str, value:Any):
        self.__dict__[name] = value
    def _get(self, name:str) -> Any:
        return self.__dict__[name]
    
#in the future this may be better as subclasses or brikWorkError
errString = Collection()
errString.invalid = "'{value}' is not a valid value"
errString.invalidName = "'{value}' is not a valid {name} value"
errString.invalidFor = "'{value}' is not a valid {name} value for {element}"
errString.invalidProp = "'{name}' is not a valid property for {element}"
errString.invalidArg = "'{value}' is not a valid {arg} agument for [{brik}| ]"
errString.unclosedBrik = "unclosed brik in {source} from {prop} of {element}"

def asNum(string:str, *, err:Union[bool, str] = False) -> Union[int, Literal[None]]:
    if re.match(r'^-?\d+$', string):
        return int(string)
    elif re.match(r'^\d*(\.\d+)?in$', string):
        #FIXME this uses a hardcoded dpi
        return int(float(string[:-2])*300)
    else:
        if err:
            if type(err) == str:
                raise brikWorkError(err)
            else:
                raise brikWorkError(f"'{string}' is not a valid number")
        else:
            return None

trues = 'yes on true'.split()
falses = 'no off false 0'.split()
falses.extend((0, ''))
def asBool(string:str, err:Union[bool, str] = False) -> Union[bool, Literal[None]]:
    '''returns either a bool or None'''
    folded = string.lower()
    if folded in trues:
        return True
    elif folded in falses:
        return False
    else:
        if err:
            if type(err) == str:
                raise brikWorkError(err)
            else:
                raise brikWorkError(f"'{string}' is not a valid true/false value")
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