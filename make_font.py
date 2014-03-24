# -*- coding: utf-8 -*-
"""
The format of font.bin: [File Header][Glyphs Table][Glyphs Data]
File Header: 	BF [2 bytes]
				VersionNumber [1 byte]
				FontHeight [ 1 byte]
				FontWidthMinimum [1 byte]
				FontWidthMaximum [1 byte]
				Glyph Count [2 bytes] 
Glyphs Table: 	[ data position[2 bytes], width [1 byte] ] x Glyph Count
Glyphs Data:	(Glyph data) x Actual Glyph count

GlyphDataSize: FontHeight / 8 x FontHeight / 8
"""

import sys, Image, ImageDraw, ImageFont
from optparse import OptionParser
import os
import StringIO

def get_font_info(chars, font):
	img = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
	draw = ImageDraw.Draw(img)

	height_prefer = 0
	width_min = 0xffff
	width_max = 0

	for ch, _, _ in chars:
		width, height = draw.textsize(ch, font=font)
		if height_prefer != height:
			if height_prefer == 0:
				height_prefer = height
			else:
				print('Not all characters are in same size. Quit')
				sys.exit()

		if width < width_min:
			width_min = width
		if width > width_max:
			width_max = width

	return (height_prefer, width_min, width_max)

def get_stride(width):
	return int((width + 7) / 8)

def make_font(glyph_count, chars, is_save_font_image, font, save_fn):
	cache_imgs = {}
	if is_save_font_image:
		if not os.path.exists("font_chars"):
			os.makedirs("font_chars")

	fontData = StringIO.StringIO()
	chr_infos = [[0, 0] for _ in range(glyph_count) ]
	
	(height_prefer, width_min, width_max) = get_font_info(chars, font)
	print('height: %d, width_min: %d, width_max: %d' % (height_prefer, width_min, width_max))

	imageFontSize = Image.new('RGBA', (10, 10), (0, 0, 0, 0))
	drawFontSize = ImageDraw.Draw(imageFontSize)

	for ch, code, pos in chars:
		width, height = drawFontSize.textsize(ch, font=font)
		canvas_qeometry = (width, height)

		chr_infos[code][0] = pos
		chr_infos[code][1] = width

		img = cache_imgs.get(canvas_qeometry)
		if img is None:
			img = Image.new('RGB', canvas_qeometry, (0, 0, 0, 0))

		draw = ImageDraw.Draw(img)
		draw.rectangle((0, 0, width, height), fill=0)
		draw.text((0, 0), ch, font=font, fill='#ffffff')

		dots = []
		data = img.getdata()
		for y in range(height):
			for x in range(0, width, 8):
				pix = 0
				for bit in range(x, x + 8):
					if bit >= width:
						break
					if data[y * width + bit][0] >= 0xff / 2:
						pix |= 1 << (7 - (bit - x))
				fontData.write(chr(pix))
				dots.append('0x%02x' % (pix,))

			# write padding data.
			for _ in range(get_stride(width_max) - get_stride(width)):
				fontData.write('\x00')
				dots.append('0x00')

		if is_save_font_image:
			try:
				with open("font_chars/%d-%x-%s.txt" % (pos, code, ch), "wb") as f:
					f.write(', '.join(dots))
				img.save("font_chars/%d-%x-%s.png" % (pos, code, ch), 'PNG')
			except IOError as e:
				with open("font_chars/%d-%x.txt" % (pos, code), "wb") as f:
					f.write(', '.join(dots))
				pass

	#print('Chars: %d, data_size: %d' % (len(chr_infos), fontData.len))
	with open(save_fn, 'wb') as f:
		f.write('BF')
		f.write(chr(2)) # Version
		f.write(chr(height_prefer))
		f.write(chr(width_min))
		f.write(chr(width_max))
		f.write(chr(glyph_count >> 8) + chr(glyph_count & 0xff))	# glyph count

		# write font header.
		for pos, width in chr_infos:
			if pos > 0xff:
				f.write(chr(pos >> 8) + chr(pos & 0xff))
			else:
				f.write('\x00' + chr(pos & 0xff))

			f.write(chr(width & 0xff))

		f.write(fontData.getvalue())

	print('%d characters. ' % (len(chars),))

def is_in_encoding(s, encoding):
	try:
		s.encode(encoding)
		return True
	except UnicodeEncodeError as e:
		return False
	
def get_glyph_set(code_max, encoding_list):
	chars = []
	for i in range(code_max):
		s = unichr(i)
		for encoding in encoding_list:
			if is_in_encoding(s, encoding):
				chars.append([s, i, len(chars)])
				break

	return chars

class GlyphFont:
	OFFSET_GLYPH_INDEX = 6
	OFFSET_GLYPH_DATA = OFFSET_GLYPH_INDEX + 3 * 0xffff

	def __init__(self):
		with open('font.bin') as f:
			data = f.read()
			if data[0] != 'F' and data[1] != 'F' and ord(data[2]) != 1:
				raise Exception('Incorrect format.')

			self.height = ord(data[3])
			self.width_min = ord(data[4])
			self.width_max = ord(data[5])
			
			self.glyh_size = self.height * get_stride(self.width_max)

			self.glyph_index = []
			for i in range(0xffff):
				offset = GlyphFont.OFFSET_GLYPH_INDEX + i * 3
				self.glyp_index.append((ord(data[offset]) << 8) | ord(data[offset]), ord(data[offset]))
				
			self.glyph_datas = data[GlyphFont.OFFSET_GLYPH_DATA:]

	def print_with_font(self, text):
		img = Image.new('RGBA', (300, self.height), (0, 0, 0, 0))
	
		draw = ImageDraw.Draw(img)

		text = unicode(text)
		for ch in text:
			data_offset = self.glyph_index[ord(ch)]
			
			
		img.save('out.png', 'PNG')

def make_chinese_font(font_size, is_save_font_image):
	#font_file = '/usr/share/fonts/truetype/freefont/FreeSerif.ttf'
	#font_file = '/System/Library/Fonts/STHeiti Light.ttc'
	font_file = r'C:\windows\fonts\simsun.ttc'
	#font_file = r'C:\windows\fonts\simhei.ttf'
	font = ImageFont.truetype(font_file, font_size)

	# Prepare characters
	chars = get_glyph_set(0xffff, ['gb2312', 'big5'])

	make_font(0xffff, chars, is_save_font_image, font, 'cn_font.bin')

def make_barcode_font(font_size, is_save_font_image):
	#font_file = '/usr/share/fonts/truetype/freefont/FreeSerif.ttf'
	#font_file = '/System/Library/Fonts/STHeiti Light.ttc'
	font_file = os.path.join(os.path.dirname(__file__), 'code128.ttf')
	font = ImageFont.truetype(font_file, font_size)

	# Prepare characters
	chars = get_glyph_set(0x7f, ['utf-8'])

	make_font(0x7f, chars, is_save_font_image, font, 'barcode_font.bin')

if __name__ == '__main__':
	'''
	size: 28 height: 32, width_min: 13, width_max: 29
	size: 23 height: 26, width_min: 11, width_max: 24
	'''
	cmd_parser = OptionParser()
	cmd_parser.add_option("-s", "--size", action="store", type="int", dest="font_size")
	cmd_parser.add_option("-c", "--chinese", action="store_true", dest="chinese", default=False,
                  help="Create Chinese font")
	cmd_parser.add_option("-b", "--barcode", action="store_true", dest="barcode", default=False,
                  help="Create Barcode font")
	cmd_parser.add_option("-v", "--save_glyph_image", action="store_true", dest="save_glyph_image", default=False,
                  help="Save individual glyph to files.")
	(options, args) = cmd_parser.parse_args()

	font_size = getattr(options, 'font_size')
	chinese = getattr(options, 'chinese')
	barcode = getattr(options, 'barcode')
	save_glyph_image = getattr(options, 'save_glyph_image')
	if not font_size or (not chinese and not barcode):
		cmd_parser.print_help()
		sys.exit()

	if chinese:
		make_chinese_font(font_size, save_glyph_image)

	if barcode:
		make_barcode_font(font_size, save_glyph_image)
