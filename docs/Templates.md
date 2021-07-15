# Layout Templates
A template is a layout file that is read before another, and are useful when making multiple layouts that feature the same elements or other properties. A template can feature anything a normal layout can, such as `layout` properties, user briks, elements, even data. Anything a layout does provide overrides the template.

Consider a set of playing cards, you could have a template that placed the indexes in the corners, then seperate layouts for aces, face cards, and rank cards. 

As an example, let's look at a set of playing cards. For the sake of brevity, we won't look at every single element and property in each file. We'll start with the template

    layout:
        width: 2.5in
        height: 3.5in
        output: cards/
        name: [suit][rank].png
We set the size of the card and the output folder so we don't need to repeat ourselves in each layout

    names:
        red: #ff1547
        #a red with just a bit of pink
        black: #1a1a3a
        #a slightly blueish grayish black
        rank: 0
        #place holder

These are the suit colors

    upperLeftNumber:
        type: label
        text: [rank]
The `[rank]` brik will be defined by each layout depending on what cards it will generate
    
        color: [if| [in| [suit] | spade | club ] | [black] | [red] ]
This sets the color according to the suit of the card
    
    upperLeftPip:
        type = image
        source = /images/[suit]Small.png
The places the pip in the corner, using the `suit` column

    data:
    suit
    spade
    heart
    club
    diamond
Lastly, the template has some test data to see where things will go. Let's take a look at what this looks like:
<img src='../img/spade0.png' width=338><hr>

## Using the template

    layout:
        template: indexes.bwl
For everything else we don't need any other properties in the `layout` section, because they'll be loaded in from the template. Here's a look at some of the rest of the face card layout

    names:
        rank: [substring| [royal] | 1 | 1 ]
        #grab the first character of [royal]

    upperArt:
        type: image
        source: /images/[color][royal].png

    data:
    suit, color, royal
    spade, black, Jack
    spade, black, Queen
    spade, black, King
    heart, red, Jack
    ...

This all gets us
<img src='../img/diamondJ.png' width=338> <hr>
Okay, so this is a chess knight not a jack protrait, but I already had this laying around from another project that never went anywhere and those portraits are little complex for my drawing ability

### Aces

    layout:
        template: indexes.bwl

    names:
        rank: A

    ace:
        type: image
        x: center
        y: center
        source: images/[suit]Big.png

    #data is pulled from the template

This layout I can present in it's entirety. Because the template provides data this layout can use it just but not having any data of it's own. Here's one of the aces
<img src='../img/heartA.png' width=338><hr>



The rest of this tutorial will be completed with a later version. I hate to leave this unfinished, but rank cards will use a feature that requires some substantial effort to implement and I want to make sure it's right. In the mean time a version of the rank cards is available in the playing card example included with brikWork