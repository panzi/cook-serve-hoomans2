#!/usr/bin/env python3

import escsv
from os.path import join as pjoin, abspath, dirname

def make_list():
    names = []
    with open(pjoin(dirname(abspath(__file__)), "..", "hoomans.csv")) as fp:
        for line in sorted(list(row[0].strip() for row in escsv.read(fp)), key=lambda name: name.lower()):
            names.append(line.strip().split('\n')[0])
    n = len(names)
    part_count = 4
    partlen = (n + part_count - 1) // part_count
    lines = []
    maxlens = [0] * part_count
    for off in range(partlen):
        line = []
        for part in range(part_count):
            i = part * partlen + off
            if i < n:
                name = names[i]
                namelen = len(name)
                if namelen > maxlens[part]:
                    maxlens[part] = namelen
                line.append(name)
        lines.append(line)
    
    for line in lines:
        outline = []
        for maxlen, name in zip(maxlens, line):
            pad = maxlen - len(name)
            outline.append(name + (' ' *pad))
        print('   '.join(outline).rstrip())

if __name__ == '__main__':
    make_list()
