# Values
This is a shorter page to quickly go over the types of values used by properties

## Numbers

Most numbers used in brikWork are locations and sizes, like `x` and `width`. These numbers, called `NUM` on [Layout and Elements](../Layout-and-Elements/), by default are in pixels and aren't allowed to have a decimal point. Sizes can also be in inches, by having `in` attached to the end, like `1in`. Inches can have a decimal point like `1.25in`. Inches are converted to pixels at a dpi(dots per inch) of 300 which is commonly used by print on demand services. In a future update, not only will there be more units but also dpi will be changeable

Lastly some properties use numbers in different units, these will be spelled out in their entry on [Layout and Elements](../Layout-and-Elements/).

## True/False values

Some properties merely need to know if you want them on or off, such as `underline`. This is done with true/false values. Indicated with `T/F` on "Layout and Elements":../Layout-and-Elements , these values are fairly flexible. A true value is one of `true`, `yes`, and `on` while a false value is one of `false`, `no`, `off`, `0`, or an empty string. They all evaluate the same in the end, so use whichever feels more readable. In a future update the user will be able to add more true/false values

## Colors

Currently colors in brikWork exist in a rather rudimentary state, they can either be in hex color codes like `#ff00ff` or they can be one of the named SVG colors, which are highly suitable for reaching simple colors like black and white, or for testing. In a future update colors will be more robust, such as the ability to specify colors in hue-saturation-value and the ability to specify transparency

## Strings

A string is any value or other piece of text that isn't one of the above values types, such as the `source` property on image elements. Some properties further restrict the allowed values of strings, which are detailed in their entry on [Layout and Elements](../Layout-and-Elements/)

## File Paths

The `output` and `data` properties of the `[layout]` section and the `source` property of images use file paths. Due to backslash being the escape character, use a forward slash `/` as the path separator even on Windows, they will be properly converted. Paths are considered relative to the location of the layout file as long as they don't begin with a slash, otherwise they will be considered as being at the root of the file system, C:\ on Windows. When in doubt there's nothing wrong with using the full file path