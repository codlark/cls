# Plan

*note* to build, run `python setup.py build`


units and dpi update

 - better toggle handler
 - 
Maybe 0.4
 - `inherit` value that means inherit fromm the container
 - `csv` section to control the dialect of csv used
 - custom true and false values?

for 0.5
 - imagebox element type that allow the more accurate positioning of variably sized images 
 - texture element type that allows you yo specify a specific area of the images to draw
 - polygons and polylines
 - color briks, like `[hsl| H| S| L]` that emit a color string
 - -  OR a distinct color type that generate QColors, asColor if you will
 - - something like `color = hsl|12|67|67` or `color = hsl(12,67,67)`?
 - gradients?
 - `c` sign or prefix on positions to allow centering by the center of the element?

long term 
 - some sort of alt art mechanism for image elements. specify an image to load if the desired are desn't exist, like `src: path\art.png; noArt: path\noArt.png`
 - a working directory folder property, like `folder: ` that specifies a folder that contains the resources and output folder
 - vs code plugin
 - finish annotating types (maybe? not sure if this gets me much)
 - json based data? (i'm not sure what the point of this was)
 - - array of object, each object is an asset and each kv pair is a brik maybe?
 - pdf export
 - printer support??
 - `[=| NAME | VALUE ]` - change the value of the element's propery
 - `[assetName]` ???
 - `[print| STRING]` prints a string to the console
 - `[asset| prop]` inspect the current asset? maybe just get the unevaluated value

 - linux support
 - look at different back ends, but it's hard to find one that supports both images in strings *and* selecting open type features
 - css style shortcut properties, like `radius = 5` to set both radii on rect

deeper integration of macro briks, like 
    
    x: # 1/8in + 1/4in
    text: [dup| #4+5| asdf]
the idea being they act like ? in [if| ], so when they get seen the value immediately gets dispatched to the macro. Make them first class. 
maybe also give macro briks `frame` made in generate


1.0
 - image magick element types, for pango and drop shadows
 - plugin support?
