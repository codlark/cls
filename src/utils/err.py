### err.py ###

class CLSError(Exception):
    '''base class for errors raised by CLS'''
    def __init__(self, msg:str, /, **kwargs):
        '''msg will be formated with kwargs'''
        if 'origin' in kwargs:
            self.msg = "error in {origin}:\n\t"+msg
        elif 'layout' in kwargs:
            self.msg = "error in layout '{layout}':\n\t"+msg
        elif 'file' in kwargs:
            self.msg = "error in file '{file}':\n\t"+msg
        elif 'prop' in kwargs:
            self.msg = "error in property '{prop}' of element '{elem}:'\n\t"+msg
        elif 'elem' in kwargs:
            self.msg = "error in element '{elem}':\n\t"+msg
        else:
            self.msg = "error from unknown source:\n\t"+msg
        self.kwargs = kwargs

    @property
    def message(self):
        return self.msg.format(**self.kwargs)

class InvalidValueError(CLSError):
    def __init__(self, elem, prop, value):
        super().__init__("'{value}' is not a valid value for '{prop}' property",
        elem=elem, prop=prop, value=value
        )

class InvalidArgError(CLSError):
    def __init__(self, elem, prop, macro, arg, value):
        super().__init__("'{value}' is not a valid {arg} argument for macro [{macro}| ]",
        elem=elem, prop=prop, macro=macro, arg=arg, value=value
        )

class UnclosedMacroError(CLSError):
    def __init__(self, elem, prop, source):
        super().__init__("'{source}' has an unclosed macro in '{prop}' property",
        elem=elem, prop=prop, source=source
        )

class ImbalancedDelimError(CLSError):
    def __init__(self, elem, prop, source):
        super().__init__("'{source}' has unbalanced delimiters in '{prop}' property",
        elem=elem, prop=prop, source=source
        )

class CLSSyntaxError(CLSError):
    def __init__(self, msg, /, **kwargs):
        if 'origin' in kwargs:
            self.msg = "syntax error in {origin}:\n\t"+msg
        elif 'elem' in kwargs:
            self.msg = "syntax error in element '{elem}' from file '{file}':\n\t"+msg
        elif 'file' in kwargs:
            self.msg = "syntax error in file '{file}':\n\t"+msg
        else:
            self.msg = "syntax error from unknown source:\n\t"+msg
        self.kwargs = kwargs

class NoValueError(CLSSyntaxError):
    def __init__(self, file, elem, name):
        super().__init__("'{name}' has no value or section",
        file=file, elem=elem, name=name)

class UnexpectedEOFError(CLSSyntaxError):
    def __init__(self, file, name):
        super.__init__("unexpected EOF in '{name}'",
        file=file, name=name)