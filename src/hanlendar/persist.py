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
from typing import Any

import os
import io
import zipfile
import filecmp
import pickle


_LOGGER = logging.getLogger(__name__)


class RenamingUnpickler(pickle.Unpickler):

    def __init__(self, file, module_mapper=None):
        super().__init__(file)
        self.module_mapper = module_mapper

    def find_class(self, module, name):
        moduleName, itemName = self.find_name(module, name)
        #         _LOGGER.info( "unpicking module: %s %s %s", module, name, moduleName )
        return super().find_class(moduleName, itemName)

    def find_name(self, module, name):
        if self.module_mapper is None:
            return (module, name)

        ## find module name
        try:
            return self.module_mapper(module, name)
        except TypeError:
            ## whatever your fall-back plan is when obj doesn't support [] (__getitem__)
            pass

        ## do nothing
        return (module, name)


## class_mapper -- object mapping class names based on code version
def load_object(inputFile, defaultValue=None, class_mapper=None):
    _LOGGER.info("loading data from: %s", inputFile)
    with open(inputFile, "rb") as fp:
        content = fp.read()
        return load_data(content, defaultValue, class_mapper)


## class_mapper -- object mapping class names based on code version
def load_data(content, defaultValue=None, class_mapper=None):
    try:
        if class_mapper is None:
            # ruff: noqa: S301
            return pickle.loads(content)
        stream_str = io.BytesIO(content)
        return RenamingUnpickler(stream_str, class_mapper).load()
    except FileNotFoundError:
        _LOGGER.exception("failed to load")
        return defaultValue
    except Exception:
        _LOGGER.exception("failed to load")
        raise


def store_object(input_object, output_file):
    tmp_file = output_file + "_tmp"
    store_object_simple(input_object, tmp_file)

    if os.path.isfile(output_file) is False:
        ## output file does not exist -- rename file
        _LOGGER.info("saving data to: %s", output_file)
        os.rename(tmp_file, output_file)
        return True

    if filecmp.cmp(tmp_file, output_file) is True:
        ## the same files -- remove tmp file
        _LOGGER.info("no new data to store in %s", output_file)
        os.remove(tmp_file)
        return False

    _LOGGER.info("saving data to: %s", output_file)
    os.remove(output_file)
    os.rename(tmp_file, output_file)
    return True


def store_backup(input_object, output_file):
    if store_object(input_object, output_file) is False:
        return False
    ## backup data
    stored_zip_file = output_file + ".zip"
    backup_files([output_file], stored_zip_file)
    return True


def load_object_simple(input_file, default_value=None, *, silent=False):
    try:
        #         _LOGGER.info( "loading data from: %s", input_file )
        with open(input_file, "rb") as fp:
            return pickle.load(fp)
    except AttributeError:
        if silent is False:
            _LOGGER.exception("failed to load: %s", input_file)
        return default_value
    except FileNotFoundError:
        if silent is False:
            _LOGGER.error("failed to load: %s", input_file)
        return default_value
    except ModuleNotFoundError:
        ## class moved to other module
        if silent is False:
            _LOGGER.exception("failed to load: %s", input_file)
        return default_value


def store_object_simple(input_object, output_file):
    outdir_dir = os.path.dirname(output_file)
    if not os.path.exists(outdir_dir):
        os.makedirs(outdir_dir, exist_ok=True)

    with open(output_file, "wb") as fp:
        pickle.dump(input_object, fp)


def backup_files(input_files, output_archive):
    ## create zip
    tmp_zip_file = output_archive + "_tmp"
    with zipfile.ZipFile(tmp_zip_file, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in input_files:
            zip_entry = os.path.basename(file)
            zipf.write(file, zip_entry)

    ## compare content
    stored_zip_file = output_archive
    if os.path.isfile(stored_zip_file) is False:
        ## output file does not exist -- rename file
        _LOGGER.info("storing data to: %s", stored_zip_file)
        os.rename(tmp_zip_file, stored_zip_file)
        return

    if filecmp.cmp(tmp_zip_file, stored_zip_file) is True:
        ## the same files -- remove tmp file
        _LOGGER.info("no new data to backup")
        os.remove(tmp_zip_file)
        return

    ## rename files
    counter = 1
    next_file = f"{stored_zip_file}.{counter}"
    while os.path.isfile(next_file):
        counter += 1
        next_file = f"{stored_zip_file}.{counter}"
    _LOGGER.info("found backup slot: %s", next_file)

    curr_file = stored_zip_file
    while counter > 1:
        curr_file = f"{stored_zip_file}.{counter - 1}"
        os.rename(curr_file, next_file)
        next_file = curr_file
        counter -= 1

    os.rename(stored_zip_file, next_file)
    os.rename(tmp_zip_file, stored_zip_file)


def load_backup(outputArchive):
    with zipfile.ZipFile(outputArchive) as input_zip:
        return {name: input_zip.read(name) for name in input_zip.namelist()}


def compare_files_bytes(file_1_path, file_2_path):
    content_a = read_file_bytes(file_1_path)
    content_b = read_file_bytes(file_2_path)
    a_size = len(content_a)
    b_size = len(content_b)
    if a_size != b_size:
        _LOGGER.info("files size differ: %s %s", a_size, b_size)
        return
    for i in range(a_size):
        if content_a[i] != content_b[i]:
            _LOGGER.info("files differ at byte %s: %s %s", i, content_a[i], content_b[i])


def print_file_content(file_path):
    byte_list = read_file_bytes(file_path)
    # return ''.join('{:02x} '.format(x) for x in byte_list)
    b_size = len(byte_list)
    for i in range(b_size):
        # ruff: noqa: T201
        print(f"byte {i:06d}: {byte_list[i]:02x}")
        # print( ''.join( '{:06d}: {:02x}'.format( i, byte_list[i] ) ) )


def read_file_bytes(file_path):
    byte_list = []
    with open(file_path, "rb") as f:
        while 1:
            byte_s = f.read(1)
            if not byte_s:
                break
            byte_list.append(byte_s[0])
    return byte_list


## ==========================================================


class Versionable:
    def _convertstate_(self, state_dict, state_version) -> dict[str, Any]:
        """Convert state between versions.

        This method is intended to be overriden.
        Method should return modified/updated state of object based on 'state_dict' and 'state_version'.
        """
        # pylint: disable=E1101,C0301
        _LOGGER.info("converting object from version %s to %s", state_version, self._class_version)  # type: ignore[attr-defined]
        # pylint: disable=W0201
        return state_dict

    def __getstate__(self):
        """Get object's state."""
        if not hasattr(self, "_class_version"):
            message = "Your class must define _class_version class variable"
            raise RuntimeError(message)
        # pylint: disable=E1101
        return {"_class_version": self._class_version, **self.__dict__}

    def __setstate__(self, dict_):
        """Restore object state."""
        version_present_in_pickle = dict_.pop("_class_version", None)
        # pylint: disable=E1101
        if version_present_in_pickle == self._class_version:  # type: ignore[attr-defined]
            # pylint: disable=W0201
            self.__dict__ = dict_
        else:
            state_dict = self._convertstate_(dict_, version_present_in_pickle)
            if state_dict is None:
                state_dict = dict_
            self.__dict__ = state_dict


#     @abc.abstractmethod
#     def _convertstate_(self, state_dict, dict_version_ ):
#         raise NotImplementedError('You need to define this method in derived class!')
