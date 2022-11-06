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
import io

import abc


_LOGGER = logging.getLogger(__name__)


class RenamingUnpickler(pickle.Unpickler):

    def __init__(self, file, module_mapper=None):
        super().__init__( file )
        self.module_mapper = module_mapper

    def find_class(self, module, name):
        moduleName, itemName = self.findName( module, name )
#         _LOGGER.info( "unpicking module: %s %s %s", module, name, moduleName )
        return super().find_class( moduleName, itemName )
    
    def findName(self, module, name):
        if self.module_mapper is None:
            return (module, name)

        ## find module name
        try:
            return self.module_mapper( module, name )
        except TypeError:
            ## whatever your fall-back plan is when obj doesn't support [] (__getitem__) 
            pass

        ## do nothing
        return (module, name)


## class_mapper -- object mapping class names based on code version
def load_object( inputFile, defaultValue=None, class_mapper=None ):
    _LOGGER.info( "loading data from: %s", inputFile )
    with open( inputFile, 'rb') as fp:
        content = fp.read()
        return load_data( content, defaultValue, class_mapper )


## class_mapper -- object mapping class names based on code version
def load_data( content, defaultValue=None, class_mapper=None ):
    try:
        if class_mapper is None:
            return pickle.loads( content )
        else:
            stream_str = io.BytesIO( content )
            return RenamingUnpickler( stream_str, class_mapper ).load()
    except FileNotFoundError:
        _LOGGER.exception("failed to load")
        return defaultValue
    except Exception:
        _LOGGER.exception("failed to load")
        raise


def store_object( inputObject, outputFile ):
    tmpFile = outputFile + "_tmp"
    with open(tmpFile, 'wb') as fp:
        pickle.dump( inputObject, fp )

    if os.path.isfile( outputFile ) is False:
        ## output file does not exist -- rename file
        _LOGGER.info( "saving data to: %s", outputFile )
        os.rename( tmpFile, outputFile )
        return True

    if filecmp.cmp( tmpFile, outputFile ) is True:
        ## the same files -- remove tmp file
        _LOGGER.info("no new data to store in %s", outputFile)
        os.remove( tmpFile )
        return False

    _LOGGER.info( "saving data to: %s", outputFile )
    os.remove( outputFile )
    os.rename( tmpFile, outputFile )
    return True


def backup_files( inputFiles, outputArchive ):
    ## create zip
    tmpZipFile = outputArchive + "_tmp"
    zipf = zipfile.ZipFile( tmpZipFile, 'w', zipfile.ZIP_DEFLATED )
    for file in inputFiles:
        zipEntry = os.path.basename( file )
        zipf.write( file, zipEntry )
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


def load_backup( outputArchive ):
    input_zip = zipfile.ZipFile( outputArchive )
    return { name: input_zip.read(name) for name in input_zip.namelist() }


##
class Versionable( metaclass=abc.ABCMeta ):

    def __getstate__(self):
        if not hasattr(self, "_class_version"):
            raise Exception("Your class must define _class_version class variable")
        # pylint: disable=E1101
        return dict(_class_version=self._class_version, **self.__dict__)

    def __setstate__(self, dict_):
        version_present_in_pickle = dict_.pop("_class_version", None)
        # pylint: disable=E1101
        if version_present_in_pickle == self._class_version:
            # pylint: disable=W0201
            self.__dict__ = dict_
        else:
            self._convertstate_( dict_, version_present_in_pickle )

    @abc.abstractmethod
    def _convertstate_(self, dict_, dictVersion_ ):
        raise NotImplementedError('You need to define this method in derived class!')
