# Changelog
This page collects the changes made to brikWork over time

## v 0.5
 - added: `imageBox` element type, which aligns images within its box
 - added: `csv` property to layout that controls what dialect of csv to parse data as
 - changed: unknown properties are no longer errors

## v 0.4
 - added: more units! checkout [Values](../Values/) for how they work
 - added: `[slice| STRING | START | STOP]` takes substring of `STRING` like `[substr| ]` but uses start and stop positions instead of a start position and a length
 - added: support for parenthesis to the math brik, infact the whole thing has been rewritten
 - added: pdf export
 - changed: the `[substring| ]` brik has been renamed to `[substr| ]`
 - changed: the math brik has been changed to `[=| ]` and has different semantics

## v 0.3
 - added: A graphical interface
 - added: elements can now contain other elements
 - added: `defaults` section
 - added: `[s| ]` and `[u| ]` for strike thru and underline respectively
 - changed: `names` section now called `briks`
 - changed: new css style syntax
 - changed: image resizing ruels have been tweaked
 - changed: completed the playing card example and corresponding help page
 - changed: tweaks to the csv dialect
 - fixed: layouts without a `layout` section now emit a helpful error
 - fixed: somehow the `[file| ]` brik wasn't registered properly, it's fixed now

## v 0.2
 - added: templates for layouts
 - added: a new playing card example
 - added: `draw` property on elements that controls if an element gets drawn
 - added: math brik, `[#| ]`, that processes arithmetic
 - added: `[file| ]` brik that loads in the contents of a file
 - changed: syntax is now in a more modern colon-indent style
 - changed: images are now cached when loaded for the first time
 - fixed: single column data sets now work right