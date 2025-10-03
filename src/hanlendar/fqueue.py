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

import pqueue
from filelock import Timeout, FileLock


# script_dir = os.path.dirname(__file__)
# tmp_dir    = os.path.realpath( os.path.join( script_dir, os.pardir, os.pardir, 'tmp' ) )


_LOGGER = logging.getLogger(__name__)


queue_path      = os.path.join( '/tmp', 'hanlendar.spool' )
queue_info_path = os.path.join( queue_path, 'info' )
queue_lock      = os.path.join( '/tmp', 'hanlendar.spool.lock' )


## ensure directory exists (required for watchdog)
os.makedirs( queue_path, exist_ok=True )


def get_from_queue( nowait=False ):
    with FileLock( queue_lock ):
        quene = pqueue.Queue( queue_path )
        if nowait:
            message = quene.get()
        else:
            message = quene.get_nowait()
        quene.task_done()
        return message
    return None


def put_to_queue( message_type, value ):
    with FileLock( queue_lock ):
        quene = pqueue.Queue( queue_path )
        message = (message_type, value)
        print( "adding to queue:", message )
        quene.put( message )
