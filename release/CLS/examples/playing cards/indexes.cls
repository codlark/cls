layout {
    size: 2.5in, 3.5in
}
export {
    destination: cards/
    bulk {
        name: [suit][rank].png
    }
}
macros {
    red = #ff1569
    black = #1a1a5e
    rank = 0
}
upper-left-index {
    position: 1/8in, 1/8in
    size: .3in, .6in
    
    number {
        type: text
        size: .3in, .3in
        font: 1/4in, Consolas
        font-color: [if| [in| [suit],  spade, club], [black], [red]]
        align: center, top
        text: [rank]
    }

    pip {
        type: image
        position: center, .3in
        source: images/[suit]-small.png
    }
}

lower-right-index {
    position: ^1/8in, ^1/8in
    size: .3in, .6in
    angle: 180

    number {
        type: text
        size: .3in, .3in
        font: 1/4in, Consolas
        font-color: [if| [in| [suit], spade, club], [black], [red]]
        align: center, top
        text: [rank]
    }

    pip {
        type: image
        position: center, .3in
        source: images/[suit]-small.png
    }
}

data{
suit
spade
heart
club
diamond
}