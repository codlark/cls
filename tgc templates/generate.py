import csv

templateData = []

with open('template-data.csv', newline='') as file:
    reader = csv.DictReader(file)
    for row in reader:
        templateData.append(row)

scriptTemplate = '''#This template layout describes a '{cardType}' card from The Game Crafter
layout {{
    size: {cardWidth}in, {cardHeight}in
    bleed: {bleedWidth}in, {bleedHeight}in
    dpi: 300
}}

export {{
    tts {{
        size: {ttsWidth}, 7
    }}
}}

bleed-zone {{
    position: -{bleedWidth}in, -{bleedHeight}in
    size: {fullWidth}in, {fullHeight}in
}}

safe-zone {{
    position: center, center
    size: {safeWidth}in, {safeHeight}in
}}
'''

for row in templateData:
    print('now making:', row['cardType'])

    ttsWidth = int(4096 // (float(row['cardWidth']) * 300))
    
    with open(row['cardType']+".cls", 'w') as file:
        file.write(scriptTemplate.format(ttsWidth=ttsWidth, **row))

print('all done')