# Syntax
brikWork technically uses 3 different parsers at different points of generating assets, each with it's own quirks.

## Layout File Parser

The basic structure of the layout file is of a series of sections. Sections consist of a name followed by contents enclosed in curly braces, for example
```
layout {
    width: 2.5in
}
```
Different sections can feature different contents. The standard type of contents is a series of property definitions, which feature a property name, a colon, and a value, and are ended by either a semi colon or the end of the line.
```
    italic: yes; bold: yes;
```
The indentation is not required but reccomended for readability. There are two kinds of sections, special sections that control the operation of the engine and element sections that describe elements that become the asset.

## Special Sections

There are 4 special sections.

The `layout` section specifies the size of the final asset as well as interactions with the file system. This section uses property definitions. A full list of properties available to the `layout` section are listed in [Layout and Elements](../Layout-and-Elements/).

The `data` section specifies data used in generating assets. This section uses the CSV syntax described [below](#csv-syntax).

The `briks` section specifies briks available to the user. The contents of this section use a syntax similar to variable definition in other languages. A description of briks is [below](#brik-syntax).
```
briks {
    Heliotrope = #DF73FF
}
```

The `defaults` section specifies defaults for element properties. This section uses property definitions.

## Element Sections

Element sections describe the text, images, and shapes that make the final asset. Element sections must have unique names and those names can't be the names of the special sections, nor can they contain any special characters like colon or curly braces, spaces are okay.

### Whitespace

Whitespace is largly ignored. The rule of thumb is that whitespace on boundries is removed. In a property definition such as `text: NOW that's what I call tokens     ;` the property name is "text" and the value is "NOW that's what I call tokens". When whitespace is meaningful it is called out in the description of that syntax.

### Comments

A comment is a line that has a pound sign, `#`, for its first character after any indent. Everything after the pound sign is ignored until the end of the line.

## Brik Syntax

Briks are the programming utility of brikWork, as well as its namesake. Briks are used in values and are surrounded by square brackets. A brik returns a value, either as a variable brik like `[repeatIndex]` or as a function brik like `[capitalize| ]`. Variable briks include column briks` which pull values from the data, and user briks  which are defined in the `briks` section. The act of turning a brik into a value is called evaluation. For a full list of briks provided by brikWork see [Briks](../Briks/).

Function briks have extra syntax over other briks in the form of arguments. Arguments are values that are seen by the underlying code of a brik in order to generate the final returned value. The brik name and arguments are separated by vertical bars. Brik arguments are evalutated as part of evalutating the brik, and if the birk returns a value that contains briks they too will be evaluated.

### Escapes

An escape is a means of preventing a part of a value from being evaluated, it "escapes" the parser. brikWork uses the common idiom of using the back slash `\` as the escape character, with any character after it not having any special value, this can be used to put square brackets in your value without them being evaluated as briks, or to put spaces at the edge of a value. Escapes known to brikWork are

Escape | Meaning | Escape | Meaning
------ | ------- | ------ | -------
`\n` | a new line | `\s` | a space
`\t` | a tab | `\\` | a literal backslash

Anything else has it's back slash removed and put into the final value. Because escapes are the last thing evaluated something like `\[new\]` won't be evaluated as a brik and instead will be "[new]" in the asset.

## CSV Syntax

brikWork uses comma seperated values for data. Like with colons seperating properties and values, any whitespace that touches the comma is removed. The first row is used as names for column briks. Commas can be escaped to be included in the data with `\,`. The parser keeps track of how many names are seen in the first row as well as how many columns it's seen on the current row, if the parser knows it's on the last column of a row it will ignore any more commas.

A layout file does not need any data. If both the `data` property in hte `layout` section is blank and the `data` section is not used, only one asset will be generated, and no column blocks will be available. Data is also considered blank if there are fewer than two lines.

A column with the name `repeat` acts as a special column. When a row's repeat value is more than one, multiple assets are generated from that row, each evaluated on their own, each counted as their own asset. A repeat column is not required.

The way brikWork works is to build the layout from the above sections, then for each row in the data, a new asset is generated by evaluating all the properties of all the elements, with the column briks set to the values in the same column of the current row.
