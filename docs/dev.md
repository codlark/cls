# bwUtils

## Errors

### bwError
the base exception class, pairs a message with a prample based on the kwargs
 * origin "error in origin"
 * layout "error in layout" layout level error
 * file "error in file" "problem with a  file
 * prop "error in property of element" needs elem
 * elem "error in element"

 - InvalidPropError(elem, prop) I don't think this gets called
 - InvalidValueError(elem, prop, value)
 - InvalidArgError(elem, prop, brik, arg, value)

### bwSyntaxError
* origin
* elem (needs file)
* file

- NoValueError(file, elem, name)
- UnexpectedEOFError(file, name)
- UnclosedBrikError(elem, prop, source)

## Classes

### Collection(**kwargs)
 - _set(name, value)
 - _get(name)

### AttrDict(**kwargs)
 - items
 - copy
 - __repr
 - __contains

 ### Unit(sign, num, unit)
 - toFloat(*, dpi, whole)
 - toInt(*, dpi, whole)
 - @staticmethod fromStr(sting, signs='-+', units=(px, in, mm)) -> Unit|None
    + all = px, pt, in, mm, %

### CSVParser(source)
 - parseCSV() -> list[dict] where each dict is a row, and the keys are pulled from the header

### LayoutParser(source, filename)
 - parseLayout() -> dict representing the layout file

## functions

### asBool(string, err=False)
tries to turn a toggle into a bool
This function will be rewritten before release

### evalEscapes(string)
finds and replaces escapes with their value

### deepUpdata(self, other)
like normal dict.update but recusive

### build(accum)
collapse a string builder, equivalent to ''.join(accum).strip()


# bwStore

## classes

### BrikStore
handles the storage, scoping, and parsing of briks
 - copy() returns a copy of self at the next level scope
 - add(name, value)(func) if value is not a string then it becomes a decorator, if so value whould be an int or a pair of ints indicating the number of args
 - call(name, context, args) call brik named name with context and *args. on context are
    - store - the BrikStore object
    - parse - the associated parse method
    - source - the source string
    - prop - the name of the prop this brik was found in
    - elem - the name of the elem this brik was found in
 - parse(string) repeatedly parse out briks until none exist
 - @classmethod addStdLib(name, value)(func) like add but adds it to the standard library of briks

# brikWorkEngine

## classes

### Validation(layout)
holds all the validators and runs them, as well as owns the BrikStore. Validation is the layout wide validation while Generator is asset wide
 - validate(frame) see ElementGenerator for what's in frame. call the validator associated with the prop in frame and raise an error if it's false
 - @classmethod addValidator(name, func) add a validator to validator regristry

### frame
frame isn't a class but an AttrDict passed between Validation and ElementGenerator
- name - the name of the element
- prop - the current property being evaluated
- value - the parsed value being looked at
- layout - a proxy of the layout object as an AttrDict
- conatiner - a copy of the container of this element or 'layout'
- containerValue - the value on the container for this property or None

### ElementGenerator
Turn the Element objects into drawable elements by parsing and validating their properties.
 - generate(template, validator) turn an element object into a useable element.

### ElementPrototype
a subclass of chain map that keeps track of it's container by name
 - maps  the list of mappings used by ChainMap
 - contianer - this element's container, none if layout
 - subelements - the sub elements of this container
 - name - the name of this element
 - qualName - the qualified name of this element
 - type - the type of the element

### Element
These classes represent the types of elements, and hold default values, as well as the paint and post generation function. all these values are static
 - defaults - element scope that serves as the base of a new element
 - paint(elem, painer:QPainter, upperLeft:QPoint, size:QSize) used to draw the element. painter is the painter object to use, upperLeft and size are the location and dimensions to use. they've been adjusted for the sake of rotation and should be used instead of elem properties
 - postGenerate(elem) clean up any lose ends on the element before drawing starts, used by image to properly scale width and height before rotation

### Layout
The class the represents the layout properties
 - width
 - height
 - name
 - output
 - data
 - elements
 - template
 - defaults
 - filename
 - userBriks
 - dpi
 - pdf
 - addElement(elem) add element to elements

### AssetPainter(layout)
draws the assets, really the main runner
- layout: Layout
- validator: Validation
- images: list[QImage, str] - the generated asset images
- paint() - paints the assets, storing them in images
- makePdf() - generates a pdf
- save() - save the images

## Functions

### parseDate(rows:str)
returns the parsed data object, a list[dict] that also has the index briks inserted

### buildLayout(filename)
opens file and builds the layout out of it. 