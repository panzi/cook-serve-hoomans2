#!/usr/bin/env python3

import os
import struct
import collections
from PIL import Image
from io import BytesIO
from os.path import join as pjoin
from game_maker import *

def dump_sprites(fp, outdir):
	fp.seek(0, 2)
	file_size = fp.tell()
	fp.seek(0, 0)

	head = fp.read(8)
	magic, size = struct.unpack("<4sI", head)
	if magic != b'FORM':
		raise ValueError("illegal file magic: %r" % magic)

	expected = size + 8
	if expected < file_size:
		raise ValueError("file size underflow: file size = %d, read size = %d" % (
			file_size, expected))

	elif expected > file_size:
		raise ValueError("file size overflow: file size = %d, read size = %d" % (
			file_size, expected))

	end_offset = fp.tell() + size
	txtrs = []
	sprts = {}
	while fp.tell() < end_offset:
		head = fp.read(8)
		magic, size = struct.unpack("<4sI", head)
		next_offset = fp.tell() + size

		if magic == b'SPRT':
			sprite_count, = struct.unpack("<I", fp.read(4))
			data = fp.read(4 * sprite_count)
			sprite_offsets = struct.unpack("<%dI" % sprite_count, data)

			for offset in sprite_offsets:
				fp.seek(offset, 0)
				data = fp.read(4 * 20)
				sprite_record = struct.unpack('<20I', data)

				tpag_count = sprite_record[-1]
				data = fp.read(4 * tpag_count)
				tpag_offsets = struct.unpack('<%dI' % tpag_count, data)

				strptr = sprite_record[0]
				fp.seek(strptr - 4, 0)
				strlen, = struct.unpack('<I', fp.read(4))
				sprite_name = fp.read(strlen).decode()

				for tpag_index, tpag_offset in enumerate(tpag_offsets):
					fp.seek(tpag_offset, 0)
					data = fp.read(22)
					tpag = struct.unpack('<HHHHHHHHHHH', data)

					# TODO: find out what all the fields mean
					txtr_index = tpag[-1]
					rect = tpag[:4]

					sprite_info = (sprite_name, tpag_index, rect)

					if txtr_index in sprts:
						sprts[txtr_index].append(sprite_info)
					else:
						sprts[txtr_index] = [sprite_info]

		elif magic == b'TXTR':
			start_offset = fp.tell()
			count, = struct.unpack("<I", fp.read(4))
			data = fp.read(4 * count)
			info_offsets = struct.unpack("<%dI" % count, data)
			file_infos = []

			for offset in info_offsets:
				if offset < start_offset or offset + 12 > end_offset:
					raise FileFormatError("illegal TXTR info offset: %d" % offset)

				fp.seek(offset, 0)
				data = fp.read(12)
				info = struct.unpack("<III", data)
				file_infos.append(info)

			seen_sprites = set()
			for index, (unknown1, unknown2, offset) in enumerate(file_infos):
				if offset < start_offset or offset > end_offset:
					raise FileFormatError("illegal TXTR data offset: %d" % offset)

				fp.seek(offset, 0)
				info = parse_png_info(fp)

				if offset + info.filesize > end_offset:
					raise FileFormatError("PNG file at offset %d overflows TXTR data section end" % offset)

				if index in sprts:
					sprites = sprts[index]
					fp.seek(offset, 0)
					data = fp.read(info.filesize)

					image = Image.open(BytesIO(data))

					txtr_filename = pjoin(outdir, '%05d.png' % index)
					print(txtr_filename)
					with open(txtr_filename, 'wb') as outfp:
						outfp.write(data)

					for sprite_name, tpag_index, rect in sprites:
						sprite_key = (sprite_name, tpag_index)
						if sprite_key in seen_sprites:
							raise FileFormatError("Sprite double occurence: %s %d" % sprite_key)

						seen_sprites.add(sprite_key)

						sprite_dir = pjoin(outdir, sprite_name)
						os.makedirs(sprite_dir, exist_ok=True)

						sprite_filename = pjoin(sprite_dir, '%d.png' % tpag_index)
						print(sprite_filename)

						x, y, width, height = rect
						box = (x, y, x + width, y + height)
						sprite = image.crop(box)
						sprite.save(sprite_filename)

		fp.seek(next_offset, 0)

if __name__ == '__main__':
	import sys

	if len(sys.argv) > 1:
		outdir = sys.argv[1]
	else:
		outdir = os.path.realpath(pjoin(os.path.dirname(os.path.abspath(__file__)), '..', 'dump'))

	if len(sys.argv) > 2:
		archive = sys.argv[2]
	else:
		archive = find_archive()

	with open(archive, 'rb') as fp:
		dump_sprites(fp, outdir)
