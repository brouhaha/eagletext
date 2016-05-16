#!/usr/bin/env python3

# Rasterize text into a new Eagle CAD library file
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

import argparse
import sys

from Eagle import EagleLibraryFile, EaglePackage, EagleDeviceset, EagleDevice, EagleRectangle
from Rasterize import RasterizeText


# I would like to be able to say things like
#   ./eagletext.py --size 0.2 "hello" --size 0.3 --italic "blah" -o foo.lbr
# and have the options affect the next "positional" argument. This seems to be
# tricky to do with argparse.
#   http://stackoverflow.com/questions/11276501/can-argparse-associate-positional-arguments-with-named-arguments

# I tried using a custom Action for the "positional" arguments. It works for:
#   ./eagletext.py "foo" "bar" -s 3.0
# or
#   ./eagletext.py -s 2.0 "foo" "bar"
# but fails for
#   ./eagletext.py -s 2.0 "foo" -s 3.0 "bar"
# The action function does not even get called for the second instance of the "same"
# positional argument.



class StrActionStoreOptions(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super().__init__(option_strings, dest, **kwargs)
    def __call__(self, parser, namespace, values, option_string=None):
        print('%r %r %r' % (namespace, values, option_string))
        setattr(namespace, self.dest, values)

parser = argparse.ArgumentParser(description='Rasterized text library generator for Eagle CAD',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("text",               help="string to rasterize", type = str, nargs='+')
parser.add_argument("-o", "--output",     help="new Eagle library file", type=argparse.FileType('wb'), default = sys.stdout)
parser.add_argument("-l", "--layer",      help = "layer number", type = int, default = 21)
parser.add_argument("-r", "--resolution", help = "resolution in dpi", type = int, default = 600)
#parser.add_argument("-n", "--name",       help = "device/package name", type = str)
parser.add_argument("-f", "--font",       help = "font face", type = str, default = 'sans')
parser.add_argument("-b", "--bold",       help = "bold", action = 'store_true')
parser.add_argument("--halign",           help = "horizontal alignment", choices = ['left', 'right', 'center'], default = 'left')
parser.add_argument("--valign",           help = "vertical alignment", choices = ['top', 'bottom', 'baseline', 'center'], default = 'bottom')
parser.add_argument("--overlap",          help = "overlap percentage", type = float, default = 10.0)

slant_group = parser.add_mutually_exclusive_group()
slant_group.add_argument("-i", "--italic",     help = "italic", action = 'store_true')
slant_group.add_argument("--oblique",          help = "italic", action = 'store_true')

parser.add_argument("-s", "--size",       help = "font size in inches (float)", type = float, default = 0.2)


args = parser.parse_args()
#print(args)

layer = args.layer


lib = EagleLibraryFile()

for text in args.text:
    #if args.name is None:
    #    args.name = args.text.upper().replace(' ', '_')
    name = text.upper().replace(' ', '_')

    package_name = name
    deviceset_name = name

    raster = RasterizeText(text, args.resolution, args.font, args.size, args.bold, args.italic, args.oblique)

    width_pixels, height_pixels = raster.get_size_pixels()
    x_origin, y_origin = raster.get_origin()

    package = EaglePackage(package_name)

    overlap = args.overlap/(200 * args.resolution)

    yoffset = 0
    if args.valign == 'top':
        yoffset = height_pixels/args.resolution
    elif args.valign == 'bottom':
        pass
    elif args.valign == 'baseline':
        yoffset = height_pixels/args.resolution - y_origin
    elif args.valign == 'center':
        yoffset = height_pixels/(2*args.resolution)
    #elif args.valign == 'center-above-baseline':
    #    yoffset = ?

    xoffset = 0
    if args.halign == 'left':
        pass
    elif args.halign == 'right':
        xoffset = width_pixels/args.resolution
    elif args.halign == 'center':
        xoffset = width_pixels/(2*args.resolution)

    for y in range(height_pixels):
        #print("row %d" % y)
        y1 = y / args.resolution - overlap - yoffset
        y2 = (y + 1) / args.resolution + overlap - yoffset
        ri = raster.row_iter(height_pixels - 1 - y)
        for x1p, x2p, p in ri:
            #print(x1p, x2p, ['%d' % p[i] for i in range(len(p))])
            x1 = x1p / args.resolution - xoffset
            x2 = x2p / args.resolution - xoffset
            if p[0] != 0:
                package.add_primitive(EagleRectangle(layer,
                                                     x1 * 25.4, y1 * 25.4,
                                                     x2 * 25.4, y2 * 25.4))

    lib.add_package(package)

    deviceset = EagleDeviceset(deviceset_name)
    device = EagleDevice('', package_name)
    deviceset.add_device(device)
    
    lib.add_deviceset(deviceset)

lib.write(args.output)
