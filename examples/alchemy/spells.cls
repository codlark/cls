layout {
    template: euro-poker-deck.cls
}

export {
    destination: cards
    bulk {
        name: [title].png
        include-bleed: no
    }
}

macros {
    icon = <img source="img/[1]-small.png"/>
    text-icon = <img source="img/[1]-small.png" width="37" height="37"/>
}

defaults {
    font-family: Cambria
    font-size: 9pt
    align: left, top
}

bleed-zone {
    frame {
        type: image
        source: img/[frame]-bg.png
    }
}

safe-zone {
    title {
        type: text
        text: [title]
        x: .1in
        size: 100%, .25in
        font-size: .2in
    }
    cost {
        type: text
        text: [for-each| [cost], [icon| [item]]\s\s]
        size: 100%, .25in
        align: right, middle
    }
    img {
        type: image
        source: art/[art]
        position: 0.05in, .25in

    }
    type {
        type: text
        position: 0, 2in
        size: 100%, .25in
        font-size: 10pt
        align: center, top
        text: Spell [if| [ne| [type], []], - [type]]
        
    }
    card-text {
        position: .1in, 2.15in
        size: 2.13in, 1in
        
        effect {
            
            type: text
            size: 100%, 100%
            font-size: 9pt
            text: [effect]
        }
        flavor {
            type: text
            size: 100%, 100%
            font-size: 8pt
            align: left, bottom
            text: [i| [flavor]]
        }
    }
}

data {
title, frame, art, cost, type, effect, flavor
Stone Wall, earth, stone-wall.jpg, (any, earth), Continuous, Pay [text-icon| any]: On your opponent's next turn you may prevent one spell of that type from taking affect., These walls have held off so many invaders\, I swear you can hear them say no if you get close.
Bees, air, bees.jpg, (air, air), [], Gain 3\, 1/1 Air element Bee tokens, Not the Bees!
}