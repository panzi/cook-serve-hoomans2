#!/usr/bin/env python3

import csv
from os.path import join as pjoin, abspath, dirname

FOLDERS = ('CUST_SPR_POOR', 'CUST_SPR_COMMON', 'CUST_SPR_RICH')

def free():
	free_map = {folder: set(range(73)) for folder in FOLDERS}

	with open(pjoin(dirname(abspath(__file__)), '..', 'hoomans.csv'), 'r') as fp:
		for row in csv.reader(fp):
			hpath = row[1].strip()
			folder, filename = hpath.split("/")
			number, ext = filename.split(".")
			if ext == "png":
				free_map[folder].remove(int(number))

	for folder in FOLDERS:
		free_slots = free_map[folder]
		if free_slots:
			print(folder+ ':')
			for number in sorted(free_slots):
				print('\t%s/%d.png' % (folder, number))
		print()

if __name__ == '__main__':
	free()
