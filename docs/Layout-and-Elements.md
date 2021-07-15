# Layout and Elements
brikWork uses a text file to define a layout and the elements on that layout. This document will list the types of elements as well as the properties that layouts and elements may have

[TOC]

## Layout Properties

These properties affect the layout and how assets are generated. These are mandatory

 * `width: NUM` width of the asset
 * `height: NUM` height of the asset
 * `name: FILENAME` - pattern to use for generating names of assets. If no briks are featured `[assetIndex]` will be added to the beginning of the name

These properties are optional.

 * `output: FOLDER` - folder to save the assets in. The default behavior is to save the assets in same folder as the layout file
 * `data: FILENAME` - external file to load data from. This property overrides the `data` section. If neither the `data` property nor the `data` section are present only one asset will be generated
 * `template: FILENAME` - Specify a layout file to act as a template. For a full description of templates see [Templates](Templates/)

## Element Properties

These properties are common to all elements. With the exception of the `type` property, these are all optional. Below the value name is in `ALL CAPS`

 * `type: TYPE` - the type of the element, can be one of
 * * `label` - a text label or box
 * * `image` - an external image
 * * `rect` - a rectangle with optional corner rounding
 * * `ellipse` - an ellipse or circle
 * * `circ` - an easier to spell alias for `ellipse`
 * * `line` - a line
 * `x: NUM` - this and `y` determine the upper left corner location of the element. If `center` is used instead of a number, the element will be centered in that dimension. The origin point (the 0,0 point) is at the upper left of the asset. The default value is `0`
 * `y: NUM` - this and `x` are in either pixels or inches, see [Numbers](../Values/#Numbers) . The default value is `0`
 * `width: NUM` - this and `height` determine the size of the element. Like `x` and `y` these can be in pixels or inches. The default value is `50`
 * `height: NUM` - the default value is `50`
 * `rotation: ANGLE` - the rotation of the element in degrees. The default value is `0`
 * `draw: T/F` - whether to draw the object. If false the element is not drawn.

### `label`

Labels have the most properties, which are used to customize the appearance of the text

 * `text: TEXT` - text to display. The default value is no text
 * `fontFamily: FONT` - the font family to use to render the text. The default value is `Verdana`
 * `fontSize: POINTSIZE` - the point size of the text. The default value is `18`
 * `color: COLOR` - color to render the font with, see "Colors"../Values#Colors for accepted colors. The default value is `black`
 * `wordWrap: T/F` - whether to wrap the text, if false, the text will spill over and be unreadable. The default value is `true`
 * `alignment: HORZ VERT` - how to align the text. Both `HORZ` and `VERT` must be specified. The default value is `center top`
 * * `HORZ` must be one of `left`, `center`, `right`, or `justify`
 * * `VERT` must be one of `top`, `middle`, or `bottom`
 * `italic: T/F` - these properties control text decoration. The default value for all of them is `false`
 * `bold: T/F`
 * `overline: T/F`
 * `underline: T/F`
 * `lineThrough: T/F`

#### HTML subset

Because brikWork uses Qt as its rendering engine, you can use a subset of HTML in the `text` value, this includes

 * `<b>` bold text, also usable thru the `[b| ]` brik
 * `<i>` italic text, also usable thru the `[i| ]` brik
 * `<font>` allows you to change the font family in the middle of a label
 * `<img>` places images in the text. When used in conjunction with custom briks this is a convenient way to add icons to text

These are only some of the tags available, for a fuller explanation of these and more valid HTML, visit the Qt docs for the [Supported HTML Subset](https://doc.qt.io/qt-6/richtext-html-subset.html)

### `image`

If either of an image's `width` or `height` is `0` (the default for images) then that dimension is set to the image size, while the other dimension is left alone
 
 * `source: FILENAME` - the image file to load, several filetypes are recognized but png is recommended. The default value is no value
 * `keepAspectRatio: T/F` - whether to keep the aspect ratio when resizing the image. If true the image will be scaled the same amount in both directions to a size that will fit within the size defined by `width` and `height`, if false the image will be whatever size is specified by `width` and `height` regardless of aspect ratio. The default value is `true`

### Shapes

The rest of the elements are shapes, which have certain properties in common. Not all of these properties affect every shape element. Some of these properties will be more meaningful in the future when arbitrary polygons are added
 
 * `lineColor: COLOR` - the color of the line used to draw the shape. The default value is `black`
 * `lineWidth: NUM` - the width of the line used to draw the shape, if `lineWidth` is `0` no line will be draw. The default value is `1`
 * `lineJoin: JOIN` - this affects the corners of rectangles when `lineWidth` is more than `1`. The default value is `miter`. `JOIN` must be one of
 * * `miter` - a sharp point
 * * `bevel` - a flattened corner, as if it were sanded
 * * `round` - a rounded corner
 * `lineCap: CAP` - this affects the ends of lines when `lineWidth` is more than 1. The default value is `flat`. `CAP` must be one of
 * * `flat` - no line cap, the default
 * * `square` - a square cap that extends half `lineWidth` past the end of the line
 * * `round` - a round cap like above
 * `fillColor: COLOR` - the color of the shape. The default value is `white`


### `rect`

A rect fills the entirety of its `width` and `height` with a rectangle

 * `xRadius: NUM` - this and `yRadius` control the rounding of the corners of the rectangle in the x and y directions respectively. The default value is `0`
 * `yRadius: NUM` - the default value is `0`

### `circ` and `ellipse`

Both the circ and ellipse type do the same thing, draw a round shape. The different names are merely to help you keep track of whether a shape is meant to be a circle or ellipse. If `width` and `height` are the same, a circle will be drawn, and if they are different, an ellipse will be drawn. This element has no unique properties

### `line`

A line is a simple line from one point to another. Lines cannot be rotated and any `rotation` value will be ignored

 * `x: NUM` - this and `y` define the start point for the line
 * `y: NUM`
 * `x2: NUM` - this and `y2` define the end point for the line. The default value is `50`
 * `y2: NUM` - the default value is `50`