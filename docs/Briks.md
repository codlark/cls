# Briks
Briks are the main programming utility in brikWork. They come in 3 main types

 * variable briks like `[assetIndex]` that simply return a value
 * function briks like `[if| ]` that process arguments, and
 * macro briks that perform special parsing on their argument

## Variable Briks

The variable briks you'll most likely see are column briks, briks that are filled in by the engine based on the current data rows, and user briks, the briks defined in the `[names]` section. Here are some others

`[]` - the empty brik
This brik intentionally left blank. Use this brik when you don't want to fill in a value or argument and want to make it clear that the blank space is intentional

`[rowIndex]` and `[rowTotal]`
`[assetIndex]` and `[assetTotal]`
`[repeatIndex]` and `[repeatTotal]`
These briks return numerical statistics about assets

 * `row` refers to the current row of the data. Assets generated from the first row of data will have a `[rowIndex]` of `1`
 * `asset` refers to the specific asset. The total number of generated assets is in `[assetTotal]`
 * `repeat` refers to the repetitions as defined by a repeat column in the data. `[repeatTotal]` is the same as the repeat value of a given row. If no repeat column is present in the data `[repeatIndex]` and `[repeatTotal]` will both be `1`
 * `Index` refers to the number of the current asset. The second card made from a row will have a `[repeatIndex]` of `2`
 * `Total` refers to the total number of that category. `[rowTotal]` is the total number of rows

These are useful for things like generating "24 out of 50" with `[rowIndex] out of [rowTotal]` where repeated cards are not counted separately. If the layout is being generated without data, these will have an undefined value, they could be one, they could be blank

## Function Briks

Function briks can be divided into two rough categories, string functions, and comparison functions

### String Functions

String function briks modify string values

`[b| STRING ]`
This brik is a shortcut for bolding text with `<b>STRING</b>` in labels

`[capitalize| STRING ]`
Capitalize `STRING`. This uses a dumb algorithm of making the first letter of any word longer than 4 letters, plus the first letter overall, uppercase.

`[dup| TIMES | STRING ]`
Duplicate `STRING` `TIMES` times. When evaluating `STRING`, the brik `[d]` is set to which duplication this is, so the first time it's `1`, the second time it's `2`, and the last time it's equal to `TIMES`

`[i| STRING ]`
This brik is a shortcut for italicizing text with `<i>STRING</i>` in labels

`[lower| STRING]`
Convert the entirety of `STRING` to lowercase

`[substring| STRING | START | LENGTH ]`
Select a sub string of `STRING`, starting at `START` for `LENGTH`. The first character of `STRING` is `1`

`[upper| STRING]`
Convert the entirety of `STRING` to uppercase


### Comparison Functions

Comparison function briks manage compare values and return a true/false value for the `[if| ]` brik, which is also described here

`[eq| LEFT | RIGHT ]`
Test if `LEFT` and `RIGHT` are equal. The arguments can be any type of value

`[if| TEST | TRUE ]`
`[if| TEST | TRUE | FALSE ]`
Returns either `TRUE` or `FALSE` depending on `TEST`, which must evaluate to a true/false value. When the first character of `TEST` is `?` the rest of the argument will be given to the comparison brik for evaluation. The `FALSE` argument is optional, and omitting it is the same as using `[]` as the false value

`[in| VALUE | ARGS... ]`
This macro takes any number of arguments. Test to see if `VALUE` is equal to any of `ARGS`

`[ne | LEFT | RIGHT ]`
Test if `LEFT` and `RIGHT` are not equal. The arguments can be any type of value

## Macro Briks

Macro briks do more processing on their argument. There are currently only 2

`[?| VALUE ]` - the comparison brik
The comparison brik performs numeric comparison. `VALUE` is evaluated for a single comparison operator with either side being the operands, if either operand is not a number parsing will stop with an error. Inches will be converted to pixels before comparison
Valid comparison operators are 

 * `==` - equal to
 * `!=` - not equal to
 * `>` - greater than
 * `>=` - greater than or equal to
 * `<` - less than
 * `<=` - less than or equal to

When the first character of `TEST` of an `[if| ]` is `?` the rest of the argument will be given to this brik for evaluation
```none
[if|? [assetIndex] == [assetCount] | Last asset! | Still waiting... ]
```
This would evaluate to "Last asset!" on the last asset and "Still waiting..." on every other asset

`[/| VALUE ]` - the expansion brik
The expansion brik processes escapes and expands them. Normally this is the last step of evaluating a value but this brik lets you do it early. As an example, you can use the expansion brik to dynamically generate brik names
```none
[/| \[ [someBrik] \] ]
```
Because values are evaluated until there are no more briks, this would end up evaluating a brik with the name of whatever is in `[someBrik]`