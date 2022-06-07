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

import hanlendar.persist as persist


class FileMock():
    
    def read(self):
        return None
    
    def readline(self):
        return None


class RenamingUnpicklerTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_dict_property(self):
        class TestClass():
            
            def __init__(self):
                self._field = None
                
            @property
            def field(self):
                return self._field
                
            @field.setter
            def field(self, value):
                self._field = value


        testObject = TestClass()
        self.assertTrue( "_field" in testObject.__dict__ )
        self.assertTrue( "field" not in testObject.__dict__ )

    def test_findName_callable(self):
        def mapper_function( module, name ):
            name_map = { "aaa": "bbb" }
            return ( name_map.get( module, module ), name )
        
        file = FileMock()
        unpicker = persist.RenamingUnpickler( file, module_mapper=mapper_function )

        module, name = unpicker.findName( "aaa", "xxx" )

        self.assertEqual( module, "bbb" )
        self.assertEqual( name, "xxx" )
