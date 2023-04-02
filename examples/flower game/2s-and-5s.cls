layout {
    #size: 2.5in, 3.75in
    size: 2.5in, 3.5in
    bleed: 1/8in, 1/8in
    
    data: flowers.csv
    dpi: 300
}
#pdf{
#    contentOnly: yes
#    #border: 0in
#    #render: yes
#}
export {
    include-bleed: no
    destination: cards
    bulk {
        include-bleed: yes
        name: [major][minor][repeat-index].png
    }
    pdf {
        output: []
        center-in-page: yes
    }
}

defaults {
    width: 3/4in
    height: 3/4in
}
macros {
    indexOfs = 1/8in
}
bg {
    type: image
    source: img/bg/[major].png
    position: -1/8in, -1/8in
    size: 0,0
}

index {
    position: .15in, .15in
    major {
        type: image-box
        size: 1/4in, 1/4in
        source: img/index/[major].png
    }
    minor {
        type: image-box
        y: 0.3in
        size: 1/4in, 1/4in
        source: img/index/[minor].png
    }
}

major {
    type: image-box
    position: .3in, [if|? [repeat-index] == 1| 3/4in | 1in ]
    source: img/[major].png
}

minor {
    type: image-box
    position: ^.3in, [if|? [repeat-index] == 1| 1in | 3/4in ]
    source: img/[minor].png
}

turns {
    #turns hold the rotated elements, and defines its rect as the lower half of the card
    angle: 180
    position: 0, 1.3/4in
    size: 2.5in, 1.3/4in

    index {
        position: .15in, .15in
        major {
            type: image-box
            size: 1/4in, 1/4in
            source: img/index/[major].png
        }
        minor {
            type: image-box
            y: 0.3in
            size: 1/4in, 1/4in
            source: img/index/[minor].png
        }
    }

    major {
        type: image-box
        position: .3in, [if|? [repeat-index] == 1| 3/4in | 1in ]
        source: img/[major].png
    }

    minor {
        type: image-box
        position: ^.3in, [if|? [repeat-index] == 1| 1in | 3/4in ]
        source: img/[minor].png
    }
}
