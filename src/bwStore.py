import os
import re
from collections import ChainMap
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

    def add(self, name:str, value:Union[list[int], str]):
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
        
        raise UnclosedBrikError(context.elem, context.prop, ps.source)


    def evalBrik(self, ps) -> str:
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
                ps.pos += 2
                continue
                
            elif char == '|':
                ps.pos += 1
                args.append(self.parseBrikArg(ps, context))
            
            elif char == ']':
                return self.call(''.join(nameB).strip(), context, args)
            
            else:
                nameB.append(char)

            ps.pos += 1

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
    parsed = context.parse(value)
    for arg in args:
        if parsed == context.parse(arg):
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
    times = asNum(times, err=InvalidArgError(
        context.elem, context.prop, 'dup', 'TIMES', nTimes
    ))
    result = []
    newStore = context.store.copy()
    for i in range(times):
        newStore.add('d', str(i+1))#FIXME
        result.append(newStore.parse(value))
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

@BrikStore.addStdlib('substring', 3)
def subBrik(context, value, start, length):
    value = context.parse(value)
    start = asNum(context.parse(start), err=InvalidArgError(
        context.elem, context.prop, 'substring', 'START', start
    ))-1
    length = asNum(context.parse(length), err=InvalidArgError(
        context.elem, context.prop, 'substring', 'LENGTH', length
    ))
    return value[start:start+length]

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
    left = asNum(left.strip(), err=InvalidArgError(
        context.elem, context.prop, '?', 'OPERAND', left
    ))
    right = asNum(right.strip(), err=InvalidArgError(
        context.elem, context.prop, '?', 'OPERAND', right
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
        raise bWError("'{value}' does not contain a valid comparison",
        prop=context.prop, elem=context.elem, value=value
        )
    if final:
        return 'true'
    else:
        return 'false'

@BrikStore.addStdlib('#', 1)
def mathMacro(context, value):
    
    value = context.parse(value)
    ops = '+-*/%'

    makeToken = lambda x: ''.join(x).strip()
    tokens = []
    token = []
    for c in value:
        if c == ' ':
            tokens.append(makeToken(token))
            token = []
        elif c in ops:
            tokens.append(makeToken(token))
            tokens .append(c)
            token = []

        else:
            token.append(c)
    if len(token) > 0:
        tokens.append(makeToken(token))

    accum = None
    op = None
    newTokens = []

    for token in tokens:
        if token == '': continue
        currentToken = asNum(token)
        if currentToken is None:
            if token in '*/%':
                op = token
            elif token in '+-':
                if accum is None:
                    raise bWError("{op} in '{source}' is missing a left operand",
                    elem=context.elem, prop=context.prop, source=value, op=token
                    )    
                newTokens.append(accum)
                accum = None
                newTokens.append(token)
                op = None
            else:
                raise InvalidArgError(context.elem, context.prop, '#', 'OPERATION',token)
        else:
            if op is None:
                accum = currentToken
            elif accum is None:
                raise bWError("{op} in '{source}' is missing a left operand",
                elem=context.elem, prop=context.prop, source=value, op=op
                )
            elif op == '*':
                accum *= currentToken
            elif op == '/':
                accum /= currentToken
            elif op == '%':
                accum %= currentToken


    newTokens.append(accum)
    accum = None
    op = None

    for token in newTokens:
        #currentToken = asNum(token)
        #if currentToken is None:
        if type(token) not in (int, float):
            op = token
        else:
            if op is None:
                accum = token#currentToken
            elif accum is None:
                raise bWError("{op} in '{source}' is missing a left operand",
                elem=context.elem, prop=context.prop, source=value, op=op
                )
            elif op == '+':
                accum += token#currentToken
            elif op == '-':
                accum -= token#currentToken
            else:
                raise bWError("huh, not sure how you got here, anyway, {op} in '{source}' is not an operator",
                elem=context.elem, prop=context.prop, source=value, op=op
                )

    return str(int(accum))

@BrikStore.addStdlib('file', 1)
def fileBrik(context, filename):
    name = context.parse(filename)
    if not os.path.isfile(name):
        raise InvalidArgError(context.elem, context.prop, 'file', 'FILENAME', filename)
    try:
        with open(name, encoding='utf-8') as file:
            fileContents = file.read()
    except OSError:
        raise bWError("Could not open '{filename}'", elem=context.elem, prop=context.prop)
    return fileContents

    
    