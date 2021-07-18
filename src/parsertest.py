
import re
from typing import Optional

def parseProps(source:str, filename, elem):

    lines=source.splitlines()
    section = {}

    for line in lines:
        if ':' not in line:
            raise SyntaxError(f"line '{line}' is not a valid property")
        name, value = line.split(':', maxsplit=1)
        section[name.strip()] = value.strip()
    
    return section

def parseUserBriks(source:str, filename):

    lines = source.splitlines()
    briks = {}

    for line in lines:
        if '=' not in line:
            raise SyntaxError(f"line '{line}' is not a valid brik definition")
        name, value = line.split('=', maxsplit=1)
        #down the line this is where parametized user briks would be defined as well
        briks[name.strip()] = value.strip()

    return briks


def parseLayout(source:str, filename:str):
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
        raise SyntaxError(f"section '{name}' is not closed")
    elif len(storage) == 0:
        raise SyntaxError(f"Could not find a layout in {filename}")

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


test = '''
layout {
    width: 2.5in 
    height: 3.5in
    name: [role][repeatIndex].png
    output: out/
}
briks {
    bloodRed = #a32b1d
    #maybe a little dark, but readability is important
}
titleBorder {
    type: rect
    x: center
    y: .5in
    width: 1.5in
    height: .25in
    lineWidth: 6
    xRadius: .125in
    yRadius: .125in
}
title {
    type: label
    x: center
    y: .5in
    width: 1.5in
    height: .25in
    text: [capitalize| [role] ]
    color: [if| [eq| [role] | werewolf ] | [bloodRed] | black ]
    alignment: center middle
    fontSize: 36
    fontFamily: Palatino Linotype
}
icon {
    type: image
    x: center
    y: 1in
    source: images/[role].png
}
data {
repeat, role
2, werewolf
4, villager
1, seer
}
'''

layout = parseLayout(test, '')

for name, section in layout.items():
    print(name)
    print(section)