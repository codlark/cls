# Layout and Elements
brikWork uses a text file to define a layout and the elements on that layout. This document will list the types of elements as well as the properties that layouts and elements may have

[TOC]

## Layout Properties

These properties affect the layout and how assets are generated. These are mandatory.

 * `width: NUM` width of the asset.
 * `height: NUM` height of the asset.
 * `name: FILENAME` - pattern to use for generating names of assets. If no briks are featured `[assetIndex]` will be added to the beginning of the name. This is the only layout property that evaluates briks.

These properties are optional.

 * `output: FOLDER` - folder to save the assets in. The default behavior is to save the assets in same folder as the layout file.
 * `data: FILENAME` - external file to load data from. This property overrides the `data` section. If neither the `data` property nor the `data` section are present only one asset will be generated.
 * `template: FILENAME` - Specify a layout file to act as a template. For a full description of templates see [Templates](Templates/).

## Element Properties

These properties are common to all elements. With the exception of the `type` property, these are all optional. Below the value name is in `ALL CAPS`.

 * `type: TYPE` - the type of the element. This is the only element property that does not evaluate briks. `TYPE` can be one of
 * * `label` - a text label or box
 * * `image` - an external image
 * * `rect` - a rectangle with optional corner rounding
 * * `ellipse` - an ellipse or circle
 * * `circ` - an easier to spell alias for `ellipse`
 * * `line` - a line
 * `x: NUM` - this and `y` determine the upper left corner location of the element. If `center` is used instead of a number, the element will be centered in that dimension. The origin point (the 0,0 point) is at the upper left of the asset. The default value is `0`. If the element these properties belong to is contained in another element, the element will be positioned relative to the cotainer, this also affects `center`.
 * `y: NUM` - this and `x` are in either pixels or inches, see [Numbers](../Values/#Numbers) . The default value is `0`
 * `width: NUM` - this and `height` determine the size of the element. Like `x` and `y` these can be in pixels or inches. The default value is `50`
 * `height: NUM` - the default value is `50`
 * `rotation: ANGLE` - the rotation of the element in degrees. The default value is `0`
 * `draw: TOGGLE` - whether to draw the object. If `false` the element is not drawn.

### `label`

Labels place text on an asset and have the most properties, which are used to customize the appearance of the text.

 * `text: TEXT` - text to display. The default value is no text
 * `fontFamily: FONT` - the font family to use to render the text. The default value is `Verdana`
 * `fontSize: POINTSIZE` - the point size of the text. The default value is `18`
 * `color: COLOR` - color to render the font with, see "Colors"../Values#Colors for accepted colors. The default value is `black`
 * `wordWrap: TOGGLE` - whether to wrap the text, if false, the text will spill over and be unreadable. The default value is `true`
 * `alignment: HORZ VERT` - how to align the text. Both `HORZ` and `VERT` must be specified. The default value is `center top`
 * * `HORZ` must be one of `left`, `center`, `right`, or `justify`
 * * `VERT` must be one of `top`, `middle`, or `bottom`
 * `italic: TOGGLE` - these properties control text decoration. The default value for all of them is `false`
 * `bold: TOGGLE`
 * `overline: TOGGLE`
 * `underline: TOGGLE`
 * `lineThrough: TOGGLE`

#### HTML subset

Because brikWork uses Qt as its rendering engine, you can use a subset of HTML in the `text` value, this includes

 * `<b>` bold text, also usable thru the `[b| ]` brik
 * `<i>` italic text, also usable thru the `[i| ]` brik
 * `<font>` allows you to change the font family in the middle of a label
 * `<img>` places images in the text. When used in conjunction with custom briks this is a convenient way to add icons to text

These are only some of the tags available, for a fuller explanation of these and more valid HTML, visit the Qt docs for the [Supported HTML Subset](https://doc.qt.io/qt-6/richtext-html-subset.html)

### `image`

An `image` element displas an image.
 
 * `source: FILENAME` - the image file to load, several filetypes are recognized but png is recommended. The default value is no value
 * `keepAspectRatio: TOGGLE` - whether to keep the aspect ratio when resizing the image. The default value is `true`

The final size to render an images uses the below algorithm. In all these cases the final size of the element will affect any contained elements that are positioned with `center`.

 - If both `width` and `height` are `0` the image is draw at full size, reguardless of `keepAspectRatio`. This is the default behavior.
 - If `keepAspectRatio` is `true` and either `width` or `height` is `0` the image will be scaled evenly according to the other.
 - If `keepAspectRatio` is `true` the image will be scaled evenly according to the smaller of `width` and `height`.
 - If `keepAspectRatio` is `false` the image will be scaled to exactly what `width` and `height` specify.

### Shapes

The rest of the elements are shapes, which have certain properties in common. Not all of these properties affect every shape element. Some of these properties will be more meaningful in the future when arbitrary polygons are added.
 
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

A rect fills the entirety of its `width` and `height` with a rectangle, and can optional corner rounding.

 * `xRadius: NUM` - this and `yRadius` control the rounding of the corners of the rectangle in the x and y directions respectively. The default value is `0`
 * `yRadius: NUM` - the default value is `0`

### `circ` and `ellipse`

Both the circ and ellipse type do the same thing, draw a round shape. The different names are merely to help you keep track of whether a shape is meant to be a circle or ellipse. This element has no unique properties. If `width` and `height` are the same, a circle will be drawn, and if they are different, an ellipse will be drawn, additionally, if either the `width` or the `height` is set to `0` but not the other than a circle will be draw at this size, eg `width: 0.5in; height: 0;` will draw a half inch circle

### `line`

A line is a simple line from one point to another. Lines cannot be rotated and any `rotation` value will be ignored.

 * `x: NUM` - this and `y` define the start point for the line
 * `y: NUM`
 * `x2: NUM` - this and `y2` define the end point for the line. The default value is `50`
 * `y2: NUM` - the default value is `50`