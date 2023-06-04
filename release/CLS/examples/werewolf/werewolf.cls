layout {
    size: 2.5in, 3.5in
}

export {
    destination: cards
    bulk {
        name: [role][repeat-index].png
    }
}

macros {
    dark-red = #a32b1d
}

defaults {
    font-family: Palatino Linotype
}

role-container {
    position: center, .5in
    size: 1.5in, .25in

    border {
        type: rect
        size: 100%, 100%
        corner-radius: .1in
    }

    role {
        type: text
        size: 100%, 100%
        font-size: 12pt
        font-color: [if| [eq| [role], werewolf], [dark-red], black]
        
        align: center, middle
        text: [capitalize, [role]]
    }
}

icon {
    type: image
    position: center, 1in
    source: images/[role].png
}

description {
    type: text
    position: center, ^.5in
    size: 2in, .5in
    font-size: 10pt
    align: center, middle
    text: [description]
}

data {
repeat, role, description
2, werewolf, You may kill one player per night.
1, seer, You may find out the role of one player per night.
4, villager, You have no abilities.
}