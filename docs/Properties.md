# Properties
brikWork uses a text file to define a layout and the elements on that layout. This document will list the types of elements as well as the properties that layouts and elements may have.

[TOC]


## Layout Properties

These properties affect the layout and how assets are generated. These are mandatory:

 * `width: WIDTH` width of the asset. Unit can be `px`, `in`, or `mm`.
 * `height: HEIGHT` height of the asset. Unit can be `px`, `in`, or `mm`. The `width` and `height` values must use the same unit.
 * `name: FILENAME` - pattern to use for generating names of assets. If no briks are featured `[assetIndex]` will be added to the beginning of the name. This is the only layout property that evaluates briks.

These properties are optional:

 * `output: FOLDER` - folder to save the assets in. The default behavior is to save the assets in the same folder as the layout file.
 * `data: FILENAME` - external file to load data from. This property overrides the `data` section. If neither the `data` property nor the `data` section are present only one asset will be generated.
 * `template: FILENAME` - Specify a layout file to act as a template. For a full description of templates see [Templates](Templates/).
 * `dpi: DPI` ratio to convert inches to pixels. Default value is `300` meaning 300 pixels per inch. Also affects millimeters. Number must be bare (no unit).
 * `csv: DIALECT` - dictates how to process csv data, both the `data` section and the `data` property. Can be one of
    * `brikWork` - the dialect described in [Syntax](../Syntax/). This is the default value.
    * `excel` - the dialect exported by speadsheet programs like Microsoft Excel and Google Sheets. This is a strict dialect and not recommended for hand written data, but is crucial for CSV data exported by those programs.

## PDF properties

These properties control how pdf files are generated.

 - `name: FILENAME` - The name to save the pdf as. If no name is provided, the name of the layout file will be used, eg "cards.bwl" will become "cards.pdf".
 - `xMargin: MARGIN`
 - `yMargin: MARGIN` - `xMargin` and `yMargin` control the margin on the left/right and top/bottom of the page respectively. Unit is one of 'px' or 'mm'. Both `xMargin` and `yMargin` must use the same unit and that unit must be the same unit as the `width` and `height` properties in the `layout` section. Default for both is `.25in`, which is the minimum allowed by most printers.
 - `border: WIDTH` - The width of the border to draw around assets, if 0 no border will be drawn. Units are `in` and `mm`. Default value is `.01in`
 - `pageSize: SIZE` - The size of the pages. Must be either `letter` or `A4`. Default is `letter`.
 - `orientation: ORIENTATION` - The rotation of the page. must be either `portrait` or `landscape`. Default value is `portrait`.
 - `render: TOGGLE` - If a true value, create a pdf file, if false create individual images as if the pdf section was not present. Default value is `true`.

## Element Properties

These properties are common to all elements. With the exception of the `type` property, these are all optional. Below the value name is in `ALL CAPS`.

 * `type: TYPE` - the type of the element. This is the only element property that is not evaluated for briks. `TYPE` can be one of:
    * `label` - a text label or box
    * `image` - an external image
    * `rect` - a rectangle with optional corner rounding
    * `ellipse` - an ellipse or circle
    * `circ` - an easier to spell alias for `ellipse`
    * `line` - a line
 * `x: X`
 * `y: Y` - `x` and `y` can be one of:
    * A number with units `px`, `in`, or `mm`, either positive or negative. This positions the element's upper left to its container's upper left. This is considered the standard positioning scheme.
    * A number with units `px`, `in`, or `mm`, and with the sign `^`. This positions the element's lower right to its container's lower right. An example of this is given in the playing card example.
    * A number with unit `%` which positions the element realative to its container in the same direction, eg `x: 50%` will position the left edge of the element in the middle of its container going left-right. Can only be positive.
    * `center` which centers the element within its container.
  Default value for both `x` and `y` is `0`
 * `width: WIDTH` 
 * `height: HEIGHT` - `width` and `height` can be one of:
    * A number with units `px`, `in`, or `mm`, either positive or negative.
    * A number with unit`%` which sizes the element to a ratio of its container, eg `width: 50%` will make an element half the width of its container. Can only be positive.
  Default value for both `width` and `height` is `1/4in`
 * `rotation: ANGLE` - the rotation of the element in degrees. Elements are rotated about their center. Rotation also affects the location and rotation of contained elements.  The default value is `0deg`. Unit is `deg`. Can be positve or negative.
 * `draw: TOGGLE` - whether to draw the object. If `false` the element, and any contained elements, will not be drawn.


### `label`

Labels place text on an asset and have the most properties, which are used to customize the appearance of the text:

 * `text: TEXT` - text to display. The default value is no text.
 * `fontFamily: FONT` - the font family to use to render the text. The default value is `Verdana`.
 * `fontSize: SIZE` - the point size of the text. The default value is `18pt`. Unit is one of `pt`, `px`, `in`, `mm`. Must be positive.
 * `color: COLOR` - color to render the font with, see [Colors](../Values#Colors) for accepted colors. The default value is `black`.
 * `wordWrap: TOGGLE` - whether to wrap the text, if false, the. text will spill over and be unreadable. The default value is `true`
 * `alignment: HORZ VERT` - how to align the text. Both `HORZ` and `VERT` must be specified. The default value is `center top`.
    * `HORZ` must be one of `left`, `center`, `right`, or `justify`
    * `VERT` must be one of `top`, `middle`, or `bottom`
 * `italic: TOGGLE` - these properties control text decoration. The default value for all of them is `false`.
 * `bold: TOGGLE`
 * `overline: TOGGLE`
 * `underline: TOGGLE`
 * `lineThrough: TOGGLE`

#### HTML subset

Because brikWork uses Qt as its rendering engine, you can use a subset of HTML in the `text` value, this includes:

 * `<b>` bold text, also usable thru the `[b| ]` brik
 * `<i>` italic text, also usable thru the `[i| ]` brik
 * `<font>` allows you to change the font family in the middle of a label
 * `<img>` places images in the text. When used in conjunction with user briks this is a convenient way to add icons to text

These are only some of the tags available, for a fuller explanation of these and more valid HTML, visit the Qt docs for the [Supported HTML Subset](https://doc.qt.io/qt-6/richtext-html-subset.html)

### `image`

An `image` element displays an image. This element is best suited to displaying a single image across all assets, or images of the same size.
 
 * `source: FILENAME` - the image file to load, several filetypes are recognized but png is recommended. The default value is no value.
 * `keepAspectRatio: TOGGLE` - whether to keep the aspect ratio when resizing the image. The default value is `true`.

The final size to render an image at is found with the algorithm below. In all these cases the final size of the element will affect any contained elements that are positioned with `center`.

 - If both `width` and `height` are `0` the image is drawn at full size, regardless of `keepAspectRatio`. This is the default behavior.
 - If `keepAspectRatio` is `true` and either `width` or `height` is `0` the image will be scaled evenly according to the other of the two.
 - If `keepAspectRatio` is `true` the image will be scaled evenly according to the smaller of `width` and `height`.
 - If `keepAspectRatio` is `false` the image will be scaled to exactly what `width` and `height` specify.

### `imageBox`
An `imageBox` element displays images like the `image` element, but is better suited to images of different sizes.

 * `source: FILENAME` - the image file to load, several filetypes are recognized but png is recommended. The default value is no value.
 * `keepAspectRatio: TOGGLE` - whether to keep the aspect ratio when resizing the image. The default value is `true`.
 * `alignment: HORZ VERT` - how to align a given image. Both `HORZ` and `VERT` must be specified. The default value is `center middle`.
    * `HORZ` must be one of `left`, `center`, or `right`
    * `VERT` must be one of `top`, `middle`, or `bottom`

Whereas `image` elements find the size to draw the image at by looking at the image, `imageBox` always uses the `width` and `height` properties of the element. 
 - If the image is smaller than the element, the image will be aligned according to the `alignment` property
 - If the image is larger than the element, the image will be resized to fit according to the `keepAspectRatio` property

### Shapes

The rest of the elements are shapes, which have certain properties in common. Not all of these properties affect every shape element. Some of these properties will be more meaningful in the future when arbitrary polygons are added.
 
 * `lineColor: COLOR` - the color of the line used to draw the shape. The default value is `black`.
 * `lineWidth: NUM` - the width of the line used to draw the shape, if `lineWidth` is `0` no line will be drawn. The default value is `0.01in`. Unit can be one of `px`, `in`, `mm`. Must be positive.
 * `lineJoin: JOIN` - this affects the corners of rectangles when `lineWidth` is more than `1`. The default value is `miter`. `JOIN` must be one of:
    * `miter` - a sharp point
    * `bevel` - a flattened corner, as if it were sanded
    * `round` - a rounded corner
 * `lineCap: CAP` - this affects the ends of lines when `lineWidth` is more than 1. The default value is `flat`. `CAP` must be one of:
    * `flat` - no line cap, the default
    * `square` - a square cap that extends half `lineWidth` past the end of the line
    * `round` - a round cap that extends half `lineWidth` past the end of the line
 * `fillColor: COLOR` - the color of the shape. The default value is `white`.


### `rect`

A rect fills the entirety of its `width` and `height` with a rectangle, and can have optional corner rounding.

 * `xRadius: NUM` - this and `yRadius` control the rounding of the corners of the rectangle in the x and y directions respectively. The default value is `0px`. Unit can be one of `px`, `in`, `mm`. Must be positive.
 * `yRadius: NUM` - the default value is `0px`. Unit can be one of `px`, `in`, `mm`. Must be positive.

### `circ` and `ellipse`

Both the circ and ellipse type do the same thing, draw a round shape. The different names are merely to help you keep track of whether a shape is meant to be a circle or an ellipse. This element has no unique properties. If `width` and `height` are the same, a circle will be drawn, and if they are different, an ellipse will be drawn, additionally, if either the `width` or the `height` is set to `0` but not the other than a circle will be drawn at this size, eg `width: 0.5in; height: 0;` will draw a half inch circle

### `line`

A line is a simple line from one point to another. Lines cannot be rotated and any `rotation` value will be ignored.

 * `x2: NUM` 
 * `y2: NUM` - `x2` and `y2` work the same way as `x` and `y`, described in [Element Properties](#element-properties) above. The only difference is that their default value is `1/4in`.