import os
import re
import random
from collections import ChainMap, deque
from typing import Union, Callable, Collection
from bwUtils import *
import operator

class BrikStore():

    stdlib = {'': ''}

    @classmethod
    def addStdlib(cls, name:str, value:Union[int, str]):
        '''with two strings, add text brik
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
        self.briks = ChainMap({}, self.stdlib)

    def copy(self):
        '''make a copy of this BrikStore'''
        new = BrikStore()
        new.briks = self.briks.new_child()
        return new

    def add(self, name:str, value:Union[list[int], str]):
        '''with two strings, add text brik
        with a string and an int, use as a decorator to add a function'''
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

    def call(self, name:str, context:Collection, args:str) -> str:
        '''call a brik by name'''
        #print(f'{name!r} : {args!r}')
        if name in self.briks:
            brik = self.briks[name]
            if type(brik) == str:
                return brik
            else:
                func, signature = brik
                if type(signature) is int:
                    if len(args) != signature:
                        raise bWError('wrong number of arguments for [{brik}| ], expected {num} got {badnum}',
                        elem=context.elem, prop=context.prop, brik=name, num=signature, badnum=len(args)
                        )
                    return func(context, *args)

                else:
                    min, max = signature
                    if len(args) < min:
                        raise bWError('too few arguments for [{brik}| ], expected at least {num} got {badnum}',
                        elem=context.elem, prop=context.prop, brik=name, num=min, badnum=len(args)
                        )
                    elif len(args) > max:
                        raise bWError('too many arguments for [{brik}| ], expected at most {num} got {badnum}',
                        elem=context.elem, prop=context.prop, brik=name, num=max, badnum=len(args)
                        )
                    return func(context, *args)
        else:
            return ''
        
    def parseBrikArg(self, ps, context) -> str:
        argB = []
        brikStack = []
        char = ''

        while ps.pos < len(ps.string):
            char = ps.string[ps.pos]

            if char == '\\':
                argB.append(ps.string[ps.pos:ps.pos+2])
                ps.pos += 1

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
        
        print('parseBrikArg')
        raise UnclosedBrikError(context.elem, context.prop, ps.string)


    def evalBrik(self, ps) -> str:
        '''evalBrik parses out a brik then calls it with its arguments and context
        context includes:
         - store - this brikStore object
         - parse - a reference to the parse method of this object
         - source - the string the brik was found in, used for errors
         - prop - the property this brik was found in, used for errors
         - elem - the element this brik was found in, used for errors'''
        nameB = []
        args = []
        char = ''

        context = Collection(
            store=self,
            parse=self.parse,
            source=ps.string,
            prop = self.briks['propertyName'],
            elem = self.briks['elementName']
        )
        while ps.pos < len(ps.string):
            char = ps.string[ps.pos]
            if char == '\\':
                nameB.append(ps.string[ps.pos:ps.pos+2])
                ps.pos += 1
                
            elif char == '|':
                ps.pos += 1
                args.append(self.parseBrikArg(ps, context))
            
            elif char == ']':
                name = build(nameB)
                context.name = name
                return self.call(name, context, args)
            
            else:
                nameB.append(char)

            ps.pos += 1
        print('evalBrik')
        raise UnclosedBrikError(context.elem, context.prop, ps.string)

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
                ps.pos += 1
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

 
@BrikStore.addStdlib('if', (2,3))
def ifBrik(context, test, true, false=''):

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

@BrikStore.addStdlib('eq', 2)
def eqBrik(context, left, right):
    if context.parse(left) == context.parse(right):
        return 'true'
    else:
        return 'false'

@BrikStore.addStdlib('ne', 2)
def neBrik(context, left, right):
    if context.parse(left) != context.parse(right):
        return 'true'
    else:
        return 'false'

@BrikStore.addStdlib('in', (2, 99))
def inBrik(context, value, *args):
    parsed = evalEscapes(context.parse(value))
    if len(args) == 0:
        return 'false'
    parsedList = ListParser(args[0]).parse()
    if parsedList == None:
        parsedList = args
    for arg in parsedList:
        if parsed == evalEscapes(context.parse(arg)):
            return 'true'
    return 'false'

@BrikStore.addStdlib('i', 1)
def italicBrik(context, string):
    return f'<i>{string}</i>'

@BrikStore.addStdlib('b', 1)
def boldBrik(context, string):
    return f'<b>{string}</b>'

@BrikStore.addStdlib('s', 1)
def strikedBrik(context, string):
    return f'<s>{string}</s>'

@BrikStore.addStdlib('u', 1)
def underlineBrik(context, string):
    return f'<u>{string}</u>'


@BrikStore.addStdlib('dup', 2)
def repeatBrik(context, times, value):
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

@BrikStore.addStdlib('for-each', 2)
def forBrik(context, lst, body):
    lst = context.parse(lst)
    parsedList = ListParser(lst).parse()
    if parsedList == None:
        raise InvalidArgError(context.elem, context.prop, 'for-each', 'LIST', lst)
    result = []
    newStore = context.store.copy()
    for item in parsedList:
        newStore.add('item', item)
        result.append(newStore.parse(body))
    return ''.join(result)

@BrikStore.addStdlib('capitalize', 1)
def capitalizeBrik(context, value):
    value = context.parse(value)
    value = value[0].upper()+value[1:]
    def repl(m):
        return m.group(1).upper() + m.group(2)
    return re.sub(r'\b([a-z])(\w{3,})\b', repl, value)

@BrikStore.addStdlib('upper', 1)
def upperBrik(context, value):
    value = context.parse(value)
    def repl(m):
        return m.group(1).upper()
    return re.sub(r'(?<!\\)([a-z])', repl, value)
    
@BrikStore.addStdlib('lower', 1)
def upperBrik(context, value):
    value = context.parse(value)
    def repl(m):
        return m.group(1).lower()
    return re.sub(r'(?<!\\)([A-Z])', repl, value)

@BrikStore.addStdlib('slice', (2, 3))
def sliceBrik(context, value, start, stop=None):
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
        
    parsedList = ListParser(value).parse()
    if parsedList is not None:
        return makeList(parsedList[start:stop])
    else:
        return value[start:stop]

@BrikStore.addStdlib('length', 1)
def lengthBrik(context, value):
    parsedValue = evalEscapes(context.parse(value))
    parsedList = ListParser(context.parse(value)).parse()
    if parsedList is not None:
        return len(parsedList)
    else:
        return len(parsedValue)

@BrikStore.addStdlib('rnd', (1,2))
def randomBrik(context, start, stop=None):
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


@BrikStore.addStdlib('/', 1)
def expansionMacro(context, value):
    value = context.parse(value)
    return evalEscapes(value)

@BrikStore.addStdlib('?', 1)
def comparisonMacro(context, value):
    prop = context.store.briks['']
    nValue = context.parse(value)
    try:
        left, op, right = re.split(r'(==|!=|<=?|>=?)', nValue, maxsplit=1)
    except ValueError as e:
        raise bWError("'{value}' does not contain a valid comparison",
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
        raise bWError("'{value}' does not contain a valid comparison",
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

@BrikStore.addStdlib('=', 1)
def mathBrik(context, value):
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
                raise bWError("'{value}' is missing an opening parenthesis in brik [{name}| ]", 
                elem=context.elem, prop=context.prop, name=context.name, value=value
                )
            while length > 0:
                if opStack[length-1].name != '(':
                    rpn.append(opStack.pop())
                else:
                    break
                length = len(opStack)
            else:
                raise bWError("'{value}' is missing an opening parenthesis in brik [{name}| ]", 
                elem=context.elem, prop=context.prop, name=context.name, value=value
                )
            opStack.pop()
        elif op != None:
            if length > 0 and opStack[length-1].prec >= op.prec:
                rpn.append(opStack.pop())
            opStack.append(op)
        else:
            raise bWError("'{value}' is an unknown operator in brik [{name}| ]", 
                elem=context.elem, prop=context.prop, name=context.name, value=token
                )
    while len(opStack) > 0:
        op = opStack.pop()
        if op.name == '(':
            raise bWError("'{value}' is missing a closing parenthesis in brik [{name}| ]", 
                elem=context.elem, prop=context.prop, name=context.name, value=value
                )
        rpn.append(op)

    accum = []
    if len(rpn) < 3:
        raise bWError("'{value}' is not a valid mathematical expression in brik [{name}| ]", 
                elem=context.elem, prop=context.prop, name=context.name, value=value
                )
    for op in rpn:
        if type(op) == float:
            accum.append(op)
        else:
            if len(accum) < 2:
                print(accum, op)
                raise bWError("'{value}' does not have enough operands in brik [{name}| ]", 
                elem=context.elem, prop=context.prop, name=context.name, value=value
                )
            right = accum.pop()
            left = accum.pop()
            accum.append(op.op(left, right))
    if len(accum) != 1:
        raise bWError("'{value}' has too many operands in brik [{name}| ]", 
                elem=context.elem, prop=context.prop, name=context.name, value=value
                )
    
    if int(accum[0]) == accum[0]:
        return str(int(accum[0]))
    else:
        return str(accum[0])


@BrikStore.addStdlib('file', 1)
def fileBrik(context, filename):
    name = context.parse(filename)
    if not os.path.isfile(name):
        raise InvalidArgError(context.elem, context.prop, 'file', 'FILENAME', filename)
    try:
        with open(name, encoding='utf-8') as file:
            fileContents = file.read()
    except OSError:
        raise bWError("Could not open '{filename}'", elem=context.elem, prop=context.prop, filename=filename)
    return fileContents

@BrikStore.addStdlib('switch', (3, 99))
def switchBrik(context, sentinal, *args):
    if len(args)% 2 != 0:
        raise bWError("case and results are not balanced in brik [switch| ]", elem=context.elem, prop=context.prop)
    test = evalEscapes(context.parse(sentinal))
    for pair in range(len(args)//2):
        case = pair*2
        if case+2 == len(args):
            if args[case] == 'default':
                return args[case+1]
        if test == evalEscapes(context.parse(args[case])):
            return args[case+1]
    return ''

if __name__ == '__main__':
    context = AttrDict(elem='<test>', prop='<test>', name='=', parse=(lambda x: x))
    print(mathBrik(context, '2.1/4 - 2/3 ' ))
    #print(mathBrik(context, ''))