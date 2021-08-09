# Selecting Strings

The briks `[slice| ]` and `[substr| ]` look similar but are actually fairly different. `slice` specifies a start and a stop, while `substr` specifies a start and a length.

    [slice| abcdefg | 2| 4]
gets "bc"

    [substr| abcdefg | 2| 4]
gets "bcde"

They can both start counting from 0

    [slice| abcdefg | 02| 04]
gets "cd"

    [substr| abcdefg | 02| 4]
gets "cdef"

Only `slice` can use negative numbers

    [slice| abcdefg | -4| -2]
gets "de"

    [substr| abcdefg | -4| 4]
gets an error

`slice` can also be used without an end, which can be handy for grabbing all but the first character in  a string.

    [slice| abcdefg | 2]
gets "bcdefg"

You can mix positive and negative arguments to `slice`

    [slice | abcdefg | 2 | -1]
gets "bcdef"

If the start is further into the string than the end, an empty string will be returned.

    [slice | abcdefg | -1| 1]
gets ""

To sumerize, use `substr` if you know how long of a sting to get and `slice` for everything else.
