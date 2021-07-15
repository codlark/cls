# Plan

*note* to build, run `python setup.py build`

version 3
 - element rework
 - - defaults, templates, etc
 - 

long term 
 - vs code plugin
 - gui interface
 - fractions for inches
 - point or pixel font size
 - finish annotating types (maybe? not sure if this gets me much)
 - json based data? (i'm not sure what the point of this was)
 - pdf export
 - printer support??
 - templates
 - custom true and false values?
 - `[=| NAME | VALUE ]` - change the value of the element's propery
 - `[assetName]` ???
 - `[print| STRING]` prints a string to the console
 - mm sizes
 - `[asset| prop]` inspect the current asset? maybe just get the unevaluated value
 
 - color briks, like `[hsl| H| S| L]` that emit a color string
 - -  OR a distinct color type that generate QColors, asColor if you will
 - - something like `color = hsl|12|67|67` or `color = hsl(12,67,67)`?
 - gradients?
 - polygons and polylines
 - linux support
 - look at different back ends, but it's hard to find one that supports both images in strings *and* selecting open type features
 - css style shortcut properties, like `radius = 5` to set both radii on rect
 - imagebox element type that allow the more accurate positioning of variably sized images
 - texture element type that allows you yo specify a specific area of the images to draw
 
 - make it possible to change the defalut properties, like
 ```[defaults]
 fontFamily = Grenze
 ```
 - - thinking about this I might just re-write the element class and systems to use a chain map? Put this element templates, and parents in one update
 - parent elements, like a element template but the x and y get added to the parent
 - - element class idea, get rid of dif element classes, just a single class with all the prop validators registered separate, and the drawing funcs stored in a dict

1.0
 - rewrite  config parsers for more control
 - image magick element types, for pango and drop shadows
 - plugin support?
 - cache image files to reduce hits to the file system