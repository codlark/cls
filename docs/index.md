# brikWork
brikWork is a scripty board game asset maker, allowing you to make assets, like cards or tokens, with a simple INI description file and CSV data file. On these pages you'll find detailed explanations of the syntax and properties used to make assets

## brikWork layouts in brief

A layout file is an INI file with an optional section of CSV data at the end that gets turned into a set of assets. Data from the CSV data is available to the layout to generate distinct assets. A layout is made of elements and those elements have properties that are set to values, including a programming utility called briks

## brikWork layouts in longer

A layout file is an INI file with sections for the layout properties and the elements
```none
[layout]
width = 2.5in
height = 3.5in

[title]
text = This is a [capitalize| [title] ] card!
x = center
y = 1in

[image]
source = [image]
x = center
y = center
```
Layout files can also have CSV style data at the bottom
```
[data]
image, title
./images/smile.png, smiley face
```
For each row in the data, a new asset will be generated with the data from that row available as a brik with the name of the corresponding header.
Briks are the programing utility within values. Briks can be variables like `[title]`, or they can be functions like `[capitalize| ]` 

For more in depth information check out any of the pages in the nav bar. If you have questions post them to the forum on the itch.io page at [codlark.itch.io/brikwork](codlark.itch.io/brikwork)


## Conventions used in this guide

* Any text meant to be text the user enters in a layout file will have `code styling` this includes numbers like `0` and text like `this`
* Section headers are always presented with their square brackets like `[layout]`
* Briks are always presented with their square brackets, and functions with their first vertical bar like `[rowIndex]` and `[if| ]`
* Property values and function brik arguments are presented in ALL CAPS when being defined like `[lower| STRING ]`

