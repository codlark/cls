import re
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from bwUtils import *

__all__ = ["elemClasses", "ElementProtoype", "validateString", "validateNumber", "validateToggle"]

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

def validateXY(frame, elem):
    #also handles x2 and y2
    if frame.prop[0] == 'x':
        dim = 'width'
    else:
        dim = 'height'
    if frame.container == 'layout':
        containerDim = frame.layout[dim]
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
        containerDim = frame.layout[frame.prop]
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

def validateFontSize(frame, elem):
    value = Unit.fromStr(frame.value, signs='+', units=('pt', 'px', 'in', 'mm'))
    if value is None:
        return False
    elem[frame.prop] = value, frame.layout.dpi
    return True

def validateAlignment(frame, elem):
    horz = {'left':Qt.AlignLeft, 'right':Qt.AlignRight, 'center':Qt.AlignHCenter,
        'justify':Qt.AlignJustify}
    vert = {'top':Qt.AlignTop, 'bottom':Qt.AlignBottom, 'middle':Qt.AlignVCenter,}
    terms = frame.value.lower().split()
    if terms[0] in horz:
        result = horz[terms[0]]
    else:
        return False
    if terms[1] in vert:
         result |= vert[terms[1]]
    else:
        return False
    elem[frame.prop] = result
    return True

def validateLineJoin(frame, elem):
    joins = {'miter': Qt.MiterJoin, 'bevel': Qt.BevelJoin, 'round': Qt.RoundJoin}
    if frame.value.lower() not in joins:
        return False
    elem[frame.prop] = joins[frame.value.lower()]
    return True

def validateLineCap(frame, elem):
    caps = {'flat': Qt.FlatCap, 'square': Qt.SquareCap, 'round': Qt.RoundCap}
    if frame.value.lower() not in caps:
        return False
    elem[frame.prop] = caps[frame.value.lower()]
    return True

class ElementProtoype(ChainMap):
    '''This class acts as the prototype of an element, prototype:element::layout:asset  '''
    def __init__(self, container, name, props:dict, defaults:dict, type_:"Element") -> None:
        super().__init__(props, defaults, *type_.defaults.maps)

        self.container = container
        self.subelements = {}
        self.name = name
        self.type = type_
        if container is not None:
            self.qualName = f'{container}->{name}'
        else:
            self.qualName = name
    
    def validate(self, frame:AttrDict):
        if frame.prop not in self.type.validators:
            return
            #raise bWError("'{name}' is not a known property", name=frame.prop, elem=frame.name)
        func = self.type.validators[frame.prop]
        result = func(frame, frame.elem)
        if not result:
            raise InvalidValueError(frame.elem.name, frame.prop, frame.value)
        else:
            return

    def generate(self, container, store, layout):

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
        
        for prop, value in self.items():
            if prop in ['x', 'y']:
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

        
        if hasattr(self.type, 'midGenerate'):
            self.type.midGenerate(elem)

        for prop in ['x', 'y']:
            #x and y need to be validated after width and height
            value = self[prop]
            if frame.container != 'layout' and prop in frame.container:
                frame.containerValue = frame.container[prop]
            store.add('propertyName', prop)
            frame.prop = prop
            frame.value = store.parse(value)
            self.validate(frame)
        
        if hasattr(self.type, 'postGenerate'):
            self.type.postGenerate(elem)

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
        rotation = validateAngle
    ))

    @staticmethod
    def paint(elem, painter, upperLect, size):
        pass

class LabelElement():
    defaults = Element.defaults.new_child(dict(
        text = '',
        fontFamily = 'Verdana',
        fontSize = '22pt',
        color = 'black',
        wordWrap = 'yes',
        alignment = 'center top',
        italic = 'no',
        bold = 'no',
        overline = 'no',
        underline = 'no',
        lineThrough = 'no',
    ))

    validators = Element.validators.new_child(dict(
        text = validateString,
        fontFamily = validateString,
        fontSize = validateFontSize,
        color = validateString,
        wordWrap = validateToggle,
        alignment = validateAlignment,
        italic = validateToggle,
        bold = validateToggle,
        overline = validateToggle,
        underline = validateToggle,
        lineThrough = validateToggle,

    ))

    @staticmethod
    def paint(elem, painter:QPainter, upperLeft:QPoint, size:QSize):
        label = QLabel()
        label.setTextFormat(Qt.RichText)
        label.resize(size)
        label.setAttribute(Qt.WA_TranslucentBackground, True)
        label.setAlignment(elem.alignment)
        label.setWordWrap(elem.wordWrap)
        style = 'QLabel {\n'
        style += f'font-family: {elem.fontFamily};\n'
        fontSize, dpi = elem.fontSize
        if fontSize.unit == 'pt':
            fontUnit = fontSize.unit
            fontSize = fontSize.num
        else:
            fontUnit = fontSize.unit
            fontSize = fontSize.toInt(dpi=dpi)
        style += f'font-size: {fontSize}{fontUnit};\n'
        style += f'color: {elem.color};\n'
        if elem.italic: style += 'font-style: italic;\n'
        if elem.bold: style += 'font-weight: bold;\n'
        if elem.overline: style += 'text-decoration: overline;\n'
        if elem.underline: style += 'text-decoration: underline;\n'
        if elem.lineThrough: style += 'text-decoration: line-through;\n'
        #style += "font-variant-numeric: lining-nums;\n" someday
        label.setStyleSheet(style+'}')
        label.setText(re.sub(r'\n', '<br>', elem.text))
        painter.drawPixmap(upperLeft, label.grab())

        # - should I allow pt and px? (extra validation)

imageCache = {}
def validateImage(frame, elem):
    if frame.value not in imageCache:
        imageCache[frame.value] = QImage(frame.value)
    elem[frame.prop] = imageCache[frame.value]
    return True

class ImageElement():
    defaults = Element.defaults.new_child(dict(
        width = '0px',
        height = '0px',
        source = '',
        keepAspectRatio = 'yes',
    ))

    validators = Element.validators.new_child(dict(
        source = validateImage,
        keepAspectRatio = validateToggle,
    ))

    @staticmethod
    def paint(elem, painter:QPainter, upperLeft:QPoint, size:QSize):
        painter.drawPixmap(upperLeft, elem.source)

    @staticmethod
    def midGenerate(elem):
        scaleMode = Qt.SmoothTransformation
        if elem.keepAspectRatio:
            aspect = Qt.KeepAspectRatio
        else:
            aspect = Qt.IgnoreAspectRatio

        if elem.width == 0 and elem.height == 0:
            elem.width = elem.source.width()
            elem.height = elem.source.height()
        elif elem.keepAspectRatio:
            if elem.width == 0:
                elem.source = elem.source.scaledToHeight(elem.height, scaleMode)
                elem.width = elem.source.width()
            elif elem.height == 0:
                elem.source = elem.source.scaledToWidth(elem.width, scaleMode)
                elem.height = elem.source.height()
            else:
                elem.source = elem.source.scaled(elem.width, elem.height, aspect, scaleMode)
                elem.width = elem.source.width()
                elem.height = elem.source.height()
        else:
            elem.source = elem.source.scaled(elem.width, elem.height, aspect, scaleMode)
        
        elem.source = QPixmap.fromImage(elem.source)
    

class ImageBoxElement():
    defaults = ImageElement.defaults.new_child(dict(
        alignment = 'center middle'
    ))

    validators = ImageElement.validators.new_child(dict(
        alignment = validateAlignment
    ))
    
    @staticmethod
    def paint(elem, painter:QPainter, upperLeft:QPoint, size:QSize):
        painter.drawPixmap(upperLeft, elem.source)
    
    @staticmethod
    def midGenerate(elem):
        scaleMode = Qt.SmoothTransformation
        if elem.keepAspectRatio:
            aspect = Qt.KeepAspectRatio
        else:
            aspect = Qt.IgnoreAspectRatio

        if elem.source.width() > elem.width or elem.source.height() > elem.height:
            elem.source = elem.source.scaled(elem.width, elem.height, aspect, scaleMode)

        elem.source = QPixmap.fromImage(elem.source)

    @staticmethod
    def postGenerate(elem):
        widthDif = abs(elem.source.width()-elem.width)
        heightDif = abs(elem.source.height()-elem.height)

        if elem.alignment & Qt.AlignLeft:
            pass
        elif elem.alignment & Qt.AlignRight:
            elem.x += widthDif
        else: #center or justify
            elem.x += widthDif/2
        
        if elem.alignment & Qt.AlignTop:
            pass
        elif elem.alignment & Qt.AlignBottom:
            elem.y += heightDif
        else:
            elem.y += heightDif/2



class ShapeElement():
    defaults = Element.defaults.new_child(dict(
        lineColor = 'black',
        lineWidth = '0.01in',
        lineJoin = 'miter',
        lineCap = 'flat',
        fillColor = 'white',
    ))

    validators = Element.validators.new_child(dict(
        lineColor = validateString,
        lineWidth = validateNumber(),
        lineJoin = validateLineJoin,
        lineCap = validateLineCap,
        fillColor = validateString,
    ))

    @staticmethod
    def readyPainter(elem, painter:QPainter):
        pen = QPen(QColor(elem.lineColor))
        if elem.lineWidth == 0:
            pen.setStyle(Qt.NoPen)
        else:
            pen.setWidth(elem.lineWidth)
        pen.setCapStyle(elem.lineCap)
        pen.setJoinStyle(elem.lineJoin)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(elem.fillColor)))

class RectangleElement():
    defaults = ShapeElement.defaults.new_child(dict(
        xRadius = '0px',
        yRadius = '0px',
    ))

    validators = ShapeElement.validators.new_child(dict(
        xRadius = validateNumber(),
        yRadius = validateNumber(),
    ))

    @staticmethod
    def paint(elem, painter:QPainter, upperLeft:QPoint, size:QSize):
        ShapeElement.readyPainter(elem, painter)
        painter.drawRoundedRect(QRect(upperLeft, size), elem.xRadius, elem.yRadius)

class EllipseElement():
    defaults = ShapeElement.defaults.new_child()
    validators = ShapeElement.validators.new_child()

    @staticmethod
    def paint(elem, painter:QPainter, upperLeft, size):
        ShapeElement.readyPainter(elem, painter)
        painter.drawEllipse(QRect(upperLeft, size))

    @staticmethod
    def postGenerate(elem):
        if elem.width == 0 and elem.height != 0:
            elem.width = elem.height
        elif elem.width != 0 and elem.height == 0:
            elem.height = elem.width

class LineElement():
    #AAAAAAAAAAAAAHHHHHHHHHHHHHHHHHHHHHHHH
    defaults = ShapeElement.defaults.new_child(dict(
        x2 = '1/4in',
        y2 = '1/4in',
    ))

    validators = ShapeElement.validators.new_child(dict(
        x2 = validateXY,
        y2 = validateXY,
    ))


    @staticmethod
    def paint(elem, painter:QPainter, upperLeft, size):
        ShapeElement.readyPainter(elem, painter)
        painter.resetTransform()
        painter.drawLine(elem.x, elem.y, elem.x2, elem.y2)

elemClasses = dict(
    none = Element,
    label = LabelElement,
    image = ImageElement,
    imageBox = ImageBoxElement,
    rect = RectangleElement,
    ellipse = EllipseElement,
    circle = EllipseElement,
    line = LineElement
)