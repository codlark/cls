import re

def parse(string:str):
    headerLine, *lines = string.split('\n')

    headers = [h.strip() for h in headerLine.split(',') if h != '']
    
    headers = []
    for h in headerLine.split(','):
        if h != '':
            headers.append(h)

    numHeaders = len(headers)
    sheet = []
    
    for line in lines:
        record = []
        c = 0
        char = ''
        cell = []
        
        if line == '':
            continue

        while c < len(line):
            char = line[c]
            
            if char == '/':
                cell.append(line[c:c+2])
                c += 2
            

            elif char == ',':
                record.append(''.join(cell).strip())
                cell = []
                if len(record)+1 == numHeaders:
                    #we break early so thre rest of the text can become the final cell
                    break
                c += 1
            
            else:
                cell.append(char)
                cell += 1

        record.append(line[c:])

'''title, image
'''