#!/usr/bin/env python3

import os
import re
import sys
import csv
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
from os.path import splitext, isdir, join as pjoin, abspath, dirname
from time import time
from contextlib import contextmanager
from game_maker import *

MAX_FILLER_COUNT = 4
HOOMAN_SPRITES = {'CUST_SPR_POOR', 'CUST_SPR_COMMON', 'CUST_SPR_RICH'}
HOOMAN_NAMES = {}

@contextmanager
def timing(name, inline=True):
	if inline:
		print(name + "...", end="")
	else:
		print(name + "...")
	start = time()
	try:
		yield
	finally:
		end = time()
		if inline:
			print(" %.1f sec" % (end - start))
		else:
			print("%s %.1f sec" % (name, end - start))

def load_names():
	with open(pjoin(dirname(abspath(__file__)), '..', 'hoomans.csv'), 'r') as fp:
		for row in csv.reader(fp):
			hname = row[0].strip()
			hpath = row[1].strip()
			y = None
			if len(row) > 2:
				y = row[2].strip()
				if y:
					y = int(y, 10)
			HOOMAN_NAMES[hpath] = (hname, y)

load_names()

def find_font(*fontfiles):
	fontdirs = [
		pjoin(os.getenv("HOME"), '.fonts'),
		'/usr/share/fonts'
	]
	for fontfile in fontfiles:
		fontfile_lower = fontfile.lower()
		for fontdir in fontdirs:
			for dirpath, dirnames, filenames in os.walk(fontdir):
				for filename in filenames:
					if fontfile_lower == filename.lower():
						return pjoin(dirpath, filename)
	raise KeyError('font not found: ' + ', '.join(fontfiles))

SPLIT = re.compile(r'[-_\s+]')
BORDER = re.compile(r'([a-zäöüß])([A-Z0-9ÄÖÜ])')

def _wrap_text_reformat(text, width, font):
	words = SPLIT.split(BORDER.sub(r'\1 \2', text))
	lines = []
	line = []
	word_index = 0
	while word_index < len(words):
		word = words[word_index]
		line.append(word)
		size = font.getsize(' '.join(line))[0]
		if size > width:
			del line[-1]
			if line:
				lines.append(' '.join(line))
				line = []
			else:
				start = 0
				end = 0
				while start < len(word):
					for index in range(start + 1, len(word) + 1):
						if font.getsize(word[start:index])[0] > width:
							break
						end = index
					if start == end:
						end += 1 # at least one codepoint
					lines.append(word[start:end])
					start = end
				word_index += 1
		else:
			word_index += 1
	if line:
		lines.append(' '.join(line))
	return lines

def wrap_text(text, width, font):
	text = text.strip("-_\n\r\t ")
	words = SPLIT.split(text)
	lines = []
	line = []
	word_index = 0
	while word_index < len(words):
		word = words[word_index]
		line.append(word)
		size = font.getsize(' '.join(line))[0]
		if size > width:
			del line[-1]
			if line:
				lines.append(' '.join(line))
				line = []
			else:
				return _wrap_text_reformat(text, width, font)
		else:
			word_index += 1
	if line:
		lines.append(' '.join(line))
	return lines

def draw_lines(draw, lines, font, color, x, y, width, height, line_spacing):
	for line in lines:
		line_width, line_height = font.getsize(line)
		if y + line_height >= height:
			break
		line_x = x + (width - line_width) // 2
		draw.text((line_x, y), line, color, font)
		y += line_height + line_spacing

def escape_c_byte(c):
	if c == 34:
		return b'\\"'
	elif c == 92:
		return b'\\\\'
	elif c == 10:
		return b'\\n'
	elif c == 13:
		return b'\\r'
	elif c == 9:
		return b'\\t'
	elif c >= 0x20 and c <= 0x7e:
		buf = bytearray(1)
		buf[0] = c
		return buf
	else:
		return ('\\x%02x' % c).encode()

def escape_c_string(s):
	return b''.join(escape_c_byte(c) for c in s.encode()).decode()

def build_sprites(fp, spritedir, builddir):
	font = ImageFont.truetype(find_font('OpenSans_Bold.ttf', 'OpenSans_Regular.ttf', 'Arial.ttf'), 26)
	blur = ImageFilter.GaussianBlur(2)
	patch_def = []
	patch_data_externs = []

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

	replacement_sprites = {}
	for sprite_name in os.listdir(spritedir):
		subpath = pjoin(spritedir, sprite_name)
		if isdir(subpath):
			for filename in os.listdir(subpath):
				tpag_index, ext = splitext(filename)
				if ext.lower() == '.png':
					try:
						tpag_index = int(tpag_index, 10)
					except ValueError:
						pass
					else:
						sprite = Image.open(pjoin(subpath, filename))
						sprite_key = sprite_name, tpag_index

						hpath = '%s/%d.png' % sprite_key
						hooman = HOOMAN_NAMES.get(hpath)
						if hooman:
							width, height = sprite.size
							hname, text_y = hooman
							avail_width = width - 4
							tmp_img = Image.new('RGBA', sprite.size)
							draw = ImageDraw.Draw(tmp_img)
							lines = wrap_text(hname, avail_width, font)

							text_x = 0
							if text_y is None:
								text_y = int(height * 0.5)

							draw_lines(draw, lines, font, '#000000', text_x, text_y, width, height, 0)
							tmp_img = tmp_img.filter(blur)
							draw = ImageDraw.Draw(tmp_img)
							draw_lines(draw, lines, font, '#ffffff', text_x, text_y, width, height, 0)

							sprite = Image.alpha_composite(sprite, tmp_img)

						replacement_sprites[sprite_key] = sprite

	taller_filler_count = 0
	no_filler_count = 0
	filler_stats = {}
	filler_replacement_sprites = list(item for item in replacement_sprites.items() if item[0][0] in HOOMAN_SPRITES)
	filler_replacement_sprites.sort(reverse=True, key=lambda item: item[1].size)
	sprites_by_txtr = {}
	replacement_sprites_by_txtr = {}
	replacement_txtrs = {}
	seen_sprt = False
	strtbl = {}
	with timing("read game archive", inline=False):
		while fp.tell() < end_offset:
			head = fp.read(8)
			magic, size = struct.unpack("<4sI", head)
			next_offset = fp.tell() + size

			if magic == b'SPRT':
				seen_sprt = True
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
					if strptr in strtbl:
						sprite_name = strtbl[strptr]
					else:
						fp.seek(strptr - 4, 0)
						strlen, = struct.unpack('<I', fp.read(4))
						sprite_name = fp.read(strlen).decode()
						strtbl[strptr] = sprite_name

					is_required = sprite_name in HOOMAN_SPRITES

					for tpag_index, tpag_offset in enumerate(tpag_offsets):
						sprite_key = (sprite_name, tpag_index)

						fp.seek(tpag_offset, 0)
						data = fp.read(22)
						tpag = struct.unpack('<HHHHHHHHHHH', data)

						txtr_index = tpag[-1]
						rect = tpag[:4]

						sprite_info = (sprite_name, tpag_index, txtr_index, rect)

						if txtr_index in sprites_by_txtr:
							sprites_by_txtr[txtr_index].append(sprite_info)
						else:
							sprites_by_txtr[txtr_index] = [sprite_info]

						has_sprite = sprite_key in replacement_sprites

						if is_required and not has_sprite:
							width  = rect[2]
							height = rect[3]
							found  = False
							for other_key, other_sprite in filler_replacement_sprites:
								ow = other_sprite.size[0]
								if ow <= width:
									filler_count = filler_stats.get(other_key, 0)
									if filler_count < MAX_FILLER_COUNT:
										filler_stats[other_key] = filler_count + 1
										found = True
										filler_replacement_sprites.sort(key=lambda item: (filler_stats.get(item[0], 0), -item[1].size[0], item[1].size[1]))
										break

							if found:
								sprite_size = (width, height)
								if other_sprite.size != sprite_size:
									owidth, oheight = other_sprite.size
									tmp_img = Image.new(other_sprite.mode, sprite_size)
									x = (width - owidth) // 2
									if oheight > height:
										taller_filler_count += 1
										tmp2_img = other_sprite.crop((0, 0, owidth, height))
										tmp_img.paste(tmp2_img, (x, 0, x + owidth, height))
									else:
										y = height - oheight
										tmp_img.paste(other_sprite, (x, y, x + owidth, y + oheight))
									other_sprite = tmp_img
								replacement_sprites[sprite_key] = other_sprite
								has_sprite = True
								print("Using %s/%d.png as %s/%d.png" % (other_key + sprite_key))
							else:
								print("*** Could not find replacement sprite for %s/%d.png" % sprite_key)
								no_filler_count += 1

						if has_sprite:
							if txtr_index in replacement_sprites_by_txtr:
								replacement_sprites_by_txtr[txtr_index].append(sprite_info)
							else:
								replacement_sprites_by_txtr[txtr_index] = [sprite_info]

				if filler_stats:
					filler_stats = list((count, key) for key, count in filler_stats.items())
					filler_stats.sort()
					print('Filler usage:')
					sum_count = 0
					for count, (sprite_name, tpag_index) in filler_stats:
						sprite_path = '%s/%d.png' % (sprite_name, tpag_index)
						hooman = HOOMAN_NAMES.get(sprite_path)
						hname = hooman[0] if hooman else ''
						print('%5d %-25s %s' % (count, hname, sprite_path))
						sum_count += count
					print("That makes %d filler sprites." % sum_count)

				if taller_filler_count > 0:
					print("%d time(s) a filler that is taller than the available slot was used." % taller_filler_count)

				if no_filler_count > 0:
					print("Couldn't find fillers for %d sprite(s)." % no_filler_count)

			elif magic == b'TXTR':
				if not seen_sprt:
					raise FileFormatError("found TXTR block before found SPRT block")

				start_offset = fp.tell()
				count, = struct.unpack("<I", fp.read(4))
				data = fp.read(4 * count)
				info_offsets = struct.unpack("<%dI" % count, data)
				file_infos = []

				for offset in info_offsets:
					if offset < start_offset or offset + 8 > end_offset:
						raise FileFormatError("illegal TXTR info offset: %d" % offset)

					fp.seek(offset, 0)
					data = fp.read(12)
					info = struct.unpack("<III", data)
					file_infos.append(info)

				seen_sprites = set()
				for txtr_index, (unknown1, unknown2, offset) in enumerate(file_infos):
					if offset < start_offset or offset > end_offset:
						raise FileFormatError("illegal TXTR data offset: %d" % offset)

					fp.seek(offset, 0)
					info = parse_png_info(fp)

					if offset + info.filesize > end_offset:
						raise FileFormatError("PNG file at offset %d overflows TXTR data section end" % offset)

					if txtr_index in replacement_sprites_by_txtr:
						print("generate TXTR %d" % txtr_index)
						sprites = replacement_sprites_by_txtr[txtr_index]
						fp.seek(offset, 0)
						data = fp.read(info.filesize)

						image = Image.open(BytesIO(data))

						for sprite_name, tpag_index, txtr_index, (x, y, width, height) in sprites:
							sprite_key = (sprite_name, tpag_index)
							if sprite_key in seen_sprites:
								raise FileFormatError("Sprite double occurence: %s %d" % sprite_key)

							seen_sprites.add(sprite_key)

							sprite = replacement_sprites[sprite_key]
							if sprite.size != (width, height):
								raise FileFormatError("Sprite %s %d has incompatible size. PNG size: %d x %d, size in game archive: %d x %d" %
									(sprite_name, tpag_index, sprite.size[0], sprite.size[1], width, height))

							image.paste(sprite, (x, y, x + width, y + height))

						# DEBUG:
						#image.save(pjoin(builddir, '%05d.png' % txtr_index))

						buf = BytesIO()
						image.save(buf, format='PNG')
						replacement_txtrs[txtr_index] = (image.size, buf.getvalue())

			fp.seek(next_offset, 0)

	with timing("check sprites"):
		check_sprites = {}
		for txtr_index in replacement_txtrs:
			for sprite_info in sprites_by_txtr[txtr_index]:
				sprite_name = sprite_info[0]
				if sprite_name in check_sprites:
					check_sprites[sprite_name].append(sprite_info)
				else:
					check_sprites[sprite_name] = [sprite_info]

	with timing("generate patch entries"):
		# check all coordinates of sprites in replaced textures
		non_ident = re.compile('[^_a-z0-9]', re.I)
		sprt_defs = []
		for sprite_name in sorted(check_sprites):
			ident = non_ident.sub('_', sprite_name)
			tpags = check_sprites[sprite_name]
			tpags.sort(key=lambda sprite_info: sprite_info[1])
			tpag_defs = []

			for _, tpag_index, txtr_index, (x, y, width, height) in tpags:
				tpag_defs.append('{%d, %d, %d, %d, %d, %d}' % (tpag_index, x, y, width, height, txtr_index))

			sprt_defs.append("""
static struct gm_patch_sprt_entry csh2_sprt_%s[] = {
	%s
};
""" % (ident, ',\n\t'.join(tpag_defs)))

			patch_def.append('GM_PATCH_SPRT("%s", csh2_sprt_%s, %d)' % (
				escape_c_string(sprite_name), ident, len(tpag_defs)))

	with timing("generate patch data", inline=False):
		for txtr_index in sorted(replacement_txtrs):
			((width, height), data) = replacement_txtrs[txtr_index]

			patch_data_externs.append('extern const uint8_t csh2_%05d_data[];' % txtr_index)
			patch_def.append("GM_PATCH_TXTR(%d, csh2_%05d_data, %d, %d, %d)" % (txtr_index, txtr_index, len(data), width, height))
			data_filename = 'csh2_%05d_data.c' % txtr_index

			hex_data = ',\n\t'.join(', '.join('0x%02x' % byte for byte in data[i:i + 8]) for i in range(0, len(data), 8))

			data_c = """\
#include <stdint.h>

const uint8_t csh2_%05d_data[] = {
	%s
};
""" % (txtr_index, hex_data)

			out_filename = pjoin(builddir, data_filename)

			# speed up compilation by only re-generating C files with changes
			try:
				with open(out_filename, 'r') as outfp:
					old_data_c = outfp.read()
			except FileNotFoundError:
				write_file = True
			else:
				write_file = old_data_c != data_c

			if write_file:
				print(out_filename)
				with open(out_filename, 'w') as outfp:
					outfp.write(data_c)

	with timing("generate patch definition", inline=False):
		patch_def_h = """\
#ifndef CSH2_PATCH_DEF_H
#define CSH2_PATCH_DEF_H
#pragma once

#include <stdint.h>
#include "game_maker.h"

#ifdef __cplusplus
extern "C" {
#endif

%s
extern const struct gm_patch csh2_patches[];

#ifdef __cplusplus
}
#endif

#endif
""" % '\n'.join(patch_data_externs)

		out_filename = pjoin(builddir, 'csh2_patch_def.h')
		print(out_filename)
		with open(out_filename, 'w') as outfp:
			outfp.write(patch_def_h)

		patch_def_c = """\
#include "csh2_patch_def.h"
%s
const struct gm_patch csh2_patches[] = {
	%s,
	GM_PATCH_END
};
""" % (''.join(sprt_defs), ',\n\t'.join(patch_def))

		out_filename = pjoin(builddir, 'csh2_patch_def.c')
		print(out_filename)
		with open(out_filename, 'w') as outfp:
			outfp.write(patch_def_c)

if __name__ == '__main__':
	spritedir = sys.argv[1]
	builddir  = sys.argv[2]

	if len(sys.argv) > 3:
		archive = sys.argv[3]
	else:
		archive = find_archive()

	with open(archive, 'rb') as fp:
		build_sprites(fp, spritedir, builddir)
