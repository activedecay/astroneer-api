import csv

with open('stats', newline='') as f:
    READER = csv.reader(f)
    for r in READER:  # row
        print(r[0], r[8], r[14], r[15], r[10])
