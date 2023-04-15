Templates for The Game Crafter

These templates are public domain. Copy a template into the same directory as your layout and use it in the template property of the layout section.

These templates set the size of the card to the size stated on TGC's website, and a bleed sufficient to make the full size of the card fit the expected size. They also set the DPI to 300, and for convenience set the size property of the tts section to fit the cards. Two elements are defined, safe-zone is sized and positioned so that all of it's children will be in the safe zone, the area of the card that is always guaranteed to be safe from being cut by the die. The other element is bleed-zone, which is defined to be the full size of the exported card with bleed, this is used for full bleed art.

Below is an example of what a layout using one of these templates might look like.


layout {
    template: bridge-deck.cls
}

bleed-zone {
    background-art {
        source: images/background.png
    }
}

safe-zone {
    #main card elements
}

