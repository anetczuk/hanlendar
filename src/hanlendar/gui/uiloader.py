# MIT License
#
# Copyright (c) 2020 Arkadiusz Netczuk <dev.arnet@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#


import os

import logging


try:
    from PyQt5 import uic
except ImportError:
    ### No module named <name>
    logging.exception("Exception while importing")
    exit(1)


base_dir = os.path.dirname( __file__ )
MAIN_MODULE_DIR = os.path.abspath( os.path.join( base_dir, ".." ) )


def generate_ui_file_name(classFileName):
    commonPrefix = os.path.commonprefix( [classFileName, base_dir] )
    relativePath = os.path.relpath(classFileName, commonPrefix)
    nameTuple = os.path.splitext(relativePath)
    return nameTuple[0] + ".ui"


def load_ui(uiFilename):
    try:
        ui_path = os.path.join( MAIN_MODULE_DIR, "ui", uiFilename )
        return uic.loadUiType( ui_path )
    except Exception as e:
        print("Exception while loading UI file:", uiFilename, e)
        raise


def load_ui_from_class_name(uiFilename):
    ui_file = generate_ui_file_name(uiFilename)
    return load_ui( ui_file )


def printsyspath():
    import sys
    for p in sys.path:
        print( "path:", p )
