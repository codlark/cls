import re
from collections import ChainMap
from types import SimpleNamespace
from typing import Union, Callable, Collection
from bwUtils import *

class BrikStore():

    stdlib = {'': ''}

    @classmethod
    def addStdlib(cls, name:str, value:Union[int, str]):
        def inner(func:Callable):
            if type(func) == str:
                cls.stdlib[name] = func
            else:
                cls.stdlib[name] = (func, value)
            return func
        if type(value) == str:
            inner(value)
        else:
            return inner

    def __init__(self):
        self.briks = ChainMap({}, self.stdlib)

    def copy(self):
        new = BrikStore()
        new.briks = self.briks.new_child()
        return new

    def add(self, name:str, value:Union[int, str]):
        def inner(func:Callable):
            if type(func) == str:
                self.briks[name] = func
            else:
                self.briks[name] = (func, value)
            return func

        if type(value) == str:
            inner(value)
        else:
            return inner
    
    def formatArgs(self, **kwargs):
        kwargs['prop'] = self.briks['propertyName']
        kwargs['element'] = self.briks['elementName']
        return kwargs

    def call(self, name:str, context:Collection, args:str) -> str:
        #print(f'{name!r} : {args!r}')
        if name in self.briks:
            brik = self.briks[name]
            if type(brik) == str:
                return brik.format(args=args)
            else:
                if len(args) < brik[1]:
                    raise brikWorkError(f"not enough arguments for '{name}' in '{context.source}'")
                return brik[0](context, *args)
        else:
            return ''
        
    def parseBrikArg(self,ps) -> str:
        argB = []
        brikStack = []
        char = ''

        while ps.pos < len(ps.string):
            char = ps.string[ps.pos]

            if char == '\\':
                argB.append(ps.string[ps.pos:ps.pos+2])
                ps.pos += 2
                continue

            elif char == '[':
                brikStack.append(ps.pos)
                argB.append(char)
            
            elif char in '|]':
                if len(brikStack) == 0:
                    ps.pos -= 1
                    return ''.join(argB).strip()
                else:
                    if char == ']':
                        brikStack.pop()
                    argB.append(char)
            
            else:
                argB.append(char)

            ps.pos += 1
        
        raise brikWorkError(errString.unclosedBrik.format(
            **self.formatArgs(source=ps.string)))

    def evalBrik(self, ps) -> str:
        nameB = []
        args = []
        char = ''

        context = Collection(
            store=self,
            parse=self.parse,
            source=ps.string
        )
        while ps.pos < len(ps.string):
            char = ps.string[ps.pos]

            if char == '\\':
                nameB.append(ps.string[ps.pos:ps.pos+2])
                ps.pos += 2
                continue
                
            elif char == '|':
                ps.pos += 1
                args.append(self.parseBrikArg(ps))
            
            elif char == ']':
                return self.call(''.join(nameB).strip(), context, args)
            
            else:
                nameB.append(char)

            ps.pos += 1

        raise brikWorkError(errString.unclosedBrik.format(
            **self.formatArgs(source=ps.string)))

    def evalValue(self, string:str) -> str:
        ps = Collection()
        ps.string = string
        ps.pos = 0
        result = []

        char = ''

        while ps.pos < len(ps.string):
            char = ps.string[ps.pos]
        
            if char == '\\':
                result.append(ps.string[ps.pos:ps.pos+2])
                ps.pos += 2
                continue
                #ignore escapes
        
            elif char == '[':
                ps.pos += 1
                result.append(self.evalBrik(ps))
        
            else:
                result.append(char)
            
            ps.pos += 1

        return ''.join(result)

    def parse(self, string:str) -> str:
        '''parse() turns a value into a real usable object, and evalValue
        processes the top layer of briks, this function does the dirty work
        to make sure that there are no more briks left in the string before
        the final validation passes. It's also used by briks to get values
        that don't have anymore briks, but still have escapes incase of more
        square brackets.
        '''
        while True:
            match = re.search(r'(?<!\\)\[', string)
            if match:
                string = self.evalValue(string)
            else:
                break
        return string



###############################################################################
## BEGIN STDLIB
###############################################################################

#Most things don't neeed *args, I should make the arg definition more exact

@BrikStore.addStdlib('if', 2)
def ifBrik(context, test, true, false='', *args):

    if test[0] == '?' :
        b = asBool(comparisonMacro(context, test[1:]))
    else:
        b = asBool(context.parse(test), err=errString.invalidArg.format(
            value=test, arg='TEST', brik='if'
        ))
    if b:
        return true
    else:
        return false

@BrikStore.addStdlib('eq', 2)
def eqBrik(context, left, right, *args):
    if context.parse(left) == context.parse(right):
        return 'true'
    else:
        return 'false'

@BrikStore.addStdlib('ne', 2)
def neBrik(context, left, right, *args):
    if context.parse(left) != context.parse(right):
        return 'true'
    else:
        return 'false'

@BrikStore.addStdlib('in', 2)
def inBrik(context, value, *args):
    parsed = context.parse(value)
    for arg in args:
        if parsed == context.parse(arg):
            return 'true'
    return 'false'


@BrikStore.addStdlib('i', 1)
def italicBrik(context, string, *args):
    return f'<i>{string}</i>'

@BrikStore.addStdlib('b', 1)
def boldBrik(context, string, *args):
    return f'<b>{string}</b>'

@BrikStore.addStdlib('dup', 2)
def repeatBrik(context, times, value, *args):
    times = context.parse(times)
    times = asNum(times, err=errString.invalidArg.format(
        value=times, arg='TIMES', brik='dup'
    ))
    result = []
    newStore = context.store.copy()
    for i in range(times):
        newStore.add('d', str(i+1))#FIXME
        result.append(newStore.parse(value))
    return ''.join(result)
    
@BrikStore.addStdlib('capitalize', 1)
def capitalizeBrik(context, value, *args):
    value = context.parse(value)
    value = value[0].upper()+value[1:]
    def repl(m):
        return m.group(1).upper() + m.group(2)
    return re.sub(r'\b([a-z])(\w{3,})\b', repl, value)

@BrikStore.addStdlib('upper', 1)
def upperBrik(context, value, *args):
    value = context.parse(value)
    def repl(m):
        return m.group(1).upper()
    return re.sub(r'(?<!\\)([a-z])', repl, value)
    
@BrikStore.addStdlib('lower', 1)
def upperBrik(context, value, *args):
    value = context.parse(value)
    def repl(m):
        return m.group(1).lower()
    return re.sub(r'(?<!\\)([A-Z])', repl, value)

@BrikStore.addStdlib('substring', 3)
def subBrik(context, value, start, length, *args):
    value = context.parse(value)
    start = asNum(context.parse(start), err=errString.invalidArg.format(
        value=start, arg='START', brik='substring'
    ))-1
    length = asNum(context.parse(length), err=errString.invalidArg.format(
        value=length, arg='LENGTH', brik='substring'
    ))
    return value[start:start+length]

@BrikStore.addStdlib('/', 1)
def expansionMacro(context, value, *args):
    value = context.parse(value)
    return evalEscapes(value)

@BrikStore.addStdlib('?', 1)
def comparisonMacro(context, value, *args):
    nValue = context.parse(value)
    try:
        left, op, right = re.split(r'(==|!=|<=?|>=?)', nValue, maxsplit=1)
    except ValueError as e:
        raise brikWorkError(f"A comparison could not be found in '{value}'")
    left = asNum(left.strip(), err=errString.invalidArg.format(
        value=left, arg='OPERAND', brik='?'
    ))
    right = asNum(right.strip(), err=errString.invalidArg.format(
        value=right, arg='OPERAND', brik='?'
    ))
    op = op.strip()
    if op == '==':
        final = left == right
    elif op == '!=':
        final = left != right
    elif op == '>':
        final = left > right
    elif op == '>=':
        final = left >= right
    elif op == '<':
        final = left < right
    elif op == '<=':
        final = left <= right
    else:
        raise brikWorkError(f"A comparison could not be found in '{value}'")
    if final:
        return 'true'
    else:
        return 'false'

def mathMacro(context, value, *args):
    tokens = [s.strip() for s in re.split(r'([-+*/%])', value)]
    
    operand = True
    #true if were looking for an operand, false otherwise

    for token in tokens:
        
        if operand:
            pass
            #turn into number
            #apply to acc


#def brik(context, arg, *args):
#    '''
#    context is a namespace holding
#     - elem : a copy of the element
#     - evalBriks() : a function to parse a value
#     - evalEscapes() : a function to turn escapes into their escaped value

#    '''
#    pass



##this all would work to bind the propery name to the attr name
## right at the definition sight, but I'd prolly need to flesh out
## the bas element class a little to make it work pretty
#props = {}

#def prop(name):
#    return name

#def thing(func:Callable):
#    if func.__annotations__:
#        for a,p in func.__annotations__.items():
#            props[p] = a
#    return func

#class Parent():
#    @thing
#    def __init__(self, x:prop('x')=5, y:prop('y')=6, **kwargs):
#        self.x = x
#        self.y = y
#        self._extra = kwargs
    
#class Child(Parent):
#    @thing
#    def __init__(self, contents:prop('text')='', **kwargs):
#        self.contents = contents
#        super().__init__(**kwargs)
