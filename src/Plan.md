# Plan


release
 - figure out how to use CxFreeze for distro, it works as is, but not well
 - finish writing itch page
 - make a logo

long term 
 - better errors, pass along the original porperty name and value to parse for errors
 - vs code plugin
 - gui interface
 - fractions for inches
 - point or pixel font size
 - finish annotating types (maybe? not sure if this gets me much)
 - json based data
 - pdf export
 - printer support??
 - templates
 - custom true and false values?
 - `[=| NAME | VALUE ]` - change the value of the element's propery
 - `[assetName]`
 - `[print| STRING]` prints a string to the console
 - `[file| NAME ]` loads in the named file and returns the text
 - mm sizes
 
 - color briks, like `[hsl| H| S| L]` that emit a color string
 - -  OR a distinct color type that generate QColors, asColor if you will
 - - something like `color = hsl|12|67|67` or `color = hsl(12,67,67)`?
 - gradients?
 - polygons and polylines

`[#| VALUE ]` - The math macro
: This macro evaluates mathmatical expressions in a strict left to right order. Non number operands are an error. In properties that require a number, such `width`, if the value begins with a `#` the rest of the value will be evaluated by the math macro. Supported operators are:
 
 - `+` - addition
 - `-` - subtraction
 - `*` - multiplication
 - `\` - division

1.0
rewrite csv and config parsers for more control