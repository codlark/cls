layout {
    template: indexes.cls
}

export {
    bulk {
        name: [name].png
    }
}

upper-left-index {
    number {
        size: .75in, .5in
        font-color: [color]
        align: center, top
        text: [b|J]oker
    }
    pip {
        draw: off
    }
}

lower-right-index {
    number {
        size: .75in, .5in
        font-color: [color]
        align: center, top
        text: [b|J]oker
    }
    pip {
        draw: off
    }
}

portrait {
    type: image
    position: center, center
    source: images/[name].png
}

data {
color, name
[black], bigJoker
[red], smallJoker
}