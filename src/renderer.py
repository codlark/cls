### renderer.py ###

import os
import csv

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from utils import *
from parsers import *
from elements import *
from sections import *
from macros import MacroStore


def parseLayout(filename):
    '''Parses the layout out of the file and turns it into a dict
    also handles templates'''
    if not os.path.isfile(filename):
        raise CLSError("'{file}' is not a valid file",
        file=filename
        )
    try:
        with open(filename, encoding='utf-8') as file:
            layoutText = file.read()
    except OSError:
        raise CLSError("'{file}' could not be opened",
        file=filename
        )

    layout = LayoutParser(layoutText, filename).parseLayoutFile()
    if 'template' in layout['props']:
        template = parseLayout(layout['props']['template'])
        deepUpdate(template, layout)
        template['props'].pop('template', None)
        return template
    else:
        return layout

def buildLayout(filename):

    parsedLayout = parseLayout(filename)

    layoutProto = LayoutSection.defaults.new_child(parsedLayout['props'])

    frame = AttrDict()
    layout = AttrDict(filename=filename)

    for prop, value in layoutProto.items():
        if prop not in LayoutSection.validators:
            raise CLSError("'{prop}' is not a valid layout property",
            prop=prop, file=filename)
        func = LayoutSection.validators[prop]
        frame.prop = prop
        frame.value = value
        result = func(frame, layout)
        if not result:
            raise InvalidValueError('layout', prop, value)
    
    layout.cardSize = QSize(layout.widthUnit.toInt(dpi=layout.dpi), layout.heightUnit.toInt(dpi=layout.dpi))
    layout.bleed = QPoint(layout.bleedWidth.toInt(dpi=layout.dpi), layout.bleedHeight.toInt(dpi=layout.dpi))
    layout.content = QRect(layout.bleed, layout.cardSize)
    widthFull = layout.widthUnit.toFloat(dpi=layout.dpi) + layout.bleedWidth.toFloat(dpi=layout.dpi) * 2
    heightFull = layout.heightUnit.toFloat(dpi=layout.dpi) + layout.bleedHeight.toFloat(dpi=layout.dpi) * 2
    layout.fullSize = QSize(int(widthFull), int(heightFull))

    sections = parsedLayout['sections']

    #data
    if layout.data != '':
        #prefer the data property over section
        dataFilename = layout.data
        if 'data' in sections:
            sections.pop('data')
        if not os.path.isfile(dataFilename):
            raise CLSError("'{filename}' is not a valid file",
            file=filename, filename=dataFilename
            )
        try:
            with open(dataFilename, encoding='utf-8') as file:
                userData = file.read()
        except OSError:
            raise CLSError("'{filename}' could not be opened",
            file=filename, filename=dataFilename
            )
    elif 'data' in sections:
        userData = sections['data']
    else:
        userData = None
    if userData != None:
        if layout.csv == 'cls':
            reader = CSVParser(userData)
            data = reader.parseCSV()
        else:
            reader = csv.DictReader(userData.splitlines(), restval='')
            data = list(reader)
        layout.data = parseData(data)
        
    else:
        layout.data = None

    #export
    if 'export' in sections:
        exportSec = sections['export'].pop('children')
        exportDefs = sections['export']
    else:
        exportSec = {}
        exportDefs = {}
    layout.export = exportSec
    
    for exporterName, exporter in exportTypes.items():
        if exporterName in exportSec:
            proto = exporter.defaults.new_child(exportSec[exporterName])
            proto.maps.insert(1, exportDefs)
        else:
            proto = exporter.defaults.new_child(exportDefs)
        frame = AttrDict()
        section = AttrDict()
        exportSec[exporterName] = section

        for prop, value in proto.items():
            if prop == 'children':
                continue
            if prop in exporter.names:
                trueProp = exporter.names[prop]
            else:
                trueProp = prop
            if trueProp not in exporter.validators:
                continue
            func = exporter.validators[trueProp]
            frame.prop = trueProp
            frame.value = value
            result = func(frame, section)
            if not result:
                raise InvalidValueError(exporterName, prop, value)
        exporter.postGenerate(layout, section)
        

    #defaults
    if 'defaults' in sections:
        layout.defaults = sections['defaults']
    else:
        layout.defaults = {}

    #macros
    def makeMacro(value):
        def func(context, *args):
            newStore = context.store.copy()
            newStore.add('arg-total', str(len(args)))
            for num, arg in enumerate(args):
                newStore.add(str(num+1), arg)
            newStore.add('args', makeList(args))
            return newStore.parse(value)
        return func
    layout.userMacros = {}
    if 'macros' in sections:
        macros = sections['macros']
        for name, value in macros.items():
            layout.userMacros[name] = (makeMacro(value), (0, 99))

    #elemnts
    def fix(elemName, source, dest, type, renames):
        '''users can describe properties a few different ways
        this function standardizes property names, and holds on to the name the user used'''
        for name, value in source.items():
            if name == 'children':
                continue
            if name in type.shortcuts:
                values = type.shortcuts[name](value)
                if values is None:
                    raise InvalidValueError(elemName, name, value)
                for sName, sValue in values.items():
                    if sName in type.names:
                        realName = type.names[sName]
                        dest[realName] = sValue
                        renames[realName] = sName
                    else:
                        dest[sName] = sValue
                        renames[sName] = sName
            elif name in type.names:
                realName = type.names[name]
                dest[realName] = value
                renames[realName] = name
            else:
                dest[name] = value
                renames[name] = name
        

    def makeElements(source, dest, container=None):
        for name, props in source.items():

            type_ = props.pop('type', 'none')
            if type_ not in elemClasses:
                raise InvalidValueError(name, 'type', type_)
            type_ = elemClasses[type_]
            newProps = {}
            renames = {}
            fix(name, layout.defaults, newProps, type_, renames)
            fix(name, props, newProps, type_, renames)
            proto = ElementProtoype(container, name, newProps, renames, type_)
            dest[name] = proto

            children = props.pop('children')
            if len(children) > 0:
                makeElements(children, proto.subelements, proto.qualName)


    layout.elements = {}
    makeElements(parsedLayout['elements'], layout.elements)

    return layout

class CardRenderer():
    def __init__(self, layout):
        self.layout = layout
        self.store = MacroStore()
        if layout.data is not None:
            self.store.add('asset-total', str(len(layout.data)))
            self.store.add('row-total', str(layout.data[-1]['row-index']))
       
        self.store.macros.update(self.layout.userMacros)

        self.images = []

    def compile(self, source:dict[str, ElementProtoype], dest, container=None):
        '''turn a dict of element prototypes into a dict of compiled elements'''
        for name, proto in source.items():
            elem = proto.compile(container, self.store, self.layout)
            if elem.draw:
                dest[name] = elem
                elem.subelements = {}
                if len(proto.subelements) > 0:
                    self.compile(proto.subelements, elem.subelements, elem)

    def renderElment(self, elem, painter:QPainter):
        '''render a given element'''
        painter.save()
        mid = QPoint(elem.width/2, elem.height/2)
        painter.translate(QPoint(elem.x, elem.y)+mid)
        painter.rotate(elem.rotation)
        elem.type.paint(elem, painter, -mid, QSize(elem.width, elem.height))
        if len(elem.subelements) > 0:
            painter.translate(-mid)
            for subelem in elem.subelements.values():
                self.renderElment(subelem, painter)

        painter.restore()

    def renderCard(self):
        '''render the layout and the contained elements'''
        elements = {}
        self.compile(self.layout.elements, elements)

        image = QImage(self.layout.fullSize, QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.white)
        painter = QPainter(image)
        painter.setClipRect(0, 0, self.layout.fullSize.width(), self.layout.fullSize.height())
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.translate(self.layout.bleed)
        
        for element in elements.values():
            painter.setPen(Qt.black)
            painter.setBrush(Qt.white)
            self.renderElment(element, painter)

        return image


    def render(self):
        '''paint a set of assets based on the current layout and data file.'''

        if self.layout.data is None:
                image = self.renderCard()
                self.store.macros.update(dict(propertyName='card-name', elementName='layout'))
                name = self.store.parse(self.layout.assetName)
                self.images.append((image, name))

        else:
            for row in  self.layout.data:
                #TODO figure out a better way to do this
                #unless this is the good way
                self.store.macros.update(row)
                image = self.renderCard()
                self.store.macros.update(dict(propertyName='card-name', elementName='layout'))
                name = evalEscapes(self.store.parse(self.layout.assetName))
                self.images.append((image, name))
                #self.image.save(os.path.join(self.layout.output, name))
    
    def export(self, target='bulk'):
        '''save the generated images.'''
        path = os.getcwd()
        if target not in exportTypes:
            raise CLSError("illegal error, unknown export target", file=self.layout.filename)
        exportType = exportTypes[target]
        exportSection = self.layout.export[target]
        outputPath = exportSection.output
        if  outputPath != '' and not os.path.isdir(outputPath):
            try:
                os.mkdir(outputPath)
            except IOError:
                os.chdir(path)
                raise CLSError("failed to make output directory", file=self.layout.filename)
        os.chdir(os.path.realpath(outputPath))

        try:
            exportType.export(self, exportSection)
        finally:
            os.chdir(path)

        #os.chdir(path)

assetI = 'card-index'
assetT = 'card-total'
rowI = 'row-index'
rowT = 'row-total'
repeatI = 'repeat-index'
repeatT = 'repeat-total'

def parseData(data):
    #adds the counts to the roes as if they were columns
    #this should maybe be moved to the csv parser
    if data is None:
        return None

    newData = []

    if 'repeat' in data[0]:
        assetIndex = 1
        rowIndex = 1
        for row in data: #change to enumerate?
            
            repeatTotal = row.pop('repeat')
            if repeatTotal == '1':
                counts = {assetI:str(assetIndex), rowI:str(rowIndex), repeatI:'1', repeatT:repeatTotal}
                newData.append(row | counts)
                assetIndex += 1
                rowIndex += 1
            else:
                for repeat in range(int(repeatTotal)):
                    counts = {assetI:str(assetIndex), rowI:str(rowIndex), repeatI:str(repeat+1), repeatT:repeatTotal}
                    newData.append(row | counts)
                    assetIndex += 1
                rowIndex += 1

    else:
        for index, row in enumerate(data):
            counts = {assetI:str(index+1), rowI:str(index+1), repeatI:'1', repeatT:'1'}
            newData.append(row | counts)

    return newData


