# Plan

*note* to build, run `python setup.py build`

release
 - finish the example

long term 
 - better errors, pass along the original porperty name and value to parse for errors
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
 - `[file| NAME ]` loads in the named file and returns the text
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


1.0
rewrite  config parsers for more control

This brik needs to be re written 
`[#| VALUE ]` - the math brik
The math brik performs arithmetic. `VALUE` can contain any number of operators and they will be processed proper order of operations. If any operand is not a number parsing will stop with an error. Inches will be converted to pixels before performing any arithmetic
Accepted operators are

 * `+` - addition
 * `-` - subtraction
 * `*` - multiplication
 * `/` - division
 * `%` - modulus, the remainder of division

Division has a specific property. If the result features a decimal portion it will propagate to the other operators, but will be removed before the brik returns.
```none
[#| [assetIndex] / [assetCount]  * 100]
```
This would give `[assetIndex]` as a percent, for example the 21st asset of 34 would be "61"
