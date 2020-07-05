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

import logging

import os
import zipfile
import filecmp
import pickle


_LOGGER = logging.getLogger(__name__)


def loadObject( inputFile, defaultValue=None ):
    try:
        _LOGGER.info( "loading data from: %s", inputFile )
        with open( inputFile, 'rb') as fp:
            return pickle.load(fp)
    except FileNotFoundError:
        _LOGGER.exception("failed to load")
        return defaultValue
    except Exception:
        _LOGGER.exception("failed to load")
        raise


def storeObject( inputObject, outputFile ):
    tmpFile = outputFile + "_tmp"
    with open(tmpFile, 'wb') as fp:
        pickle.dump( inputObject, fp )

    if os.path.isfile( outputFile ) is False:
        ## output file does not exist -- rename file
        os.rename( tmpFile, outputFile )
        return

    if filecmp.cmp( tmpFile, outputFile ) is True:
        ## the same files -- remove tmp file
        _LOGGER.info("no new data to store in %s", outputFile)
        os.remove( tmpFile )
        return

    os.remove( outputFile )
    os.rename( tmpFile, outputFile )


def backupFiles( inputFiles, outputArchive ):
    ## create zip
    tmpZipFile = outputArchive + "_tmp"
    zipf = zipfile.ZipFile( tmpZipFile, 'w', zipfile.ZIP_STORED )
    for file in inputFiles:
        zipf.write( file )
    zipf.close()

    ## compare content
    storedZipFile = outputArchive
    if os.path.isfile( storedZipFile ) is False:
        ## output file does not exist -- rename file
        _LOGGER.info( "storing data to: %s", storedZipFile )
        os.rename( tmpZipFile, storedZipFile )
        return

    if filecmp.cmp( tmpZipFile, storedZipFile ) is True:
        ## the same files -- remove tmp file
        _LOGGER.info("no new data to backup")
        os.remove( tmpZipFile )
        return

    ## rename files
    counter = 1
    nextFile = "%s.%s" % (storedZipFile, counter)
    while os.path.isfile( nextFile ):
        counter += 1
        nextFile = "%s.%s" % (storedZipFile, counter)
    _LOGGER.info( "found backup slot: %s", nextFile )

    currFile = storedZipFile
    while counter > 1:
        currFile = "%s.%s" % (storedZipFile, counter - 1)
        os.rename( currFile, nextFile )
        nextFile = currFile
        counter -= 1

    os.rename( storedZipFile, nextFile )
    os.rename( tmpZipFile, storedZipFile )
