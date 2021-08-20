# Values
This is a shorter page to quickly go over the types of values used by properties.

## Numbers

Numbers are just that, numbers. brikWork allows for three kinds of numbers:
 - A whole number, like `1` or `23`
 - A decimal number, like `1.25` or `.5`
 - A fraction, like `2/3` or `1/8`. Fractions can have a number component as well by separating the whole number from the fraction with a dot `.` or another slash `/`, like `1.1/4` or `3/1/2`

Numbers can also have other features like units. Different properties allow different units, these will be listed in the property's entry on [Properties](../Properties/). Units are always optional, and when a unit is not provided the unit listed in the description of a property will be the default, for example `fontSize` lists units `pt`, `px`, `in`, and `mm`, so any value without a unit will be given the unit `pt`. Numbers can also hava a sign, either positive `+` or negative `-`. Some properties require positive numbers and will say so in their description. When no sign is given the number will be positive. The `x` and `y` properties also allow a sign of inverse `^` which cannot be combined with the other signs.
Units you'll see in brikWork include

 - `px` - pixel, this is the native unit of brikWork for most things
 - `in` - inch, these are converted to pixels according to the `dpi` property of the layout
 - `mm` - millimeter, these are converted to inches before being converted to pixels
 - `pt` - point, this is a common unit for measuring fonts; exactly how big a given point size is depends on the font, but generally, at 300 dpi, a 40pt to 44pt font will snuggly fit into a quarter inch tall space
 - `%` - a percent, this is a proportion of a property on another element
 - `deg` - degree, this is a unit of rotation

Any property or brik that uses different units will describe them in their description.

## Toggles

Some properties merely need to know if you want them on or off, such as the `underline` property of labels. This is done with toggle values. A toggle value tells its associated property true or false, on or off. A true value is one of `true`, `yes`, and `on` while a false value is one of `false`, `no`, `off`, `0`, or an empty string. They all evaluate the same in the end, so use whichever feels more readable. 

## Colors

Currently colors in brikWork exist in a rather rudimentary state, they can either be in hex color codes like `#ff00ff` or they can be one of the named SVG colors, which are highly suitable for simple colors like black and white, or for testing.

## Strings

A string is any value or other piece of text that isn't one of the above values types, such as the `source` property on image elements. Some properties further restrict the allowed values of strings, which are detailed in their entry on [Properties](../Properties/).

## File Paths

The several layout properties and the `source` property of images use file paths. Due to backslash being the escape character, use a forward slash `/` as the path separator on Windows and they'll be properly converted. Paths are considered relative to the location of the layout file as long as they don't begin with a slash, otherwise they will be considered as being at the root of the file system, C:\ on Windows. When in doubt there's nothing wrong with using the full file path. Folders should end with a slash, like the `out/` in the werewolf example.