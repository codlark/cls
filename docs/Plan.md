# Plan

*note* to build, run `python setup.py build`


version 3


units and dpi update
 - fractions for inches
 - point or pixel font size
 - mm sizes
 - custom DPI
 - specify a location as being relative to the other end, eg `x: ^1in;` would put something at 1 inch in from the right side, as oppesed to `x: -1in;` which puts things one inch to the left of the asset

 - polygons and polylines
 - imagebox element type that allow the more accurate positioning of variably sized images
 - texture element type that allows you yo specify a specific area of the images to draw

long term 
 - some sort of alt art mechanism for image elements. specify an image to load if the desired are desn't exist, like `src: path\art.png; noArt: path\noArt.png`
 - a working directory folder property, like `folder: ` that specifies a folder that contains the resources and output folder
 - vs code plugin
 - finish annotating types (maybe? not sure if this gets me much)
 - json based data? (i'm not sure what the point of this was)
 - - array of object, each object is an asset and each kv pair is a brik maybe?
 - pdf export
 - printer support??
 - custom true and false values?
 - `[=| NAME | VALUE ]` - change the value of the element's propery
 - `[assetName]` ???
 - `[print| STRING]` prints a string to the console
 - `[asset| prop]` inspect the current asset? maybe just get the unevaluated value

 - color briks, like `[hsl| H| S| L]` that emit a color string
 - -  OR a distinct color type that generate QColors, asColor if you will
 - - something like `color = hsl|12|67|67` or `color = hsl(12,67,67)`?
 - gradients?
 - linux support
 - look at different back ends, but it's hard to find one that supports both images in strings *and* selecting open type features
 - css style shortcut properties, like `radius = 5` to set both radii on rect


1.0

 - `include: LAYOUTFILE` strip the elements out of LAYOUTFILE and make them children of this element
 - image magick element types, for pango and drop shadows
 - plugin support?
