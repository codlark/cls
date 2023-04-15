### elements.py ###

import re
from collections import ChainMap
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from utils import *

__all__ = ["elemClasses", "ElementProtoype", "validateString", "validateNumber", "validateToggle",]

def validateString(frame, elem):
    elem[frame.prop] = evalEscapes(frame.value)
    return True

def validateNumber(signs='+', units=('px', 'in', 'mm'), out=int): 
    def func(frame, elem):
        num = Unit.fromStr(frame.value, signs, units)
        if num is None:
            return False
        else:
            if out == int:
                value = num.toInt(dpi=frame.layout.dpi)
            elif out == float:
                value = num.toFloat(dpi=frame.layout.dpi)
            else:
                value = num
            elem[frame.prop] = value
            return True
    return func

def validateToggle(frame, elem):
    value = asBool(frame.value)
    if value is None:
        return False
    elem[frame.prop] = value
    return True

def validateList(frame, elem):
    value = ListParser(frame.value, elem.name, frame.prop).parse()
    if value is None:
        return False
    elem[frame.prop] = value
    return True

def validateChoices(choices):
    def validator(frame, elem):
        if frame.value.lower() not in choices:
            return False
        elem[frame.prop] = choices[frame.value.lower()]
        return True
    return validator

def validateXY(frame, elem):
    #also handles x2 and y2
    if frame.prop[0] == 'x':
        dim = 'width'
    else:
        dim = 'height'
    if frame.container == 'layout':
        containerDim = getattr(frame.layout.cardSize, dim)()
        #containerDim = frame.layout[dim]
    else:
        containerDim = frame.container[dim]

    if frame.value == 'center':
        #x2 and y2 shouldn't center, 
        elem[frame.prop] = (containerDim-elem[dim])//2
        return True
    else:
        value = Unit.fromStr(frame.value, signs='-+^',units=('px', 'in', 'mm', '%'))
        if value is None:
            return False
        if value.unit == '%':
            value = value.toInt(whole=containerDim)
        elif value.sign == '^':
            #TODO consider making ^ a signal not a sign to allow ^-.3
            value = containerDim - elem[dim] - value.toInt(dpi=frame.layout.dpi)
        else:
            value = value.toInt(dpi=frame.layout.dpi)
        elem[frame.prop] = value
        return True

def validateHeightWidth(frame, elem):
    if frame.container == 'layout':
        containerDim = getattr(frame.layout.fullSize, frame.prop)()
        #containerDim = frame.layout[frame.prop]
    else:
        containerDim = frame.container[frame.prop]
    value = Unit.fromStr(frame.value, units=('px', 'in', 'mm', '%'))
    if value is None:
        return False
    if value.unit == '%':
        value = value.toInt(whole=containerDim)
    else:
        value = value.toInt(dpi=frame.layout.dpi)
    elem[frame.prop] = value
    return True

def validateAngle(frame, elem):
    value = Unit.fromStr(frame.value, signs='+', units=('deg'))
    if value is None:
        return False
    elem[frame.prop] = value.toInt() % 360
    return True

def validateDraw(frame, elem):
    value = asBool(frame.value)
    if value is None:
        return False
    elif frame.container == 'layout':
        elem[frame.prop] = value
    elif frame.containerValue == True:
        elem.draw = value
    else:
        elem.draw = frame.containerValue
    return True

alignments = {'left':Qt.AlignLeft, 'right':Qt.AlignRight, 'center':Qt.AlignHCenter,
        'justify':Qt.AlignJustify,
        'top':Qt.AlignTop, 'bottom':Qt.AlignBottom, 'middle':Qt.AlignVCenter}
validateAlignment = validateChoices(alignments)

def countShortcut(min, *props):
    def func(value):
        values = commaSplit(value)
        if len(values) < min:
            return None
        return {p: v for p, v in zip(props, values)}
    return func

def stretchShortcut(*props):
    def func(value):
        values = commaSplit(value)
        if len(values) ==  1:
            return {p: value for p in props}
        elif len(values) >= len(props):
            return {p: v for p, v in zip(props, values)}
        else:
            return None
    return func


class ElementProtoype(ChainMap):
    '''This class acts as the prototype of an element, prototype:element::layout:card  '''
    def __init__(self, container, name, props:dict, renames:dict, type_:"Element") -> None:
        super().__init__(props, *type_.defaults.maps)

        self.container = container
        self.subelements = {}
        self.name = name
        self.type = type_
        self.renames = renames
        if container is not None:
            self.qualName = f'{container}->{name}'
        else:
            self.qualName = name
    
    def validate(self, frame:AttrDict):
        trueProp = frame.prop
        if trueProp in self.renames:
            userProp = self.renames[trueProp]
        else:
            userProp = trueProp
        #trueProp is the coannonical name of a property
        #userProp is the name the user used

        if trueProp not in self.type.validators:
            return
            #we ignore any property we don't knoe, is this too forgiving?
        func = self.type.validators[trueProp]
        result = func(frame, frame.elem)
        if not result:
            raise InvalidValueError(frame.elem.name, userProp, frame.value)
        else:
            return

    def compile(self, container, store, layout):
        '''turn a element protopye into a rendered element, ready for rendering
        stored as a dictionary'''
        frame = AttrDict(name=self.qualName)
        frame.layout = layout.copy()
        if container is None:
            frame.container = 'layout'
            frame.containerValue = None
        else:
            frame.container = container.copy()
         
        elem = AttrDict(name=self.qualName, type=self.type)
        frame.elem = elem
        
        store.add('elementName', self.qualName)
        
        xyProps = ['x', 'y']

        for prop, value in self.items():
            if prop in xyProps:
                continue
            if frame.container != 'layout' and prop in frame.container:
                frame.containerValue = frame.container[prop]
            else:
                frame.containerValue = None
            store.add('propertyName', prop)
            frame.prop = prop
            frame.value = store.parse(value)
            #the validate function puts the new value on element
            self.validate(frame)

        
        if hasattr(self.type, 'midCompile'):
            self.type.midCompile(elem)

        for prop in xyProps:
            #x and y need to be validated after width and height
            if prop not in self:
                continue
            value = self[prop]
            if frame.container != 'layout' and prop in frame.container:
                frame.containerValue = frame.container[prop]
            store.add('propertyName', prop)
            frame.prop = prop
            frame.value = store.parse(value)
            self.validate(frame)
        
        if hasattr(self.type, 'postCompile'):
            self.type.postCompile(elem)

        return elem


class Element():
    defaults = ChainMap(dict(
        draw =  'true',
        x =  '0px',
        y =  '0px',
        width =  '1/4in',
        height =  '1/4in',
        rotation =  '0',
    ))

    validators = ChainMap(dict(
        draw = validateDraw,
        x = validateXY,
        y = validateXY,
        width = validateHeightWidth,
        height = validateHeightWidth,
        rotation = validateAngle,
    ))
    #validate functions are missnamed, they actually set the associated property
    #on the reified element, then return true or false depending on success

    shortcuts = ChainMap(dict(
        position = stretchShortcut('position X', 'position Y'),
        size = stretchShortcut('size WIDTH', 'size HEIGHT'),
    ))
    #shortcut functions take a compound value and split that value, pairing each
    #sub value with it's name

    names = ChainMap({
        'angle': 'rotation',
        'position X': 'x',
        'position Y': 'y',
        'size WIDTH': 'width',
        'size HEIGHT': 'height',
    })

    @staticmethod
    def paint(elem, painter, upperLeft, size):
        pass

def countPrintingChars(text):
    text = re.sub(r'<img[^>]*>', '@', text)
    text = re.sub(r'<br ?/?>', '\n', text)
    text = re.sub(r'<[^>]*>', '', text)
    return len(text)

validFontSizes = ('pt', 'px', 'in', 'mm')

def validateShrinkFont(frame, elem):
    if frame.value[0] != '(' and frame.value[-1] != ')':
        frame.value = '(' + frame.value + ')'
    list = ListParser(frame.value, elem.name, frame.prop).parse()
    if list is None: return False
    if len(list) == 0:
        elem.shrinkFont = ()
        return True
    result = []
    for item in list:
        if ':' not in item:
            frame.value = item
            return False
        num, size = item.split(':', 1)
        parsedNum = Unit.fromStr(num.strip(), units=('c'))
        if parsedNum is None:
            frame.value = num
            return False
        parsedSize = Unit.fromStr(size.strip(), units=validFontSizes)
        if parsedSize is None:
            frame.value = size
            return False
        result.append((parsedNum.toInt(), parsedSize.toInt(dpi=frame.layout.dpi)))
    elem.shrinkFont = result
    return True

def shortcutDecoration(value):
    values = commaSplit(value)
    decos = ['italic', 'bold', 'underline', 'overline', 'word-wrap', 'line-thru', 'line-though']
    res = {}
    for value in values:
        if value in decos:
            res[value] = 'on'
        elif value[0:3] == 'no-' and value[3:] in decos:
            res[value[3:]] = 'off'
        else:
            return None
    return res

class LabelElement():
    defaults = Element.defaults.new_child(dict(
        text = '',
        fontFamily = 'Verdana',
        fontSize = '22pt',
        fontColor = 'black',
        shrinkFont = '()',
        wordWrap = 'yes',
        hAlign = 'center',
        vAlign = 'top',
        italic = 'no',
        bold = 'no',
        overline = 'no',
        underline = 'no',
        lineThrough = 'no',
    ))

    validators = Element.validators.new_child(dict(
        text = validateString,
        fontFamily = validateString,
        fontSize = validateNumber(units=validFontSizes),
        fontColor = validateString,
        shrinkFont = validateShrinkFont,
        wordWrap = validateToggle,
        vAlign = validateAlignment,
        hAlign = validateAlignment,
        italic = validateToggle,
        bold = validateToggle,
        overline = validateToggle,
        underline = validateToggle,
        lineThrough = validateToggle,
    ))

    shortcuts = Element.shortcuts.new_child(dict(
        align = countShortcut(2, 'align H-ALIGN', 'align V-ALIGN'),
        font = countShortcut(2, 'font FONT-SIZE', 'font FONT-FAMILY', 'font FONT-COLOR'),
        decoration = shortcutDecoration,
    ))

    names = Element.names.new_child({
        'font-family': 'fontFamily',
        'font FONT-FAMILY': 'fontFamily',
        'font-color': 'fontColor',
        'font FONT-COLOR': 'fontColor',
        'font-size': 'fontSize',
        'font FONT-SIZE': 'fontSize',
        'shrink-font': 'shrinkFont',
        'word-wrap': 'wordWrap',
        'v-align': 'vAlign',
        'align V-ALIGN': 'vAlign',
        'h-align': 'hAlign',
        'align H-ALIGN': 'hAlign',
        'line-through': 'lineThrough',
        'line-thru': 'lineThrough',
    })

    @staticmethod
    def paint(elem, painter:QPainter, upperLeft:QPoint, size:QSize):


        label = QLabel()        
        label.setTextFormat(Qt.RichText)
        label.setAttribute(Qt.WA_TranslucentBackground, True)
        label.setAlignment(elem.vAlign|elem.hAlign)
        label.setWordWrap(elem.wordWrap)
        label.resize(size)
        
        if len(elem.shrinkFont) > 0:
            textLen = countPrintingChars(elem.text)
            for num, newSize in elem.shrinkFont:
                if textLen >= num:
                    elem.fontSize = newSize
                else:
                    break

        style = ['QLabel {']
        style.append(f'font-size: {elem.fontSize}px;\n')
        style.append(f'font-family: {elem.fontFamily};\n')
        style.append(f'color: {elem.fontColor};\n')
        if elem.italic: style.append('font-style: italic;\n')
        if elem.bold: style.append('font-weight: bold;\n')
        if elem.overline: style.append('text-decoration: overline;\n')
        if elem.underline: style.append('text-decoration: underline;\n')
        if elem.lineThrough: style.append('text-decoration: line-through;\n')
        #style += "font-variant-numeric: lining-nums;\n" someday *dreamy sigh*
        style.append('}')
        label.setStyleSheet(build(style))
        
        
        label.setText(re.sub(r'\n', '<br>', elem.text))
        painter.drawPixmap(upperLeft, label.grab())



def validateImage(frame, elem):

    elem[frame.prop] = ImageGetter.getImage(frame.value)
    return True

class ImageElement():
    defaults = Element.defaults.new_child(dict(
        width = '0px',
        height = '0px',
        source = '',
        keepAspectRatio = 'yes',
        scaleWidth = '0',
        scaleHeight = '0'
    ))

    validators = Element.validators.new_child(dict(
        source = validateImage,
        keepAspectRatio = validateToggle,
        scaleWidth = validateNumber(units=('%', 'x'), out=Unit),
        scaleHeight = validateNumber(units=('%', 'x'), out=Unit),
        
    ))

    shortcuts = Element.shortcuts.new_child(dict(
        scale = stretchShortcut('scale SCALE-WIDTH', 'scale SCALE-HEIGHT')
    ))

    names = Element.names.new_child({
        'keep-ratio': 'keepAspectRatio',
        'scale-width': 'scaleWidth',
        'scale-height': 'scaleHeight',
        'scale SCALE-WIDTH': 'scaleWidth',
        'scale SCALE-HEIGHT': 'scaleHeight'
    })

    @staticmethod
    def paint(elem, painter:QPainter, upperLeft:QPoint, size:QSize):
        painter.drawPixmap(upperLeft, elem.source)

    @staticmethod
    def midCompile(elem):
        scaleMode = Qt.SmoothTransformation
        if elem.keepAspectRatio:
            aspect = Qt.KeepAspectRatio
        else:
            aspect = Qt.IgnoreAspectRatio

        if elem.width == 0 and elem.height == 0:

            if elem.scaleWidth.num != 0:
                if elem.scaleHeight.num == 0:
                    elem.scaleHeight = elem.scaleWidth
        
                width = elem.source.width()
                height = elem.source.height()
                if elem.scaleWidth.unit == '%':
                    newWidth = int(elem.scaleWidth.num/100 * width)
                else:
                    newWidth = int(elem.scaleWidth.num*width)
                if elem.scaleHeight.unit == '%':
                    newHeight = int(elem.scaleHeight.num/100 * height)
                else:
                    newHeight = int(elem.scaleHeight.num*height)
                elem.source = elem.source.scaled(newWidth, newHeight, aspect, scaleMode)
            
        elif elem.keepAspectRatio:
            if elem.width == 0:
                elem.source = elem.source.scaledToHeight(elem.height, scaleMode)
            elif elem.height == 0:
                elem.source = elem.source.scaledToWidth(elem.width, scaleMode)
            else:
                elem.source = elem.source.scaled(elem.width, elem.height, aspect, scaleMode)
        else:
            elem.source = elem.source.scaled(elem.width, elem.height, aspect, scaleMode)
        
        elem.width = elem.source.width()
        elem.height = elem.source.height()
        elem.source = QPixmap.fromImage(elem.source)

class ImageBoxElement():
    defaults = ImageElement.defaults.new_child(dict(
        hAlign = 'center',
        vAlign = 'top',
    ))

    validators = ImageElement.validators.new_child(dict(
        vAlign = validateAlignment,
        hAlign = validateAlignment,
    ))

    shortcuts = ImageElement.shortcuts.new_child(dict(
        align = countShortcut(2, 'align H-ALIGN', 'align V-ALIGN')
    ))

    names = ImageElement.names.new_child({
        'v-align': 'vAlign',
        'align V-ALIGN': 'vAlign',
        'h-align': 'hAlign',
        'align H-ALIGN': 'hAlign',
    })
    
    @staticmethod
    def paint(elem, painter:QPainter, upperLeft:QPoint, size:QSize):

        widthDif = abs(elem.source.width()-elem.width)
        heightDif = abs(elem.source.height()-elem.height)
        
        if elem.hAlign & Qt.AlignLeft:
            xOfs = 0
        elif elem.hAlign & Qt.AlignRight:
            xOfs = widthDif
        else: #center or justify
            xOfs = widthDif/2
        
        if elem.vAlign & Qt.AlignTop:
            yOfs = 0
        elif elem.vAlign & Qt.AlignBottom:
            yOfs = heightDif
        else:
            yOfs = heightDif/2

        painter.drawPixmap(upperLeft+QPoint(xOfs, yOfs), elem.source)
    
    @staticmethod
    def midCompile(elem):
        scaleMode = Qt.SmoothTransformation
        if elem.keepAspectRatio:
            aspect = Qt.KeepAspectRatio
        else:
            aspect = Qt.IgnoreAspectRatio

        if elem.scaleWidth.num != 0:
            if elem.scaleHeight.num == 0:
                elem.scaleHeight = elem.scaleWidth
            width = elem.source.width()
            height = elem.source.height()

            if elem.scaleWidth.unit == '%':
                newWidth = int(elem.scaleWidth.num/100 * width)
            else:
                newWidth = int(elem.scaleWidth.num*width)
            if elem.scaleHeight.unit == '%':
                newHeight = int(elem.scaleHeight.num/100 * height)
            else:
                newHeight = int(elem.scaleHeight.num*height)

            elem.source = elem.source.scaled(newWidth, newHeight, aspect, scaleMode)

        if elem.source.width() > elem.width or elem.source.height() > elem.height:
            elem.source = elem.source.scaled(elem.width, elem.height, aspect, scaleMode)

        elem.source = QPixmap.fromImage(elem.source)


validateLineJoin = validateChoices({'miter': Qt.MiterJoin, 'bevel': Qt.BevelJoin, 'round': Qt.RoundJoin})
validateLineCap = validateChoices({'flat': Qt.FlatCap, 'square': Qt.SquareCap, 'round': Qt.RoundCap})
validateLineStyle = validateChoices({'solid': Qt.SolidLine, 'dash': Qt.DashLine, 'dots': Qt.DotLine,
    'dash-dot': Qt.DashDotLine, 'dot-dash': Qt.DashDotLine})

class ShapeElement():
    defaults = Element.defaults.new_child(dict(
        lineColor = 'black',
        lineWidth = '0.01in',
        lineStyle = 'solid',
        lineJoin = 'miter',
        lineCap = 'flat',
        fillColor = 'white',
    ))

    validators = Element.validators.new_child(dict(
        lineColor = validateString,
        lineStyle = validateLineStyle,
        lineWidth = validateNumber(),
        lineJoin = validateLineJoin,
        lineCap = validateLineCap,
        fillColor = validateString,
    ))

    shortcuts = Element.shortcuts.new_child(dict(
        line = countShortcut(2, 'line LINE-WIDTH', 'line LINE-COLOR', 'line LINE-STYLE', 'line LINE-CAP', 'line LINE-JOIN')
    ))

    names = Element.names.new_child({
        'line-color': 'lineColor',
        'line-width': 'lineWidth',
        'line-style': 'lineStyle',
        'line-join': 'lineJoin',
        'line-cap': 'lineCap',
        'fill-color': 'fillColor',
        'line LINE-STYLE': 'lineStyle',
        'line LINE-WIDTH': 'lineWidth',
        'line LINE-COLOR': 'lineColor',
        'line LINE-JOIN': 'lineJoin',
        'line LINE-CAP': 'lineCap',
    })

    @staticmethod
    def readyPainter(elem, painter:QPainter):
        pen = QPen(QColor(elem.lineColor))
        if elem.lineWidth == 0:
            pen.setStyle(Qt.NoPen)
        else:
            pen.setWidth(elem.lineWidth)
        pen.setCapStyle(elem.lineCap)
        pen.setJoinStyle(elem.lineJoin)
        pen.setStyle(elem.lineStyle)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(elem.fillColor)))

class RectangleElement():
    defaults = ShapeElement.defaults.new_child(dict(
        xRadius = '0px',
        yRadius = '0px',
        #rename these
        #corner radius: one value for both OR two values for x and y
    ))

    validators = ShapeElement.validators.new_child(dict(
        xRadius = validateNumber(),
        yRadius = validateNumber(),
    ))

    shortcuts = ShapeElement.shortcuts.new_child({
        'corner-radius': stretchShortcut('corner-radius X-CORNER-RADIUS', 'corner-radius Y-CORNER-RADIUS')
    })

    names = ShapeElement.names.new_child({
        'x-corner-radius': 'xRadius',
        'y-corner-radius': 'yRadius',
        'corner-radius X-CORNER-RADIUS': 'xRadius',
        'corner-radius Y-CORNER-RADIUS': 'yRadius',
    })

    @staticmethod
    def paint(elem, painter:QPainter, upperLeft:QPoint, size:QSize):
        ShapeElement.readyPainter(elem, painter)
        painter.drawRoundedRect(QRect(upperLeft, size), elem.xRadius, elem.yRadius)

class EllipseElement():
    defaults = ShapeElement.defaults.new_child()
    validators = ShapeElement.validators.new_child()
    shortcuts = ShapeElement.shortcuts.new_child(dict(
        diameter = stretchShortcut('diameter WIDTH', 'diameter HEIGHT')
        #diameter = validateManyStretch(width=validateHeightWidth, height=validateHeightWidth)
    ))

    names = ShapeElement.names.new_child({
        'diameter WIDTH': 'width',
        'diameter HEIGHT': 'height'
    })
    #radius - r*2 for width and height
    #diameter

    @staticmethod
    def paint(elem, painter:QPainter, upperLeft, size):
        ShapeElement.readyPainter(elem, painter)
        painter.drawEllipse(QRect(upperLeft, size))

    @staticmethod
    def midCompile(elem):
        if elem.width == 0 and elem.height != 0:
            elem.width = elem.height
        elif elem.width != 0 and elem.height == 0:
            elem.height = elem.width

class LineElement():
    #AAAAAAAAAAAAAHHHHHHHHHHHHHHHHHHHHHHHH
    defaults = ShapeElement.defaults.new_child(dict(
        x2 = '1/4in',
        y2 = '1/4in',
        width = '0',
        height = '0'
    ))

    validators = ShapeElement.validators.new_child(dict(
        x2 = validateXY,
        y2 = validateXY,
        #end = validateMany(2, x2=validateXY, y2=validateXY)
    ))

    shortcuts = ShapeElement.shortcuts.new_child(dict(
        start = stretchShortcut('start X', 'start Y'),
        end = stretchShortcut('end X', 'end Y')
    ))

    names = ShapeElement.names.new_child({
        'start X': 'x',
        'start Y': 'y',
        'end X': 'x2',
        'end Y': 'y2'

    })

    @staticmethod
    def paint(elem, painter:QPainter, upperLeft, size):
        ShapeElement.readyPainter(elem, painter)
        painter.drawLine(0, 0, elem.x2-elem.x, elem.y2-elem.y)

    @staticmethod
    def midCompile(elem):
        elem.width = 0
        elem.height = 0
        elem.rotation = 0

elemClasses = {
    'none': Element,
    'text': LabelElement,
    'image': ImageElement,
    'image-box': ImageBoxElement,
    'rect': RectangleElement,
    'ellipse': EllipseElement,
    'circle': EllipseElement,
    'line': LineElement
}