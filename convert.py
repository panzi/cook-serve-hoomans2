#!/usr/bin/env python3

import csv
from cgi import escape as escape_html
from string import Template

def make_hoomans_html():
    with open("hoomans.html.templ") as fp:
        templ = Template(fp.read())
    
    hoomans = []
    with open("hoomans.csv") as fp:
        for row in sorted(list(csv.reader(fp)), key=lambda row: row[0].lower()):
            name = row[0].strip()
            img  = row[1].strip()
            img_url = 'https://raw.githubusercontent.com/panzi/cook-serve-hoomans2/master/sprites/' + img
            
            hoomans.append('\t\t<div class="hooman">')
            hoomans.append('\t\t\t<div class="hooman-img">')
            hoomans.append('\t\t\t\t<img src="%s" />' % escape_html(img_url))
            hoomans.append('\t\t\t</div>')
            hoomans.append('\t\t\t<div class="label">%s</div>' % escape_html(name))
            hoomans.append('\t\t</div>')
            hoomans.append('')

    html = templ.substitute(HOOMANS='\n'.join(hoomans))

    with open("hoomans.html", "w") as fp:
        fp.write(html)

if __name__ == '__main__':
    make_hoomans_html()
