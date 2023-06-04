import os
import re
import random
from collections import ChainMap, deque
from typing import Union, Callable, Collection
import operator
from utils import *

__all__ = ['MacroStore']


class MacroStore():

    stdlib = {'': ''}

    @classmethod
    def addStdlib(cls, name:str, value:Union[int, str]):
        '''with two strings, add text macro
        with a string and an int, use as a decorator to add a function'''
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
        self.macros = ChainMap({}, self.stdlib)

    def copy(self):
        '''make a copy of this MacroStore'''
        new = MacroStore()
        new.macros = self.macros.new_child()
        return new

    def add(self, name:str, value:Union[list[int], str]):
        '''with two strings, add text macro
        with a string and an int, use as a decorator to add a function'''
        def inner(func:Callable):
            if type(func) == str:
                self.macros[name] = func
            else:
                self.macros[name] = (func, value)
            return func

        if type(value) == str:
            inner(value)
        else:
            return inner

    def call(self, name:str, context:Collection, args:str) -> str:
        '''call a macro by name'''
        #print(f'{name!r} : {args!r}')
        if name in self.macros:
            macro = self.macros[name]
            if type(macro) == str:
                return macro
            else:
                func, signature = macro
                if type(signature) is int:
                    if len(args) != signature:
                        raise CLSError('wrong number of arguments for [{macro}| ], expected {num} got {badnum}',
                        elem=context.elem, prop=context.prop, macro=name, num=signature, badnum=len(args)
                        )
                    return func(context, *args)

                else:
                    min, max = signature
                    if len(args) < min:
                        raise CLSError('too few arguments for [{macro}| ], expected at least {num} got {badnum}',
                        elem=context.elem, prop=context.prop, macro=name, num=min, badnum=len(args)
                        )
                    elif len(args) > max:
                        raise CLSError('too many arguments for [{macro}| ], expected at most {num} got {badnum}',
                        elem=context.elem, prop=context.prop, macro=name, num=max, badnum=len(args)
                        )
                    return func(context, *args)
        else:
            return ''
        
    def parseMacroArg(self, ps, context) -> str:
        argB = []
        macroStack = []
        char = ''

        while ps.pos < len(ps.string):
            char = ps.string[ps.pos]

            if char == '\\':
                argB.append(ps.string[ps.pos:ps.pos+2])
                ps.pos += 1

            elif char in '[(':
                macroStack.append(char)
                argB.append(char)
            
            elif char == ')':
                if len(macroStack) == 0:
                    #we never saw the opener
                    raise ImbalancedDelimError(context.elem, context.prop, ps.string)
                opener = macroStack.pop()
                if opener == '[':
                    raise ImbalancedDelimError(context.elem, context.prop, ps.string)
                argB.append(char)

            elif char in ',|]':
                if len(macroStack) == 0:
                    ps.pos -= 1 #backtrack so evalMacro can see the comma/bracket
                    return ''.join(argB).strip()
                else:
                    if char == ']':
                        opener = macroStack.pop()
                        if opener == '(':
                            raise ImbalancedDelimError(context.elem, context.prop, ps.string)
                    argB.append(char)
            
            else:
                argB.append(char)

            ps.pos += 1
        
        raise ImbalancedDelimError(context.elem, context.prop, ps.string)


    def evalMacro(self, ps) -> str:
        '''evalMacro parses out a macro then calls it with its arguments and context
        context includes:
         - store - this macroStore object
         - parse - a reference to the parse method of this object
         - source - the string the macro was found in, used for errors
         - prop - the property this macro was found in, used for errors
         - elem - the element this macro was found in, used for errors'''
        nameB = []
        args = []
        char = ''

        context = Collection(
            store=self,
            parse=self.parse,
            source=ps.string,
            prop = self.macros['propertyName'],
            elem = self.macros['elementName']
        )
        while ps.pos < len(ps.string):
            char = ps.string[ps.pos]
            if char == '\\':
                nameB.append(ps.string[ps.pos:ps.pos+2])
                ps.pos += 1
                
            elif char in ',|':
                ps.pos += 1
                args.append(self.parseMacroArg(ps, context))
            
            elif char == ']':
                name = build(nameB)
                context.name = name
                return self.call(name, context, args)
            
            elif char == ')': #? might be wrong, or might need a stack
                raise ImbalancedDelimError(context.elem, context.prop, ps.string)

            else:
                nameB.append(char)

            ps.pos += 1
        raise UnclosedMacroError(context.elem, context.prop, ps.string)

    def evalValue(self, string:str) -> str:
        '''looks at a string, and if it finds a macro, parses it'''
        ps = Collection()
        ps.string = string
        ps.pos = 0
        result = []

        char = ''

        while ps.pos < len(ps.string):
            char = ps.string[ps.pos]
        
            if char == '\\':
                result.append(ps.string[ps.pos:ps.pos+2])
                ps.pos += 1
                #ignore escapes
        
            elif char == '[':
                ps.pos += 1
                result.append(self.evalMacro(ps))
        
            else:
                result.append(char)
            
            ps.pos += 1

        return ''.join(result)

    def parse(self, string:str) -> str:
        '''parse() turns a value into a real usable object, and evalValue
        processes the top layer of macros, this function does the dirty work
        to make sure that there are no more macros left in the string before
        the final validation passes. It's also used by macros to get values
        that don't have anymore macros, but still have escapes incase of more
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

 
@MacroStore.addStdlib('if', (2,3))
def ifMacro(context, test, true, false=''):

    if test[0] == '?' :
        b = asBool(comparisonMacro(context, test[1:]))
    else:
        b = asBool(context.parse(test), err=InvalidArgError(
            context.elem, context.prop, 'if', 'TEST', test
        ))
    if b:
        return true
    else:
        return false

@MacroStore.addStdlib('eq', 2)
def eqMacro(context, left, right):
    if context.parse(left) == context.parse(right):
        return 'true'
    else:
        return 'false'

@MacroStore.addStdlib('ne', 2)
def neMacro(context, left, right):
    if context.parse(left) != context.parse(right):
        return 'true'
    else:
        return 'false'

@MacroStore.addStdlib('in', (2, 99))
def inMacro(context, value, *args):
    parsed = evalEscapes(context.parse(value))
    if len(args) == 0:
        return 'false'
    parsedList = ListParser(args[0], context.elem, context.prop).parse()
    if parsedList == None:
        parsedList = args
    for arg in parsedList:
        if parsed == evalEscapes(context.parse(arg)):
            return 'true'
    return 'false'

@MacroStore.addStdlib('not', 1)
def notMacro(context, value):
    parseVal = context.parse(value)
    boolVal = asBool(parseVal)
    if boolVal is not None:
        if boolVal:
            return 'false'
        else:
            return 'true'
    else:
        return 'false'

@MacroStore.addStdlib('either', 2)
def eitherMacro(context, left, right):
    parsedVal = context.parse(left)
    if asBool(parsedVal) is False:
        return right
    else:
        return left

@MacroStore.addStdlib('i', 1)
def italicMacro(context, string):
    return f'<i>{string}</i>'

@MacroStore.addStdlib('b', 1)
def boldMacro(context, string):
    return f'<b>{string}</b>'

@MacroStore.addStdlib('s', 1)
def strikedMacro(context, string):
    return f'<s>{string}</s>'

@MacroStore.addStdlib('u', 1)
def underlineMacro(context, string):
    return f'<u>{string}</u>'


@MacroStore.addStdlib('dup', 2)
def repeatMacro(context, times, value):
    nTimes = context.parse(times)
    unit = Unit.fromStr(nTimes, signs='+0', units=('',))
    if unit is None:
        raise InvalidArgError(context.elem, context.prop, 'dup', 'TIMES', nTimes)
    times = unit.toInt()
    ofs = 0 if unit.sign == '0' else 1
    result = []
    newStore = context.store.copy()
    for i in range(times):
        newStore.add('d', str(i+ofs))
        result.append(newStore.parse(value))
    return ''.join(result)

@MacroStore.addStdlib('for-each', 2)
def forMacro(context, lst, body):
    lst = context.parse(lst)
    parsedList = ListParser(lst, context.elem, context.prop).parse()
    if parsedList == None:
        raise InvalidArgError(context.elem, context.prop, 'for-each', 'LIST', lst)
    result = []
    newStore = context.store.copy()
    for item in parsedList:
        newStore.add('item', item)
        result.append(newStore.parse(body))
    return ''.join(result)

@MacroStore.addStdlib('capitalize', 1)
def capitalizeMacro(context, value):
    value = context.parse(value)
    value = value[0].upper()+value[1:]
    def repl(m):
        return m.group(1).upper() + m.group(2)
    return re.sub(r'\b([a-z])(\w{3,})\b', repl, value)

@MacroStore.addStdlib('upper', 1)
def upperMacro(context, value):
    value = context.parse(value)
    def repl(m):
        return m.group(1).upper()
    return re.sub(r'(?<!\\)([a-z])', repl, value)
    
@MacroStore.addStdlib('lower', 1)
def upperMacro(context, value):
    value = context.parse(value)
    def repl(m):
        return m.group(1).lower()
    return re.sub(r'(?<!\\)([A-Z])', repl, value)

@MacroStore.addStdlib('substr', 3)
def substrMacro(context, value, start, length):
    value = context.parse(value)
    
    start = context.parse(start)
    startUnit = Unit.fromStr(context.parse(start), signs='+0', units=('',))
    if startUnit is None:
        raise InvalidArgError(context.elem, context.prop, 'substr', 'START', start)
    start = startUnit.toInt()
    if startUnit.sign != '0':
        start -= 1
    
    length = context.parse(length)
    lengthUnit = Unit.fromStr(context.parse(length), signs='+0', units=('',))
    if lengthUnit is None:
        raise InvalidArgError(context.elem, context.prop, 'substr', 'LENGTH', length)
    length = lengthUnit.toInt()
    
    return value[start:start+length]

@MacroStore.addStdlib('slice', (2, 3))
def sliceMacro(context, value, start, stop=None):
    value = context.parse(value)   

    start = context.parse(start)
    startUnit = Unit.fromStr(context.parse(start), signs='+-0', units=('',))
    if startUnit is None:
        raise InvalidArgError(context.elem, context.prop, 'slice', 'START', start)
    start = startUnit.toInt()
    if startUnit.sign in ('+', ''):
        start -= 1

    if stop is not None:
        stop = context.parse(stop)
        stopUnit = Unit.fromStr(context.parse(stop), signs='+-0', units=('',))
        if stopUnit is None:
            raise InvalidArgError(context.elem, context.prop, 'slice', 'STOP', stop)
        stop = stopUnit.toInt()
        if stopUnit.sign in ('+', ''):
            stop -= 1
        
    parsedList = ListParser(value, context.elem, context.prop).parse()
    if parsedList is not None:
        return makeList(parsedList[start:stop])
    else:
        return value[start:stop]

@MacroStore.addStdlib('length', 1)
def lengthMacro(context, value):
    parsedValue = evalEscapes(context.parse(value))
    parsedList = ListParser(context.parse(value), context.elem, context.prop).parse()
    if parsedList is not None:
        return len(parsedList)
    else:
        return len(parsedValue)

@MacroStore.addStdlib('rnd', (1,2))
def randomMacro(context, start, stop=None):
    if stop == None:
        start, stop = '+1', start
    startUnit = Unit.fromStr(start, signs='+-0', units=('',))
    if startUnit is None:
        raise InvalidArgError(context.elem, context.prop, 'rnd', 'START', start)
    start = startUnit.toInt()
    stopUnit = Unit.fromStr(stop, signs='+-0', units=('',))
    if stopUnit is None:
        raise InvalidArgError(context.elem, context.prop, 'rnd', 'STOP', stop)
    stop = stopUnit.toInt()
    try:
        num = random.randint(start, stop)
    except ValueError:
        raise InvalidArgError(context.elem, context.prop, 'rnd', 'START', start)
    return str(num)


@MacroStore.addStdlib('/', 1)
def expansionMacro(context, value):
    value = context.parse(value)
    return evalEscapes(value)

@MacroStore.addStdlib('?', 1)
def comparisonMacro(context, value):
    nValue = context.parse(value)
    try:
        left, op, right = re.split(r'(==|!=|<=?|>=?)', nValue, maxsplit=1)
    except ValueError as e:
        raise CLSError("'{value}' does not contain a valid comparison",
        prop=context.prop, elem=context.elem, value=value
        )
    leftUnit = Unit.fromStr(left.strip(), units='all')
    if leftUnit is None:
        raise InvalidArgError(context.elem, context.prop, '?', 'OPERAND', left)
    rightUnit = Unit.fromStr(right.strip(), units='all')
    if rightUnit is None:
        raise InvalidArgError(context.elem, context.prop, '?', 'OPERAND', right)
    left = leftUnit.toFloat()
    right = rightUnit.toFloat()
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
        raise CLSError("'{value}' does not contain a valid comparison",
        prop=context.prop, elem=context.elem, value=value
        )
    if final:
        return 'true'
    else:
        return 'false'

def makeOp(op):
    if op not in '+-*/%(':
        return None
    elif op == '+':
        return AttrDict(prec=1, op=operator.add, name=op)
    elif op == '-':
        return AttrDict(prec=1, op=operator.sub, name=op)
    elif op == '*':
        return AttrDict(prec=2, op=operator.mul, name=op)
    elif op == '/':
        return AttrDict(prec=2, op=operator.truediv, name=op)
    elif op == '%':
        return AttrDict(prec=2, op=operator.mod, name=op)
    elif op == '(':
        return AttrDict(prec=0, op=(lambda x, y: None), name=op)

@MacroStore.addStdlib('=', 1)
def mathMacro(context, value):
    '''makes use of dijkstra's shunting yard algorithm to conver to
    reverse polish notation, then parses the rpn'''
    #tokens = context.parse(value).split()

    tokens = re.split(r"\s+(\+|\-|\*|\%|/|\(|\))\s+", context.parse(value.strip()))

    rpn = deque()
    opStack = []
    for token in tokens:
        if token == '':
            continue
        num = Unit.fromStr(token)
        op = makeOp(token)
        length = len(opStack)
        if num is not None:
            rpn.append(num.toFloat())
        elif token == '(':
            opStack.append(op)
        elif token == ')':
            if length == 0:
                raise CLSError("'{value}' is missing an opening parenthesis in macro [{name}| ]", 
                elem=context.elem, prop=context.prop, name=context.name, value=value
                )
            while length > 0:
                if opStack[length-1].name != '(':
                    rpn.append(opStack.pop())
                else:
                    break
                length = len(opStack)
            else:
                raise CLSError("'{value}' is missing an opening parenthesis in macro [{name}| ]", 
                elem=context.elem, prop=context.prop, name=context.name, value=value
                )
            opStack.pop()
        elif op != None:
            if length > 0 and opStack[length-1].prec >= op.prec:
                rpn.append(opStack.pop())
            opStack.append(op)
        else:
            raise CLSError("'{value}' is an unknown operator in macro [{name}| ]", 
                elem=context.elem, prop=context.prop, name=context.name, value=token
                )
    while len(opStack) > 0:
        op = opStack.pop()
        if op.name == '(':
            raise CLSError("'{value}' is missing a closing parenthesis in macro [{name}| ]", 
                elem=context.elem, prop=context.prop, name=context.name, value=value
                )
        rpn.append(op)

    accum = []
    if len(rpn) < 3:
        raise CLSError("'{value}' is not a valid mathematical expression in macro [{name}| ]", 
                elem=context.elem, prop=context.prop, name=context.name, value=value
                )
    for op in rpn:
        if type(op) == float:
            accum.append(op)
        else:
            if len(accum) < 2:
                print(accum, op)
                raise CLSError("'{value}' does not have enough operands in macro [{name}| ]", 
                elem=context.elem, prop=context.prop, name=context.name, value=value
                )
            right = accum.pop()
            left = accum.pop()
            accum.append(op.op(left, right))
    if len(accum) != 1:
        raise CLSError("'{value}' has too many operands in macro [{name}| ]", 
                elem=context.elem, prop=context.prop, name=context.name, value=value
                )
    
    if int(accum[0]) == accum[0]:
        return str(int(accum[0]))
    else:
        return str(accum[0])


@MacroStore.addStdlib('file', 1)
def fileMacro(context, filename):
    name = context.parse(filename)
    if not os.path.isfile(name):
        raise InvalidArgError(context.elem, context.prop, 'file', 'FILENAME', filename)
    try:
        with open(name, encoding='utf-8') as file:
            fileContents = file.read()
    except OSError:
        raise CLSError("Could not open '{filename}'", elem=context.elem, prop=context.prop, filename=filename)
    return fileContents

@MacroStore.addStdlib('switch', (3, 99))
def switchMacro(context, sentinal, *args):
    if len(args)% 2 != 0:
        raise CLSError("case and results are not balanced in macro [switch| ]", elem=context.elem, prop=context.prop)
    
    sentinal = evalEscapes(context.parse(sentinal))
    args = list(args)

    if args[-2] == 'default':
        default = True
        defaultValue = args.pop()
        args.pop()
    else:
        default = False

    for pair in range(0, len(args), 2):
        testValue = context.parse(args[pair])
        testList = ListParser(testValue, context.elem, context.prop).parse()
        if testList is not None:
            if sentinal in testList:
                return args[pair+1]
        else:
            if sentinal == evalEscapes(testValue):
                return args[pair+1]
    if default:
        return defaultValue
    else:
        return ''


if __name__ == '__main__':
    context = AttrDict(elem='<test>', prop='<test>', name='switch', parse=(lambda x: x))
    foo = ['a', 'foo', '(b, c)', 'bc', 'default', 'else']
    print(switchMacro(context, 'd', *foo))
    #print(mathMacro(context, ''))

