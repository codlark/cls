# Plan

*note* to build, run `python setup.py build`

 - `[layout| ]` and `[card| ]` briks to inspect the layout section and this cards in particular.

 - font from files
 - take escapes out of parsing non values
 - briks for `[dup| ]` to conditionally render text depending on repeat
 - - like `[1st| |\s]` would return `[]` on the first go thru and `\s` after
 - - `[first| TRUE | FALSE ]` `[last| TRUE | FALSE ]` would cover it  I think
 - texture element type that allows you yo specify a specific area of the images to draw


 - `inherit` value that means inherit fromm the container (what would this do if the parent is of a different type?)
 - `c` sign or prefix on positions to allow centering by the center of the element?
 - some sort of alt art mechanism for image elements. specify an image to load if the desired are desn't exist, like `src: path\art.png; noArt: path\noArt.png`
 - a working directory folder property, like `folder: ` that specifies a folder that contains the resources and output folder
 - finish annotating types (maybe? not sure if this gets me much)
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


probably not gonna happen
 - polygons and polylines
 - better toggle handler
 - custom true and false values
 - gradients?
 - color briks, like `[hsl| H| S| L]` that emit a color string
 - -  OR a distinct color type that generate QColors, asColor if you will
 - - something like `color = hsl|12|67|67` or `color = hsl(12,67,67)`?
 - - maybe `(hsl, 12, 67, 67)` and go full lisp?
 - - `hsl` is a keyword for interping `(12, 67, 67)` which is a list like `color: hsl (340: 200: 200)`
 - json based data? (i'm not sure what the point of this was)
 - - array of object, each object is an asset and each kv pair is a brik maybe?
 - -The ability to set specific values for each asset???
 - `[=| NAME | VALUE ]` - change the value of the element's propery
 - `[brik| name | value ]`