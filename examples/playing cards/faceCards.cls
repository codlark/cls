layout {
    template: indexes.cls
}
macros {
    rank = [slice| [royal]| 1| 1]
    #grab the first character of [royal]
}
portrait {
    type: image
    position: center, center
    source: images/[color][royal].png
}

data {
suit, color, royal
spade, black, Jack
spade, black, Queen
spade, black, King
heart, red, Jack
heart, red, Queen
heart, red, King
club, black, Jack
club, black, Queen
club, black, King
diamond, red, Jack
diamond, red, Queen
diamond, red, King
}