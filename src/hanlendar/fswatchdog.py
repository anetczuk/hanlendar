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
import time

import contextlib

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


_LOGGER = logging.getLogger(__name__)


class FSWatcher:

    def __init__(self):
        self.observer = Observer()
        self.event_handler = None

    def pause(self):
        if self.event_handler is None:
            return
        self.event_handler.ignore = True

    def resume(self):
        if self.event_handler is None:
            return
        self.observer.event_queue.queue.clear()
        self.event_handler.ignore = False

    def start( self, path, callback=None, recursive=True ):
        _LOGGER.info( "starting file system watchdog on %s", path )
        self.event_handler = FSHandler( callback )
        self.observer.schedule( self.event_handler, path, recursive=recursive )
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()

    def run(self, directory):
        self.start( directory )

        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print( "Error" )

        self.stop()

    @contextlib.contextmanager
    def ignoreEvents(self):
        self.pause()
        yield
        self.resume()


class WatcherBlocker:
    """
    Context guard.

    Disables watcher callbacks in "with" scope.
    """

    def __init__(self, watcher: FSWatcher):
        self.watcher: FSWatcher = watcher

    def __enter__(self):
        if self.watcher is None:
            return
        self.oldEnabled = self.watcher.setEnabled( False )
        _LOGGER.debug( "disabling sysfs watcher, prev state: %s" % self.oldEnabled )
        self.watcher.ignoreNextEvent()

    def __exit__(self, exceptionType, value, traceback):
        _LOGGER.debug( "restoring sysfs watcher state to %s" % self.oldEnabled )
        if self.watcher is None:
            return False                                                            ## do not suppress exceptions
        if self.oldEnabled is None:
            return False                                                            ## do not suppress exceptions
        self.watcher.setEnabled( self.oldEnabled )
        return False                                                                ## do not suppress exceptions



class FSHandler(FileSystemEventHandler):

    def __init__(self, callback=None):
        self.callback = callback
        self.ignore = False

    def on_created(self, event):
        # Take any action here when a file is first created.
        if self.callback is None:
            print( "Received created event - %s." % event.src_path )
            return
        if self.ignore:
            return
        self.callback()


# if __name__ == '__main__':
#     import os
# 
#     queue_path = os.path.join( '/tmp', 'hanlendar.spool' )
#     w = FSWatcher()
#     w.run( queue_path )
