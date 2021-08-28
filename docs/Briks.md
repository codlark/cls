# Briks
Briks are the main programming utility in brikWork. They come in 3 main types

 * variable briks like `[assetIndex]` that simply return a value
 * function briks like `[if| ]` that process arguments, and
 * operator briks that perform special parsing for operators on their argument 

## Variable Briks

The variable briks you'll most likely see are column briks, briks that are filled in by the engine based on the current data rows, and user briks, the briks defined in the `briks` section. Here are some others.

`[]` - the empty brik
This brik intentionally left blank. Use this brik when you don't want to fill in a value or argument and want to make it clear that the blank space is intentional.

`[rowIndex]` and `[rowTotal]`
`[assetIndex]` and `[assetTotal]`
`[repeatIndex]` and `[repeatTotal]`
These briks return numerical statistics about assets

 * `row` refers to the current row of the data. Assets generated from the first row of data will have a `[rowIndex]` of `1`
 * `asset` refers to the specific asset. The total number of generated assets is in `[assetTotal]`
 * `repeat` refers to the repetitions as defined by a repeat column in the data. `[repeatTotal]` is the same as the repeat value of a given row. If no repeat column is present in the data `[repeatIndex]` and `[repeatTotal]` will both be `1`
 * `Index` refers to the number of the current asset. The second card made from a row will have a `[repeatIndex]` of `2`
 * `Total` refers to the total number of that category. `[rowTotal]` is the total number of rows

These are useful for things like generating "24 out of 50" with `[rowIndex] out of [rowTotal]` where repeated cards are not counted separately. If the layout is being generated without data, these will have an undefined value, they could be one, they could be blank.

## Function Briks

Function briks can effectivly be divided into two categories, value functions and comparison functions.

### Value Functions

Value function briks modify and create values.

`[b| STRING ]`
This brik is a shortcut for bolding text with `<b>STRING</b>` in labels.

`[capitalize| STRING ]`
Capitalize `STRING`. This uses a dumb algorithm of making the first letter of any word longer than 4 letters, plus the first letter overall, uppercase.

`[dup| TIMES | STRING ]`
Duplicate `STRING` `TIMES` times. When evaluating `STRING`, the brik `[d]` is set to which duplication this is, eg `[dup| 3| \s[d] times ]` will result in " 1 times 2 times 3 times". If `TIMES` begins with a `0` then `[d]` will start counting with zero.

`[file| FILENAME ]`
Open the file `FILENAME` and return the text.

`[i| STRING ]`
This brik is a shortcut for italicizing text with `<i>STRING</i>` in labels.

`[lower| STRING ]`
Convert the entirety of `STRING` to lowercase.

`[rnd| STOP ]`
`[rnd| START | STOP ]`
Generate a random number from `START` upto and including `STOP`. `START` must be a lower number than `STOP`. 

`[s| STRING ]`
This brik is a shortcut for striking thru text with `<s>STRING</s>` in labels.

`[slice| STRING | START ]`
`[slice| STRING | START | END ]`
Select a sub string from `STRING` starting at `START` and ending with `END`. If `END` is not present then the rest of the string will be selected, if it is present the specified character won't be included. If `START` or `END` begins with a `0` that argument will count the first character as `0` the second as `1` and so on, otherwise the first charcter is `1`. Negative numbers are also allowed, which are counted from the end of the string, so `-1` is the last character.

`[substr| STRING | START | LENGTH ]`
Select a sub string of `STRING`, starting at `START` for `LENGTH`. If `START` begins with a `0` the first character will count as `0` the second as `1` and so on, other wise the first character is `1`. Negative numbers are not allowed.

!!! tip "Examples"
    Because `[slice| ]` and `[substr| ]` are so similar and so flexible, examples for both are located on  [this page](../Selecting-Strings/).

`[u| STRING ]`
This brik is a shortcut for underlining text with `<u>STRING</u>` in labels.

`[upper| STRING]`
Convert the entirety of `STRING` to uppercase.


### Comparison Functions

Comparison function briks manage compare values and return a toggle for the `[if| ]` brik, which is also described here

`[eq| LEFT | RIGHT ]`
Test if `LEFT` and `RIGHT` are equal. The arguments can be any type of value.

`[if| TEST | TRUE ]`
`[if| TEST | TRUE | FALSE ]`
Returns either `TRUE` or `FALSE` depending on `TEST`, which must evaluate to a toggle. When the first character of `TEST` is `?` the rest of the argument will be given to the comparison brik for evaluation. The `FALSE` argument is optional, and omitting it is the same as using `[]` as `FALSE`.

`[in| VALUE | ARGS... ]`
This brik takes any number of arguments. Test to see if `VALUE` is equal to any of `ARGS`.

`[ne | LEFT | RIGHT ]`
Test if `LEFT` and `RIGHT` are not equal. The arguments can be any type of value.

### Other Functions


## Operator Briks

Operator briks scan their argument for operators, special characters that the brik gives special meaning.

`[?| VALUE ]` - the comparison brik
The comparison brik performs numeric comparison. `VALUE` is evaluated for a single comparison operator with either side being the operands, if either operand is not a number parsing will stop with an error. Units are ignored so `3in`,  `3mm`, and `3%` are all treated the same as `3`.
Valid comparison operators are:

 * `==` - equal to
 * `!=` - not equal to
 * `>` - greater than
 * `>=` - greater than or equal to
 * `<` - less than
 * `<=` - less than or equal to

When the first character of `TEST` of an `[if| ]` is `?` the rest of the argument will be given to this brik for evaluation.
```none
[if|? [assetIndex] == [assetCount] | Last asset! | Still waiting... ]
```
This would evaluate to "Last asset!" on the last asset and "Still waiting..." on every other asset.

`[/| VALUE ]` - the expansion brik
The expansion brik processes and expands escapes. Normally this is the last step of evaluating a value but this brik lets you do it early. As an example, you can use the expansion brik to dynamically generate brik names.
```none
[/| \[ [someBrik] \] ]
```
Because values are evaluated until there are no more briks, this would end up evaluating a brik with the name of whatever is in `[someBrik]`.

`[=| VALUE ]` - the math brik
The math brik performs arithmetic. `VALUE` can contain any number of operators and they will be processed according to order of operations. If any operand is not a number parsing will stop with an error. Units are ignored like the comparison brik above. Operators and numbers must be separated with spaces, as in `1 + 2` but not `1+2`.
Accepted operators are:

 * `+` - addition
 * `-` - subtraction
 * `*` - multiplication
 * `/` - division
 * `%` - modulus, the remainder of division
 * `(` and `)` - grouping

To provide an example:

    [=| [assetIndex] / [assetTotal] * 100]

This would give `[assetIndex]` as a percent, for example the 21st asset of 34 would be "61.76". We can use this to draw a progress bar as in

    barHolder {
        ...
        bar {
            type: line
            ...
            x2: [=| [assetIndex] / [assetTotal] * 100]%
        }
    }

The element `barHolder` would be as wide as the bar at most, and each asset would have a longer bar than the last.