# Templates and Defaults
A template is a layout file the provides elements that can be reused in multiple layout files. A template can feature anything a normal layout can, such as `layout` properties, user briks, elements, even data. Anything a layout provides overrides the template. Defaults are values assigned to properties when an element doesn't assign one, and can be changed with the `defaults` section. In this document we'll be looking at templates first.

As an example, let's look at a set of playing cards. For the sake of brevity, we won't look at every single element and property in each file. We'll start with a template that'll draw the indexes, the rank and pip in the corner, as well as define a few things important to every card.

    layout {
        width: 2.5in
        height: 3.5in
        output: cards/
        name: [suit][rank].png
    }
We set the size of the card and the output folder so we don't need to repeat ourselves in each layout.

    briks {
        red = #ff1569
        #could pass for magenta in a pinch
        black = #1a1a5e
        #more of a midnight blue really
        rank = 0
        #place holder
    }
These are the colors used for the pips, which we'll use for the ranks as well.

    upperLeftNumber {
        type: label
        text: [rank]
The `[rank]` brik will be defined by each layout depending on what cards it will generate.
    
        color: [if| [in| [suit] | spade | club ] | [black] | [red] ]
    }
This sets the color according to the suit of the card.
    
    upperLeftPip {
        type = image
        source = /images/[suit]Small.png
    }
The places the pip in the corner, using the `suit` column.

    data {
    suit
    spade
    heart
    club
    diamond
    }
Lastly, the template has some test data to see where things will go. Let's take a look at what this looks like:
<img src='../img/spade0.png' width=338><hr>

## Using the template

    layout {
        template: indexes.bwl
    }
For everything else we don't need any other properties in the `layout` section, because they'll be loaded in from the template. Here's a look at some of the rest of the face card layout.

    briks {
        rank = [substr| [royal] | 1 | 1 ]
        #grab the first character of [royal]
    }
    portrait {
        type: image
        source: /images/[color][royal].png
    }
    data {
    suit, color, royal
    spade, black, Jack
    spade, black, Queen
    spade, black, King
    heart, red, Jack
    ...
    }
This all gets us
<img src='../img/diamondJ.png' width=338> <hr>
So this is a knight from chess not a jack, but I already had this laying around from another project that never went anywhere and have you ever tried drawing one of those portraits?

### Aces

    layout {
        template: indexes.bwl
    }
    briks {
        rank = A
    }
    ace {
        type: image
        x: center
        y: center
        source: images/[suit]Big.png
    }
    #data is pulled from the template

This layout I can present in it's entirety. Because the template provides data this layout can use it by just not having any data of it's own. Here's one of the aces.
<img src='../img/heartA.png' width=338><hr>

### Jokers

Before moving onto the rank cards, I want to explain one last feature of layout templates with the jokers. A layout that uses a template can modify the elements of a template by featuring an element with the same name. Remember the `upperLeftNumber` and `upperLeftPip` elements in the indexes template? here they are in the layout for the jokers.

    upperLeftNumber {
        text: [b|J]oker
        color: [color]
    }

    upperLeftPip {
        draw: no
    }

And the joker looks like
<img src='../img/bigJoker.png' width=338><hr>

### Ranks
Now that we've fully explored how templates work, let's look at the closely related defaults, as well as container elements. As said above defaults can be changed with the `defaults` setion, so lets start on ranks there.

    defaults {
        source: images/[suit].png
    }
This sets the default `source` property so if an image doesn't supply one a pip of the assets suit will be used. Speaking of pips, let's look at a few.

    row1 {
        x: .5in
        y: .5in
        draw: [in| [rank]| 8| 9| 10]
        col1 {
            type: image
        }
        col3 {
            type: image
            x: 1.1in
        }
    }
The element `row1` is a container for the elements `col1` and `col3`, and sets it's position. The contained elements are then positioned relative to that so `col1`, instead of being at the upper left corner of the asset, is positioned to the upper left corner of the container. Likewise, `col3` is positioned 1.1 inch to the right of that. Also worth pointing out is the using of the `draw` property to control when each pip is drawn. A `false` value in a `draw` property will propagate, so if a container element is not being drawn, neither will any of the elements in that container. We can use that here because those two pips will always be drawn for the same ranks.

Here's the next row of pips. There are a couple things to point out here.

    row2 {
        x: .5in
        y: .83in
        col1 {
            type: image
            draw: [in| [rank]| 4| 5| 6]
        }
        col2 {
            type: image
            x: .55in
            draw: [in| [rank]| 2| 3| 7| 10]
        }
        col3 {
            type: image
            x: 1.1in
            draw: [in| [rank]| 4| 5| 6]
        }
    }

- the names `col1` and `col3` are repeated, this is allowed because they have different containers.
- each pip has it's own `draw` because they're not all drawn for the same ranks.

Otherwise this looks like `row1` above. Now how about some more cards?
<img src='../img/club10.png' width=338><img src='../img/diamond3.png' width=338><hr>

These playing card layouts are provided in their entirety in the examples folder, so take a look and play around with them. I'll be the first to admit they don't look the best, but they were made for demonstration purposes and I wanted to keep them simple.