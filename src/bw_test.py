#! python


from brikWorkEngine import *


app=QApplication()


#with open('test.csv', 'r', newline='') as file:
#    rows = file.read()
#layout.data = parseData(rows)


layoutString = '''
[layout]
width = 675
height = 1050
name = test[assetIndex].png
output = ./out
#data = test.csv

[title]
type = label
x = center
y = .25in
width = 1.75in
height = 2in
text = [title]
fontSize = 30

[icon]
type = image
x = center
y = 0.875in
source = ./res/[img]

[body boarder]
type = rect
x = center
y = 1.5in
width = 1.75in
height = 1.75in
xRadius = 40
yRadius = 80

[body]
type = label
x = center
y = 1.625in
width = 1.5in
height = 1.25in
text = [body]
fontFamily = Cormorant

[data]
title,img,body
Smile,smile.png,"This face is smiling."
Neutral,flat.png,"This face is neither smiling nor frowning."
Frown,frown.png,"This face is frowning, [i|unfortunate]."

'''

badLayout = '''[layout]
width = 1in
height = 1in
name = foo.png
output = ./out

[text]
type = label
height = 1in
width = 1in
text = line [rowIndex] of [rowTotal] asset [assetIndex] of [assetTotal] repeat [repeatIndex] of [repeatTotal]

[data]
repeat,text
2,foo
2,bar

'''
try:
    layout = parseLayout(layoutString)
    painter = AssetPainter(layout)
    painter.paint()
    painter.save()
except brikWorkError as e:
    print(e.message)
print('done')


#for i in data:
#    print(repr(i))


