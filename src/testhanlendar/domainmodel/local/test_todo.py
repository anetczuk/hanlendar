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

import unittest

from hanlendar.domainmodel.local.todo import ToDo


class TaskTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_isCompleted(self):
        todo = ToDo()
        self.assertEqual( todo.isCompleted(), False )

        todo.setCompleted()
        self.assertEqual( todo.isCompleted(), True )

    def test_isCompleted_sub(self):
        todo = ToDo()
        self.assertEqual( todo.isCompleted(), False )

        todo.setCompleted()
        self.assertEqual( todo.isCompleted(), True )

        child = todo.addSubtodo( ToDo() )
        self.assertEqual( todo.isCompleted(), False )

        child.setCompleted()
        self.assertEqual( todo.isCompleted(), True )
        self.assertEqual( child.isCompleted(), True )
