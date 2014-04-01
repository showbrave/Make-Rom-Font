Make-Rom-Font
=============

Create binary ROM font data for Chinese or other languages.

此词库被应用于微信点餐系统的打印机中。
http://blog.csdn.net/xhy/article/details/22719853

生成的字库优点
------------

可以完全自定义创建自己的字库：
* 可自由选择任何字体，宋体，楷体，黑体……
* 可自定义字体的大小
* 可自定义需要的字符编码（简体gb2312，gb18030，繁体，韩文，日文……）
* UNICODE支持
* 价格便宜，买 Flash ROM，自己写进 Flash ROM就可以了。

创建字体库需要的软件
----------------

Windows系统，安装 Python 2.7 和 PIL 库（ Python Image Library），下载 Make ROM Font 工具
打开 Windows 命令行，进入取下的代码目录，执行: c:\Python27\python.exe make_font.py -s 23 -c
会在当前目录下产生 cn_font.bin 文件，将此文件烧录到 Flash ROM 中，安装下面的字库格式即可读取。
* 如果要选择不同的字体，修改 make_chinese_font 中 font_file 指向对应的字体文件；
* 如果要选择不同的字符编码，修改 make_chinese_font 中 get_glyph_set，添加新的编码；

字库格式
-------

	The format of font.bin: [File Header][Glyphs Table][Glyphs Data]
	File Header: 	BF [2 bytes]
					VersionNumber [1 byte]
					FontHeight [ 1 byte]
					FontWidthMinimum [1 byte]
					FontWidthMaximum [1 byte]
					Glyph Count [2 bytes] 
	Glyphs Table: 	[ data position[2 bytes], width [1 byte] ] x Glyph Count
	Glyphs Data:	(Glyph data) x Actual Glyph count

	GlyphDataSize: (FontWidthMaximum + 7) / 8 x FontHeight / 8

字库使用
-------

### 初始化字体

	/**
	 * The font info.
	 */
	struct FontInfo
	{
		u32			offset;
		u8			height;
		u8			width_min;
		u8			width_stride;
		u8			glyph_data_size;
		u16			glyph_count;
	};

	typedef unsigned short WCHAR;

	int init_font(struct FontInfo *fontInfo)
	{
		u32 offset = fontInfo->offset;


		// Not font format
		if (FLASH_read_byte(offset + 0) != 'B' && FLASH_read_byte(offset + 1) != 'F')
			return 0;


		// Invalid font lib version.
		if (FLASH_read_byte(offset + FL_OFFSET_VERSION) != FONT_LIB_VERSION)
			return 0;
		fontInfo->height = FLASH_read_byte(offset + FL_OFFSET_HEIGHT);
		fontInfo->width_min = FLASH_read_byte(offset + FL_OFFSET_WIDTH_MIN);
		u8 width_max = FLASH_read_byte(offset + FL_OFFSET_WIDTH_MAX);
		fontInfo->width_stride = get_glyph_stride(width_max);
		fontInfo->glyph_data_size = (((width_max + 7) / 8) * fontInfo->height); //(fontInfo->width_stride + 7) / 8;
		fontInfo->glyph_count = FLASH_read_u16(offset + FL_OFFSET_GLYPH_COUNT);


		return 1;
	}

### 寻址读字体

在单片机程序中，通过下面的方式寻址读字体：

	/**
	 * Get the glyph by its UCS2 character encoding.
	 *
	 * If it does not exist, return a special glyph.
	 */
	void get_glyph(WCHAR ch, struct Glyph *glyph)
	{
		u32 pos = FL_OFFSET_GLYPH_TABLE + FONT_GLYPH_INFO_SIZE * (u32) ch;
		u16 posHigh = FLASH_read_byte(pos);
		u16 posLow = FLASH_read_byte(pos + 1);
		glyph->width = FLASH_read_byte(pos + 2);
		glyph->data_pos = (posHigh << 8) | posLow;
	}

	void get_glyph_data(struct FontInfo *fontInfo, struct Glyph *glyph, u8 offset, u8 data[MAX_GLYPH_STRIDE])
	{
		u32 FL_OFFSET_GLYPH_DATA = fontInfo->offset + FL_OFFSET_GLYPH_TABLE
				+ fontInfo->glyph_count * (u32) FONT_GLYPH_INFO_SIZE;
		u32 addr = FL_OFFSET_GLYPH_DATA + (u32) (glyph->data_pos) * fontInfo->glyph_data_size + offset;
		FLASH_fast_read(data, addr, get_glyph_stride(glyph->width));
	}

