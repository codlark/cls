import os
import csv

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from bwStore import BrikStore
from bwUtils import *
from bwElements import *

class Section():
    @staticmethod
    def validateNumber(signs='+', units=('px', 'in', 'mm'), out=int): 
        def func(frame, elem):
            num = Unit.fromStr(frame.value, signs, units)
            if num is None:
                return False
            else:
                if out == int:
                    value = num.toInt()
                elif out == float:
                    value = num.toFloat()
                else:
                    value = num
                elem[frame.prop] = value
                return True
        return func
    
    @staticmethod
    def validateString(frame, sec):
        if frame.value == '[]':
            sec[frame.prop] = ''
        else:
            sec[frame.prop] = evalEscapes(frame.value)
        return True
    
    @staticmethod
    def validateMany(min, **props):
        def validator(frame, elem):
            values = commaSplit(frame.value)
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

    @staticmethod
    def validateManyStretch(**props):
        def validator(frame, elem):
            values = commaSplit(frame.value)
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

    @staticmethod
    def validateLayoutSize(frame, sec):
        values = commaSplit(frame.value)
        if len(values) != 2:
            return False
        width = Unit.fromStr(values[0], signs='+')
        if width is None:
            return False
        height = Unit.fromStr(values[1], signs='+')
        if height is None:
            return False
        sec.widthUnit = width
        sec.heightUnit = height
        return True

    @staticmethod
    def validateBleed(frame, sec):
        values= commaSplit(frame.value)
        if len(values) == 0:
            return False
        width = Unit.fromStr(values[0], signs='+', units=('in', 'mm'))
        if width is None:
            return False
        if len(values) == 1:
            height = width
        else:
            height = Unit.fromStr(values[1], signs='+', units=('in', 'mm'))
            if height is None:
                return False
        sec.bleedWidth = width
        sec.bleedHeight = height
        return True


    @staticmethod
    def validateName(frame, sec):
        if '[' not in frame.value:
            sec[frame.prop] = '[card-index]'+frame.value
        else:
            sec[frame.prop] = frame.value
        return True
    
    @staticmethod
    def validateRangeNumber(range, signs='+', units=('px', 'in', 'mm'), out=int):
        def validate(frame, sec):
            num = Unit.fromStr(frame.value, signs, units)
            if num is None:
                return False
            else:
                if out == int:
                    value = num.toInt()
                    if value < range[0] or value > range[1]:
                        return False
                elif out == float:
                    value = num.toFloat()
                    if value < range[0] or value > range[1]:
                        return False
                else:
                    if num.num < range[0] or num.num > range[1]:
                        return False
                    value = num
                sec[frame.prop] = value
                return True
        return validate

    @staticmethod
    def validatePageSize(frame, sec):
        if frame.value.lower() == 'letter':
            sec[frame.prop] = QPageSize.Letter
            return True
        elif frame.value.lower() == 'a4':
            sec[frame.prop] = QPageSize.A4
            return True
        else:
            return False
        
    @staticmethod
    def validateOrientation(frame, sec):
        if frame.value.lower() == 'portrait':
            sec[frame.prop] = QPageLayout.Portrait
            return True
        elif frame.value.lower() == 'landscape':
            sec[frame.prop] = QPageLayout.Landscape
            return True
        else:
            return False
    
    @staticmethod
    def validateCSV(frame, sec):
        if frame.value.lower() not in ('brikwork', 'excel'):
            return False
        else:
            sec[frame.prop] = frame.value.lower()
            return True

class ExportSection():
    defaults = ChainMap(dict(
        includeBleed = 'no',
        name='',
        output = '',
    ))
    validators = ChainMap(dict(
        name = Section.validateString,
        includeBleed = validateToggle,
        output = Section.validateString,
    ))
    names = ChainMap({
        'include-bleed': 'includeBleed'
    })

class BulkExport(ExportSection):
    defaults = ExportSection.defaults.new_child(dict(
        name = 'card.png',
        includeBleed = 'yes',
    ))
    validators = ExportSection.validators.new_child(dict(
        name = Section.validateName,
    ))
    names = ExportSection.names.new_child({})

    @staticmethod
    def postGenerate(layout, sec):
        layout.assetName = sec.name
    

    @staticmethod
    def export(painter, bulk):

        try:
            for image, name in painter.images:
                if bulk.includeBleed:
                    image.save(name)
                else:
                    image.copy(painter.layout.content).save(name)

        except OSError:
            raise bWError("failed to save image '{asset}' to {ouput}",
                output=painter.layout.output, layout=painter.layout.filename, asset=name
            )

class PDFExport(ExportSection):

    defaults = ExportSection.defaults.new_child(dict(
        margin = '.25in',
        border = '0.01in',
        pageSize = 'letter',
        orientation = 'portrait',
        centerInPage = 'yes',
    ))

    validators = ExportSection.validators.new_child(dict(
        margin = Section.validateManyStretch(
            xMargin=Section.validateNumber(units=('in', 'mm'), out=Unit),
            yMargin=Section.validateNumber(units=('in', 'mm'), out=Unit)
        ),
        border = Section.validateNumber(units=('in', 'mm'), out=Unit),
        pageSize = Section.validatePageSize,
        orientation = Section.validateOrientation,
        centerInPage = validateToggle,
    ))

    names = ExportSection.names.new_child({ 
        'page-size': 'pageSize',
        'center-in-page': 'centerInPage'
    })

    @staticmethod
    def postGenerate(layout, sec):
        if sec.xMargin.unit != sec.yMargin.unit:
            raise bWError("pdf margins must use the same unit", file=layout.filename)

        if sec.name == '':
            sec.name = os.path.basename(layout.filename)
        
        sec.name = os.path.splitext(sec.name)[0]+'.pdf'

    
    @staticmethod
    def export(painter, pdf):
        
        dpi = painter.layout.dpi
        border = pdf.border.toInt(dpi=dpi)
        #print(pdf)
        
        if pdf.xMargin.unit == 'in':
            unit = QPageLayout.Inch
        elif pdf.xMargin.unit == 'mm':
            unit = QPageLayout.Millimeter

        xMargin = pdf.xMargin.num
        yMargin = pdf.yMargin.num
        
        pageLayout = QPageLayout()
        pageLayout.setPageSize(QPageSize(pdf.pageSize))
        pageLayout.setOrientation(pdf.orientation)
        pageLayout.setUnits(unit)
        pageLayout.setMargins(QMarginsF(xMargin, yMargin, xMargin, yMargin))

        layout = painter.layout
        if pdf.includeBleed:
            bleedWidth = 0
            bleedHeight = 0
            assetWidth = layout.fullSize.width()
            assetHeight = layout.fullSize.height()
        else:
            bleedWidth = layout.bleed.x()
            bleedHeight = layout.bleed.y()
            assetWidth = layout.cardSize.width()
            assetHeight = layout.cardSize.height()

        paintRect = pageLayout.paintRectPixels(dpi)
        assetAcross, xofs = divmod(paintRect.width(), assetWidth)
        assetDown, yofs = divmod(paintRect.height(), assetHeight)
        xofs /= 2
        yofs /= 2
        if not pdf.centerInPage: 
            xofs = 0
            yofs = 0

        if assetAcross == 0 or assetDown == 0:
            raise bWError("failed to render PDF, asset too large for printable area", file=painter.layout.filename)

        assetPages, mod = divmod(len(painter.images), assetAcross*assetDown)
        if mod > 0:
            assetPages += 1
        
        pdfWriter = QPdfWriter(pdf.name)
        painter._pdf = pdfWriter
        pdfWriter.setPageLayout(pageLayout)
        pdfWriter.setResolution(dpi)
        pdfWriter.setCreator('brikWork')

        pdfPainter = QPainter()
        result = pdfPainter.begin(pdfWriter)
        if not result:
            raise bWError("failed to render pdf, is the file open elsewhere?", file=painter.layout.filename)
        pdfPainter.setRenderHint(QPainter.LosslessImageRendering, True)

        assetsSeen = 0
        #print(assetDown, assetAcross, assetPages)
        limit = len(painter.images)
        for page in range(assetPages):
            for down in range(assetDown):
                leftovers = limit-assetsSeen
                if leftovers < assetAcross and pdf.centerInPage:
                    xofs = (paintRect.width()-leftovers*assetWidth)/2
                for across in range(assetAcross):
                    pdfPainter.drawImage(across*assetWidth+xofs, down*assetHeight+yofs, painter.images[assetsSeen][0],
                        bleedWidth, bleedHeight, assetWidth, assetHeight
                    )
                    if border > 0:
                        pen = QPen()
                        pen.setWidth(border)
                        pdfPainter.setPen(pen)
                        pdfPainter.drawRect(across*assetWidth+xofs, down*assetHeight+yofs, assetWidth, assetHeight)
                    assetsSeen += 1
                    if assetsSeen == limit:
                        break #down
                
                if assetsSeen == limit:
                    break #across
            
            if assetsSeen == limit:
                break #page
            
            pdfWriter.newPage()

class TTSExport(ExportSection):
    defaults = ExportSection.defaults.new_child(dict(
        size= '5, 7',
    ))
    validators = ExportSection.validators.new_child(dict(
        size = Section.validateMany(2,
            width=Section.validateRangeNumber((2, 10), units=('',)), 
            height=Section.validateRangeNumber((2, 7), units=('',))
        )
    ))
    names = ExportSection.names.new_child({})

    @staticmethod
    def postGenerate(layout, sec):
        if sec.includeBleed:
            width = layout.fullSize.width()
        else:
            width = layout.cardSize.width()
        if width*sec.width > 4096:
            raise bWError("generated image would be too large for Tabletop Simulator, reduce tts width", elem='tts')
        if sec.name == '':
            sec.name = os.path.basename(layout.filename)
        name, ext = os.path.splitext(sec.name)
        if ext != 'png':
            sec.name = name+'.png'
        
    @staticmethod
    def export(painter, tts):
        layout = painter.layout
        if tts.includeBleed:
            bleedWidth = 0
            bleedHeight = 0
            assetWidth = -1
            assetHeight = -1
        else:
            bleedWidth = layout.bleed.x()
            bleedHeight = layout.bleed.y()
            assetWidth = layout.cardSize.width()
            assetHeight = layout.cardSize.height()
    
        perPage = tts.width * tts.height
        assetPages, mod = divmod(len(painter.images), perPage)
        if mod > 0:
            assetPages += 1

        tts.pages = {}
        pageSize = QSize(tts.width*assetWidth, tts.height*assetHeight)

        assetsSeen = 0
        limit = len(painter.images)
        for page in range(assetPages):
            tts.pages[page] = QImage(pageSize, QImage.Format_ARGB32_Premultiplied)
            pagePainter = QPainter()
            pagePainter.begin(tts.pages[page])
            
            for down in range(tts.height):
                for across in range(tts.width):
                    pagePainter.drawImage(across*assetWidth, down*assetHeight, painter.images[assetsSeen][0],
                        bleedWidth, bleedHeight, assetWidth, assetHeight
                    )
                    assetsSeen += 1
                    if assetsSeen == limit: 
                        break
                if assetsSeen == limit: 
                    break
            if assetsSeen == limit: 
                break
        
        try:
            if len(tts.pages) == 1:
                tts.pages[0].save(tts.name)
            else:
                for index, page in enumerate(tts.pages.values()):
                    page.save(str(index+1)+tts.name)
        except OSError:
            raise bWError("failed to save Tabletop Simulator image to {output}",
                output=painter.layout.output, layout=painter.layout.filename
            )

exportTypes = dict(
    bulk = BulkExport,
    pdf = PDFExport,
    tts = TTSExport,
)

class LayoutSection(Section):

    defaults = ChainMap(dict(
        size = '1in, 1in',
        bleed = '0in, 0in',
        data = '',
        dpi = '300',
        csv = 'brikWork',
    ))

    validators = ChainMap(dict(
        size = Section.validateLayoutSize,
        bleed = Section.validateBleed,
        data = Section.validateString,
        dpi = Section.validateNumber(units=('px'), out=int),
        csv = Section.validateCSV,
    ))

def parseLayout(filename):
    '''Parses the layout out of the file and turns it into a dict
    also handles templates'''
    if not os.path.isfile(filename):
        raise bWError("'{file}' is not a valid file",
        file=filename
        )
    try:
        with open(filename, encoding='utf-8') as file:
            layoutText = file.read()
    except OSError:
        raise bWError("'{file}' could not be opened",
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
            raise bWError("'{prop}' is not a valid layout property",
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
    layout.fullSize = QSize(layout.cardSize.width()+layout.bleed.x()*2, layout.cardSize.height()+layout.bleed.y()*2)

    sections = parsedLayout['sections']

    #data
    if layout.data != '':
        #prefer the data property over section
        dataFilename = layout.data
        if 'data' in sections:
            sections.pop('data')
        if not os.path.isfile(dataFilename):
            raise bWError("'{filename}' is not a valid file",
            file=filename, filename=dataFilename
            )
        try:
            with open(dataFilename, encoding='utf-8') as file:
                userData = file.read()
        except OSError:
            raise bWError("'{filename}' could not be opened",
            file=filename, filename=dataFilename
            )
    elif 'data' in sections:
        userData = sections['data']
    else:
        userData = None
    if userData != None:
        if layout.csv == 'brikwork':
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

    #briks
    def makeBrik(value):
        def func(context, *args):
            newStore = context.store.copy()
            newStore.add('arg-total', str(len(args)))
            for num, arg in enumerate(args):
                newStore.add(str(num+1), arg)
            return newStore.parse(value)
        return func
    layout.userBriks = {}
    if 'briks' in sections:
        briks = sections['briks']
        for name, value in briks.items():
            layout.userBriks[name] = (makeBrik(value), (0, 99))

    #elemnts
    def fix(elemName, source, dest, type, renames):
        for name, value in source.items():
            if name == 'children': continue
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

class AssetPainter():
    def __init__(self, layout):
        self.layout = layout
        self.store = BrikStore()
        if layout.data is not None:
            self.store.add('asset-total', str(len(layout.data)))
            self.store.add('row-total', str(layout.data[-1]['row-index']))
       
        self.store.briks.update(self.layout.userBriks)

        self.images = []

    def generate(self, source:dict[str, ElementProtoype], dest, container=None):
        
        for name, proto in source.items():
            elem = proto.generate(container, self.store, self.layout)
            if elem.draw:
                dest[name] = elem
                elem.subelements = {}
                if len(proto.subelements) > 0:
                    self.generate(proto.subelements, elem.subelements, elem)

    def paintElement(self, elem, painter:QPainter):
        '''Paint a given element'''
        painter.save()
        mid = QPoint(elem.width/2, elem.height/2)
        painter.translate(QPoint(elem.x, elem.y)+mid)
        painter.rotate(elem.rotation)
        elem.type.paint(elem, painter, -mid, QSize(elem.width, elem.height))
        if len(elem.subelements) > 0:
            painter.translate(-mid)
            for subelem in elem.subelements.values():
                self.paintElement(subelem, painter)

        painter.restore()

    def paintAsset(self):
        '''paint the layout and the contained elements'''
        elements = {}
        self.generate(self.layout.elements, elements)

        image = QImage(self.layout.fullSize, QImage.Format_ARGB32_Premultiplied)
        #image = QImage(self.layout.width, self.layout.height, QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.white)
        painter = QPainter(image)
        painter.setClipRect(0, 0, self.layout.fullSize.width(), self.layout.fullSize.height())
        #painter.setClipRect(0, 0, self.layout.width, self.layout.height)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.translate(self.layout.bleed)
        
        for element in elements.values():
            #painter.resetTransform()
            painter.setPen(Qt.black)
            painter.setBrush(Qt.white)
            self.paintElement(element, painter)

        return image


    def paint(self):
        '''paint a set of assets based on the current layout and data file.'''

        if self.layout.data is None:
                image = self.paintAsset()
                self.store.briks.update(dict(propertyName='card-name', elementName='layout'))
                name = self.store.parse(self.layout.assetName)
                self.images.append((image, name))

        else:
            for row in  self.layout.data:
                #TODO figure out a better way to do this
                self.store.briks.update(row)
                image = self.paintAsset()
                self.store.briks.update(dict(propertyName='card-name', elementName='layout'))
                name = evalEscapes(self.store.parse(self.layout.assetName))
                self.images.append((image, name))
                #self.image.save(os.path.join(self.layout.output, name))
    
    def export(self, target='bulk'):
        '''save the generated images.'''
        path = os.getcwd()
        if target not in exportTypes:
            raise bWError("illegal error, unknown export target", file=self.layout.filename)
        exportType = exportTypes[target]
        exportSection = self.layout.export[target]
        outputPath = exportSection.output
        if  outputPath != '' and not os.path.isdir(outputPath):
            try:
                os.mkdir(outputPath)
            except IOError:
                os.chdir(path)
                raise bWError("failed to make output directory", file=self.layout.filename)
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


if __name__ == '__main__':



    try:
        pass
    except bWError as e:
        print(e.message)
        import sys
        sys.exit()
    #print(pprint.pformat(layout.elements['icon'].subelements))