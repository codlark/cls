# Plan

*note* to build, run `python setup.py build`


for 0.6 - elements and values
 - font from files
 - css style shortcut properties, like `radius = 5` to set both radii on rect
 - texture element type that allows you yo specify a specific area of the images to draw
 - list value - `(1, 2, 3, 4, 5)` `(1:2:3:4:5)`
 - - briks like `dup` and `in` can make use of this
 - - parsing is gonna be a bitch, maybe pare out the items, then run the briks?
 - `[switch| key | match| result| match| result...]` brik
 - export {type: pdf|tts|images}
 - - would have the same props as pdf and somr from layout
 
 - rename label to textBox and add text as a direct write to the canvas, save label for an eventual imageMagick plugin
 
 - polygons and polylines
 - better toggle handler
 - custom true and false values

#v0.7
 - gradients?
 - color briks, like `[hsl| H| S| L]` that emit a color string
 - -  OR a distinct color type that generate QColors, asColor if you will
 - - something like `color = hsl|12|67|67` or `color = hsl(12,67,67)`?
 - - maybe `(hsl, 12, 67, 67)` and go full lisp?
 - - `hsl` is a keyword for interping `(12, 67, 67)` which is a list like `color: hsl (340: 200: 200)`
 
 - `inherit` value that means inherit fromm the container (what would this do if the parent is of a different type?)
 - variadic user briks `myBrik = [0],[1]` --> `[myBrik| 1| 2]` --> "1,2"
 - `c` sign or prefix on positions to allow centering by the center of the element?
 - `[brik| name | value ]`
 - some sort of alt art mechanism for image elements. specify an image to load if the desired are desn't exist, like `src: path\art.png; noArt: path\noArt.png`
 - a working directory folder property, like `folder: ` that specifies a folder that contains the resources and output folder
 - finish annotating types (maybe? not sure if this gets me much)
 - json based data? (i'm not sure what the point of this was)
 - - array of object, each object is an asset and each kv pair is a brik maybe?
 - -The ability to set specific values for each asset???
 - `[=| NAME | VALUE ]` - change the value of the element's propery
 - `[assetName]` ???
 - `[print| STRING]` prints a string to the console
 - `[asset| prop]` inspect the current asset? maybe just get the unevaluated value

 - linux support
 - look at different back ends, but it's hard to find one that supports both images in strings *and* selecting open type features

deeper integration of macro briks, like 
    
    x: # 1/8in + 1/4in
    text: [dup| #4+5| asdf]
the idea being they act like ? in [if| ], so when they get seen the value immediately gets dispatched to the macro. Make them first class. 
maybe also give macro briks `frame` made in generate


1.0
 - image magick element types, for pango and drop shadows
 - plugin support?
