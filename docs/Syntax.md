# Syntax
brikWork technically uses 3 different parsers at different points of generating assets, each with it's own quirks. For reference, we'll be looking at the werewolf.bwl example included with brikWork

```
[layout]
width = 2.5in
height = 3.5in
name = [role][repeatIndex].png
output = out/

[names]
bloodRed = #a32b1d
#maybe a little dark, but readability is important

[titleBoarder]
type = rect
x = center
y = .5in
width = 1.5in
height = .25in
lineWidth = 
xRadius = .125in
yRadius = .125in


[title]
type = label
x = center
y = .5in
width = 1.5in
height = .25in
text = [capitalize| [role] ]
color = [if| [eq| [role] | werewolf ] | [bloodRed] | black ]
alignment = center middle
fontSize = 36
fontFamily = Palatino Linotype

[icon]
type = image
x = center
y = 1in
source = images/[role].png

[data]
repeat, role
2, werewolf
4, villager
1, seer
```

## Layout File Parser

The basic structure of the layout file is of a series of sections, each started by a header. Sections include `[layout]`, `[names]`, `[data]` and element sections. Headers are square brackets with a name in between. Element sections must have unique names. The `[layout]`, `[names]`, and `[data]` sections must have those specific names

Inside `[layout]` and element sections are property definitions. Properties configure the layout when in `[layout]` or an element when in an element section. A property definition consists of a property and a value separated by an equals sign. For a full list of properties see [Layout and Elements](../Layout-and-Elements/) and for a look at values see [Values](../Values/)

### `[names]` section

The `[names]` section allows you to define user [briks](#brik-syntax). Note how the name in the example looks like a property definition. These are useful for values that will be seen repeatedly such as colors or icons for labels. Names for user briks should not include special characters, spaces are okay. There is no guarantee that some other part of brikWork won't see them as something else

### `[data]` section

The `[data]` section holds the rows of data that end up in your assets. Data is in the form of comma separated values, or CSV. The first row is the header, which is used as a [brik](#brik-syntax) to insert it into your asset. The `[data]` section must be the last section in the file

### Whitespace

In layout definition files newlines separate property definitions, making it an error to put two property definitions on a single line. Otherwise, spaces and tabs are largely ignored, and are removed when they touch the begining of a line, the end of a line, or the equals sign

### Comments

A comment is a line that has a pound sign, `#`, for its first character. Everything after the pound sign is ignored, including property definitions. Comments are also available in data

## Brik Syntax

Briks are the programming utility of brikWork, as well as its namesake. Briks exist in values and are marked by square brackets, much like section headers. A brik returns a value, either as a variable brik like `[repeatIndex]` or as a function brik like `[capitalize| ]`. Variable briks include column briks like `[name]` which pull values from the data, and user briks like `[res]` which are defined in the `[names]` section. Like properties and values, spaces and tabs surrounding brik names are ignored. The act of turning a brik into a value is called evaluation. For a full list of briks provided by brikWork see [Briks](../Briks/)

Function briks have extra syntax over other briks in the form of arguments. Arguments are values that are seen by the underlying code of a brik in order to generate the final returned value. The brik name and arguments are separated by vertical bars, and while brik names are not evaluated the arguments are, thus `[capitalize| [name] ]` will give us the capitalized forms Moderator, Werewolf, and Villager in the final asset

### Escapes

An escape is a means of preventing a part of a value from being evaluated, it "escapes" the parser. brikWork uses the common idiom of using the back slash `\` as the escape character, with any character after it not having any special value, this can be used to put square brackets in your value without them being evaluated as briks, or to put spaces at the edge of a value. Escapes known to brikWork are

Escape | Meaning | Escape | Meaning
------ | ------- | ------ | -------
`\n` | a new line | `\s` | a space
`\t` | a tab | `\\` | a literal backslash

Anything else has it's back slash removed and put into the final value. Because escapes are the last thing evaluated something like `\[new\]` won't be evaluated as a brik and instead will be "[new]" in the asset

## CSV Syntax

brikWork uses comma seperated values for data. Like with properties and values, any whitespace that touches the comma is removed. The first row is used as names for column briks. Commas can be escaped to be included in the data with `\,`. The parser keeps track of how many names are seen in the first row as well as how many columns it's seen on the current row, if the parser knows it's on the last column of a row it will ignore any more commas

A layout file does not need any data. If both the `data` property is blank and the `[data]` section is not used, only one asset will be generated, and no column blocks will be available. Data is also considered blank if there are fewer than two lines

A column with the name `repeat` acts as a special column. When a row's repeat value is more than one, multiple assets are generated from that row, each evaluated on their own, each counted as their own asset. A repeat column is not required

The way brikWork works is to build the layout from the above sections, then for each row in the data, a new asset is generated by evaluating all the properties of all the elements, with the column briks set to the values in the same column of the current row
