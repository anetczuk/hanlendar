# MIT License
#
# Copyright (c) 2025 Arkadiusz Netczuk <dev.arnet@gmail.com>
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
import shutil
from pathlib import Path
import contextlib

import socket
import threading

from radicale import config, server


_LOGGER = logging.getLogger(__name__)


class RadicaleLocalServer:

    def __init__(self, config_path, *, remove_storage: bool = False):
        self.configuration = config.load(
            [
                (config_path, False),
            ],
        )
        if remove_storage:
            storage_path = self.configuration.get("storage", "filesystem_folder")
            if storage_path:
                with contextlib.suppress(ImportError):
                    shutil.rmtree(storage_path)
        self.shutdown_r, self.shutdown_w = socket.socketpair()
        self.thread: threading.Thread = None

    def get_local_address(self):
        hosts = self.configuration.get("server", "hosts")
        if not hosts:
            return None
        port = hosts[0][1]
        return f"localhost:{port}"

    def start(self):
        # run server in a background thread
        self.thread = threading.Thread(target=self._start, daemon=True)
        self.thread.start()

    def stop(self):
        self.shutdown_w.close()  # stopping the server
        if self.thread is not None:
            self.thread.join()

    def _start(self):
        server.serve(self.configuration, self.shutdown_r)

    def count_calendars(self, user: str):
        storage_path = self.configuration.get("storage", "filesystem_folder")
        user_path = os.path.join(storage_path, "collection-root", user)
        items = os.listdir(user_path)
        return len(items)

    def count_calendar_items(self, user: str, calendar_id: str):
        storage_path = self.configuration.get("storage", "filesystem_folder")
        user_path = os.path.join(storage_path, "collection-root", user, calendar_id)
        items = os.listdir(user_path)
        return len([fitem for fitem in items if fitem.endswith(".ics")])

    def get_item(self, uuid: str):
        storage_path = self.configuration.get("storage", "filesystem_folder")
        file_name = f"{uuid}.ics"
        for path in Path(storage_path).rglob(file_name):
            return read_file(path)
        return None


## =========================================================================


def read_file(file_path):
    with open(file_path, encoding="utf-8") as f:
        return f.read()
    return None
