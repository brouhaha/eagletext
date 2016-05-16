#!/usr/bin/env python3

# Rasterize text using cairocffi
# Copyright 2016 Eric Smith <spacewar@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the version 3 of the GNU General Public License
# as published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import array
import cairocffi



class RasterRowIterator:
    def __init__(self, surface, y):
        self.bits_per_pixel = { cairocffi.FORMAT_ARGB32:    32,
                                cairocffi.FORMAT_RGB24:     32,
                                cairocffi.FORMAT_A8:        8,
                                cairocffi.FORMAT_A1:        1,
                                cairocffi.FORMAT_RGB16_565: 16,
                                cairocffi.FORMAT_RGB30:     32 }[surface.get_format()]
        self.row_base = y * surface.get_stride()
        self.data = surface.get_data()
        self.width = surface.get_width()
        self.y = y
        self.x = 0
        self.x1 = None

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def get_pixel(self, x):
        if self.bits_per_pixel >= 8:
            b = self.bits_per_pixel // 8
            i = self.row_base + x * b
            return self.data[i:i+b]
        elif self.bits_per_pixel == 1:
            i = self.row_base + x // 8
            return (self.data[i] >> (x % 8)) & 1

    def next(self):
        if self.x >= self.width:
            raise StopIteration()
        if self.x1 is None:
            self.x1 = self.x
            self.p1 = self.get_pixel(self.x)
        while True:
            self.x += 1
            if self.x >= self.width:
                return (self.x1, self.x, self.p1)
            p = self.get_pixel(self.x)
            if p != self.p1:
                result = (self.x1, self.x, self.p1)
                self.p1 = p
                self.x1 = self.x
                return result

        
class RasterizeText:
    # width, height in pixels
    # default 1x1 pixel for a dummy surface to get text extents before
    # allocating the real surface
    def _setup_context(self, width = 1, height = 1):
        self.surface = cairocffi.ImageSurface(cairocffi.FORMAT_RGB24, width, height)
        self.context = cairocffi.Context(self.surface)
        self.context.scale(self.resolution, self.resolution)
        self.context.set_source_rgb(0, 0, 0) # black
        self.context.paint
        self.context.set_source_rgb(1, 1, 1) # white

        if not self.antialias:
            font_options = self.surface.get_font_options()
            font_options.set_antialias(cairocffi.ANTIALIAS_NONE)
            self.context.set_font_options(font_options)
            
        self.context.select_font_face(self.face, self.slant, self.weight)

        self.context.set_font_size(self.size)

        self.surface_data = self.surface.get_data()
        self.surface_stride = self.surface.get_stride()
    

    def __init__(self,
                 text,        # text to render
                 resolution,  # resolution in dpi
                 face,
                 size,        # size in inches
                 bold, italic, oblique,
                 antialias = False):
        self.text = text
        self.resolution = resolution
        self.face = face
        self.size = size
        if italic:
            self.slant = cairocffi.FONT_SLANT_ITALIC
        elif oblique:
            self.slant = cairocffi.FONT_SLANT_ITALIC
        else:
            self.slant = cairocffi.FONT_SLANT_NORMAL
        if bold:
            self.weight = cairocffi.FONT_WEIGHT_BOLD
        else:
            self.weight = cairocffi.FONT_WEIGHT_NORMAL
        self.antialias = antialias

        self._setup_context(1, 1)
        te = self.context.text_extents(self.text)
        #print(te)
        (self.x_bearing, self.y_bearing, self.width, self.height, x_advance, y_advance) = te

        self.origin = (-self.x_bearing, -self.y_bearing)

        self._setup_context(int(self.width * self.resolution),
                            int(self.height * self.resolution))
        self.context.move_to(self.origin[0], self.origin[1])
        self.context.show_text(self.text)
        self.surface.write_to_png('test.png')

    def get_size_pixels(self):
        return (self.surface.get_width(), self.surface.get_height())

    def get_origin(self):
        return self.origin

    def get_pixel(self, x, y):
        i = (y * self.surface_stride + x) * 4
        return self.surface_data[i:i+4]

    def row_iter(self, y):
        return RasterRowIterator(self.surface, y)
