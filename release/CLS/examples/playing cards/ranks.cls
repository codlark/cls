layout {
    template: indexes.cls
}
macros {
    rank = [=| [repeat-index] + 1]
}

defaults {
    source: images/[suit].png
}

row1 {
    position: .5in, .5in
    size: 1.5in, .5in
    draw: [in| [rank], 8, 9, 10]
    col1 {
        type: image
    }
    col3 {
        type: image
        x: ^0
    }
}

row2 {
    position: 0.5in, 0.9in
    size: 1.5in, .5in
    col1 {
        type: image
        draw: [in| [rank], 4, 5, 6]
    }
    col2 {
        type: image
        x: center
        draw: [in| [rank], 2, 3, 7, 10]
    }
    col3 {
        type: image
        x: ^0
        draw: [in| [rank], 4, 5, 6]
    }
}

row3 {
    position: .5in, 1.16in
    size: 1.5in, .5in
    draw: [in| [rank], 7, 8, 9, 10]
    pip13 {
        type: image
    }
    pip33 {
        type: image
        x: ^0
        }
}

row4 {
    position: 0.5in, center
    size: 1.5in, .5in
    col1 {
        type: image
        draw: [in| [rank], 6]
    }
    col2 {
        type: image
        x: center
        draw: [in| [rank], 3, 5, 7, 9]
    }
    col3 {
        type: image
        x: ^0
        draw: [in| [rank], 6]
    }
}

row5 {
    position: 0.5in, ^1.16in
    size: 1.5in, .5in
    angle: 180
    draw: [in| [rank], 7, 8, 9, 10]
    col1 {
        type: image
    }
    col3 {
        type: image
        x: ^0
    }
}

row6 {
    position: 0.5in, ^.9in
    size: 1.5in, .5in
    angle: 180
    col1 {
        type: image
        draw: [in| [rank], 4, 5, 6]
    }
    col2 {
        type: image
        x: center
        draw: [in| [rank], 2, 3, 7, 10]
    }
    col3 {
        type: image
        x: ^0
        draw: [in| [rank], 4, 5, 6]
    }
}

row7 {
    position: 0.5in, ^.5in
    size: 1.5in, .5in
    angle: 180
    draw: [in| [rank], 8, 9, 10]
    col1 {
        type: image
    }
    col3 {
        type: image
        x: ^0
    }
}

data {
repeat, suit
9, spade
9, heart
9, club
9, diamond
}