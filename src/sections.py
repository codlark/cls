### sections.py ###

import os
from collections import ChainMap
from elements import validateToggle
from utils import *

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

__all__ = ['exportTypes', 'LayoutSection']

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
        if frame.value.lower() not in ('cls', 'excel'):
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
        'include-bleed': 'includeBleed',
        'dest': 'output',
        'destination': 'output'
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
            raise CLSError("failed to save image '{asset}' to {ouput}",
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
            raise CLSError("pdf margins must use the same unit", file=layout.filename)

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
            raise CLSError("failed to render PDF, asset too large for printable area", file=painter.layout.filename)

        assetPages, mod = divmod(len(painter.images), assetAcross*assetDown)
        if mod > 0:
            assetPages += 1
        
        pdfWriter = QPdfWriter(pdf.name)
        painter._pdf = pdfWriter
        pdfWriter.setPageLayout(pageLayout)
        pdfWriter.setResolution(dpi)
        pdfWriter.setCreator('CLS Renderer')

        pdfPainter = QPainter()
        result = pdfPainter.begin(pdfWriter)
        if not result:
            raise CLSError("failed to render pdf, is the file open elsewhere?", file=painter.layout.filename)
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
            raise CLSError("generated image would be too large for Tabletop Simulator, reduce tts width", elem='tts')
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
            raise CLSError("failed to save Tabletop Simulator image to {output}",
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
        csv = 'CLS',
    ))

    validators = ChainMap(dict(
        size = Section.validateLayoutSize,
        bleed = Section.validateBleed,
        data = Section.validateString,
        dpi = Section.validateNumber(units=('px'), out=int),
        csv = Section.validateCSV,
    ))
