import re
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from bwUtils import *

__all__ = ["elemClasses", "ElementProtoype", "validateString", "validateNumber", "validateToggle",
    "validateMany", "validateManyStretch"]

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

def validateChoices(choices):
    def validator(frame, elem):
        if frame.value.lower() not in choices:
            return False
        elem[frame.prop] = choices[frame.value.lower()]
        return True
    return validator

def validateMany(min, **props):
    def validator(frame, elem):
        values = frame.value.split()
        if len(values) < min:
            return False
        for i, (prop, valid) in enumerate(props.items()):
            frame.prop = prop
            frame.value = values[i]
            ret = valid(frame, elem)
            if ret is False:
                return False
        return True
        
    return validator

def validateManyStretch(**props):
    def validator(frame, elem):
        values = frame.value.split()
        if len(values) == 1:
            frame.value = values[0]
            for prop, valid in props.items():
                frame.prop = prop
                ret = valid(frame, elem)
                if ret is False:
                    return False
        elif len(values) == len(props):
            for i, (prop, valid) in enumerate(props.items()):
                frame.prop = prop
                frame.value = values[i]
                ret = valid(frame, elem)
                if ret is False:
                    return False
        else:
            return False
        return True
    return validator

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

alignments = {'left':Qt.AlignLeft, 'right':Qt.AlignRight, 'center':Qt.AlignHCenter,
        'justify':Qt.AlignJustify,
        'top':Qt.AlignTop, 'bottom':Qt.AlignBottom, 'middle':Qt.AlignVCenter}

def validateAlignmentUpdate(frame, elem):
    if 'alignment' not in elem:
        elem.alignment = 0
    if frame.value.lower() in alignments:
        elem.alignment |= alignments[frame.value.lower()]
        return True
    return False

def validateAlignmentSet(frame, elem):
    terms = frame.value.lower().split()
    result = 0
    for term in terms:
        if term not in alignments:
            return False
        else:
            result |= alignments[term]
    elem.alignment = result
    return True

def validateDecoration(frame, elem):
    values = frame.value.split()
    for value in values:
        if value == 'italic':
            elem.italic = True
        elif value == 'bold':
            elem.bold = True
        elif value == 'underline':
            elem.underline = True
        elif value == 'overline':
            elem.overline = True
        elif value in ['wrap', 'word-wrap']:
            elem.wordWrap = True
        elif value in ['thru', 'through', 'line-thru', 'line-through']:
            elem.lineThrough = True
        
        elif value == 'no-italic':
            elem.italic = False
        elif value == 'no-bold':
            elem.bold = False
        elif value == 'no-underline':
            elem.underline = False
        elif value == 'no-overline':
            elem.overline = False
        elif value in ['no-wrap', 'no-word-wrap']:
            elem.wordWrap = False
        elif value in ['no-thru', 'no-through', 'no-line-thru', 'no-line-through']:
            elem.lineThrough = False

        else:
            return False
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
        userProp = frame.prop
        value = frame.value
        #trueProp = userProp
        if userProp in self.type.names:
            trueProp = self.type.names[userProp]
            #print(userProp, trueProp)
        else:
            trueProp = userProp
        frame.prop = trueProp
        #print(trueProp)
        if trueProp not in self.type.validators:
            return
        func = self.type.validators[trueProp]
        result = func(frame, frame.elem)
        if not result:
            raise InvalidValueError(frame.elem.name, userProp, value)
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
        
        xyProps = ['x', 'y', 'position', 'xy', 'start']

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

        
        if hasattr(self.type, 'midGenerate'):
            self.type.midGenerate(elem)

        for prop in xyProps:
            if prop not in self:
                continue
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
        position = validateMany(2, x=validateXY, y=validateXY),
        width = validateHeightWidth,
        height = validateHeightWidth,
        size = validateMany(2, width=validateHeightWidth, height=validateHeightWidth),
        rotation = validateAngle,
    ))
    names = ChainMap({
        'xy': 'position',
        'corner': 'position',
        'angle': 'rotation',
        'rotate': 'rotation',
    })

    @staticmethod
    def paint(elem, painter, upperLect, size):
        pass

class LabelElement():
    defaults = Element.defaults.new_child(dict(
        text = '',
        fontFamily = 'Verdana',
        fontSize = '22pt',
        fontColor = 'black',
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
        fontColor = validateString,
        wordWrap = validateToggle,
        hAlignment = validateAlignmentUpdate,
        vAlignment = validateAlignmentUpdate,
        alignment = validateAlignmentSet,
        italic = validateToggle,
        bold = validateToggle,
        overline = validateToggle,
        underline = validateToggle,
        lineThrough = validateToggle,
        decoration = validateDecoration,
        #font - family, size, color
        #decoration - for bold, underline, etc
    ))

    names = Element.names.new_child({
        'font-family': 'fontFamily',
        'font': 'fontFamily',
        'font-color': 'fontColor',
        'color': 'fontColor',
        'font-size': 'fontSize',
        'word-wrap': 'wordWrap',
        'align': 'alignment',
        'h-align': 'hAlignment',
        'v-align': 'vAlignment',
        'line-through': 'lineThrough',
        'line-thru': 'lineThrough',
    })

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
            fontUnit = 'px'
            fontSize = fontSize.toInt(dpi=dpi)
        style += f'font-size: {fontSize}{fontUnit};\n'
        style += f'color: {elem.fontColor};\n'
        if elem.italic: style += 'font-style: italic;\n'
        if elem.bold: style += 'font-weight: bold;\n'
        if elem.overline: style += 'text-decoration: overline;\n'
        if elem.underline: style += 'text-decoration: underline;\n'
        if elem.lineThrough: style += 'text-decoration: line-through;\n'
        #style += "font-variant-numeric: lining-nums;\n" someday
        label.setStyleSheet(style+'}')
        label.setText(re.sub(r'\n', '<br>', elem.text))
        painter.drawPixmap(upperLeft, label.grab())


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
        scaleWidth = '0',
        scaleHeight = '0'
    ))

    validators = Element.validators.new_child(dict(
        source = validateImage,
        keepAspectRatio = validateToggle,
        scaleWidth = validateNumber(units=('', '%'), out=Unit),
        scaleHeight = validateNumber(units=('','%'), out=Unit),
        scale = validateManyStretch(
            scaleWidth=validateNumber(units=('','%'), out=Unit),
            scaleHeight=validateNumber(units=('','%'), out=Unit)
        )
    ))

    names = Element.names.new_child({
        'keep-aspect-ratio': 'keepAspectRatio',
        'keep-ratio': 'keepAspectRatio',
        'scale-width': 'scaleWidth',
        'scale-height': 'scaleHeight',
    })

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

            if elem.scaleWidth.num != 0 and elem.scaleHeight.num != 0:
                width = elem.source.width()
                height = elem.source.height()
                if elem.scaleWidth.unit == '%':
                    newWidth = elem.scaleWidth.toInt(whole=width)
                else:
                    newWidth = elem.scaleWidth.num * width
                
                if elem.scaleHeight.unit == '%':
                    newHeight = elem.scaleHeight.toInt(whole=height)
                else:
                    newHeight = elem.scaleHeight.num * width

                elem.source = elem.source.scaled(int(newWidth), int(newHeight), aspect, scaleMode)
            
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
        alignment = 'center middle',
    ))

    validators = ImageElement.validators.new_child(dict(
        hAlignment = validateAlignmentUpdate,
        vAlignment = validateAlignmentUpdate,
        alignment = validateAlignmentSet,
    ))

    names = ImageElement.names.new_child({
        'align': 'alignment',
        'h-align': 'hAlignment',
        'v-align': 'vAlignment',
    })
    
    @staticmethod
    def paint(elem, painter:QPainter, upperLeft:QPoint, size:QSize):

        widthDif = abs(elem.source.width()-elem.width)
        heightDif = abs(elem.source.height()-elem.height)
        
        if elem.alignment & Qt.AlignLeft:
            xOfs = 0
        elif elem.alignment & Qt.AlignRight:
            xOfs = widthDif
        else: #center or justify
            xOfs = widthDif/2
        
        if elem.alignment & Qt.AlignTop:
            yOfs = 0
        elif elem.alignment & Qt.AlignBottom:
            yOfs = heightDif
        else:
            yOfs = heightDif/2

        painter.drawPixmap(upperLeft+QPoint(xOfs, yOfs), elem.source)
    
    @staticmethod
    def midGenerate(elem):
        scaleMode = Qt.SmoothTransformation
        if elem.keepAspectRatio:
            aspect = Qt.KeepAspectRatio
        else:
            aspect = Qt.IgnoreAspectRatio

        if elem.scaleWidth.num != 0 and elem.scaleHeight.num != 0:
            width = elem.source.width()
            height = elem.source.height()
            if elem.scaleWidth.unit == '%':
                newWidth = elem.scaleWidth.toInt(whole=width)
            else:
                newWidth = elem.scaleWidth.num * width
            
            if elem.scaleHeight.unit == '%':
                newHeight = elem.scaleHeight.toInt(whole=height)
            else:
                newHeight = elem.scaleHeight.num * width

            elem.source = elem.source.scaled(int(newWidth), int(newHeight), aspect, scaleMode)

        if elem.source.width() > elem.width or elem.source.height() > elem.height:
            elem.source = elem.source.scaled(elem.width, elem.height, aspect, scaleMode)

        elem.source = QPixmap.fromImage(elem.source)


validateLineJoin = validateChoices({'miter': Qt.MiterJoin, 'bevel': Qt.BevelJoin, 'round': Qt.RoundJoin})
validateLineCap = validateChoices({'flat': Qt.FlatCap, 'square': Qt.SquareCap, 'round': Qt.RoundCap})
validateLineStyle = validateChoices({'solid': Qt.SolidLine, 'dash': Qt.DashLine, 'dot': Qt.DotLine,
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
        line = validateMany(3, lineStyle=validateLineStyle, lineWidth=validateNumber(), lineColor=validateString,
            lineJoin=validateLineJoin, lineCap=validateLineCap)
    ))

    names = Element.names.new_child({
        'line-color': 'lineColor',
        'line-width': 'lineWidth',
        'line-style': 'lineStyle',
        'line-join': 'lineJoin',
        'line-cap': 'lineCap',
        'fill-color': 'fillColor',
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
        radius = validateManyStretch(xRadius=validateNumber(), yRadius=validateNumber()),
    ))

    names = ShapeElement.names.new_child({
        'rounding': 'radius'
    })

    @staticmethod
    def paint(elem, painter:QPainter, upperLeft:QPoint, size:QSize):
        ShapeElement.readyPainter(elem, painter)
        painter.drawRoundedRect(QRect(upperLeft, size), elem.xRadius, elem.yRadius)

class EllipseElement():
    defaults = ShapeElement.defaults.new_child()
    validators = ShapeElement.validators.new_child(dict(
        diameter = validateManyStretch(width=validateHeightWidth, height=validateHeightWidth)
    ))
    names = ShapeElement.names.new_child()
    #radius - r*2 for width and height
    #diameter

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
        end = validateMany(2, x2=validateXY, y2=validateXY)
    ))

    names = ShapeElement.names.new_child({
        'start': 'position'
    })


    @staticmethod
    def paint(elem, painter:QPainter, upperLeft, size):
        ShapeElement.readyPainter(elem, painter)
        painter.resetTransform()
        painter.drawLine(elem.x, elem.y, elem.x2, elem.y2)

elemClasses = {
    'none': Element,
    'label': LabelElement,
    'image': ImageElement,
    'image-box': ImageBoxElement,
    'rect': RectangleElement,
    'ellipse': EllipseElement,
    'circle': EllipseElement,
    'line': LineElement
}