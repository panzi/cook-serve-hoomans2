# my own very simple CSV dialect
# no quoting, but escaping

import re

PARSE_SYM = re.compile(r'\\([rntv\\,])|,')
ESC_SYM = re.compile(r'[,\n\r\t\v\\]')

def parse_row(line):
	row = []
	cell = []
	index = 0
	length = len(line)
	while index < length:
		match = PARSE_SYM.search(line, index)
		if match:
			cell.append(line[index:match.start()])
			s = match[0]
			if s == ',':
				row.append(''.join(cell))
				cell = []
			else:
				c = match[1]
				if c == 'n':
					cell.append('\n')
				elif c == 'r':
					cell.append('\r')
				elif c == 't':
					cell.append('\t')
				elif c == 'v':
					cell.append('\v')
				elif c == ',' or c == '\\':
					cell.append(c)
				else:
					assert False, "unhandeled escape sequence " + s
			index = match.end()
		else:
			cell.append(line[index:])
			index = length

	row.append(''.join(cell))

	return row

def read(stream):
	for line in stream:
		yield parse_row(line)

def parse(string):
	lines = string.split('\n')
	if lines and not lines[-1]:
		del lines[-1]

	for line in lines:
		yield parse_row(line)

def escape_cell(cell):
	return ESC_SYM.sub(lambda match: '\\' + match[0], str(cell))

def stringify(rows):
	buf = []
	for row in rows:
		buf.append(','.join(escape_cell(cell) for cell in row))
		buf.append('\n')
	return ''.join(buf)

def write(rows, stream):
	for row in rows:
		stream.write(','.join(escape_cell(cell) for cell in row))
		stream.write('\n')