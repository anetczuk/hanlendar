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

from hanlendar import persist

from hanlendar.domainmodel.local.item import Item


_LOGGER = logging.getLogger(__name__)


class ToDo( Item, persist.Versionable ):
    """ToDo is entity without placement in time."""

    ## 0: add subtodos
    ## 1: add base class Item
    _class_version = 1

    def _convertstate_(self, dict_, dictVersion_ ):
        _LOGGER.info( "converting object from version %s to %s", dictVersion_, self._class_version )

        if dictVersion_ is None:
            dictVersion_ = -1

        ## set of conditions converting dict_ to recent version
        if dictVersion_ < 0:
            ## initialize subtodos field
            dict_["subtodos"] = None
            dictVersion_ = 0

        if dictVersion_ == 0:
            ## base class extracted, "subtodos" renamed to "subitems"
            dict_["subitems"] = dict_["subtodos"]
            dict_.pop('subtodos', None)
            dictVersion_ = 1

        # pylint: disable=W0201
        self.__dict__ = dict_

    def addSubtodo(self, todo=None, index=-1):
        if todo is None:
            todo = ToDo()
        return self.addSubItem(todo, index)

    def __str__(self):
        subLen = 0
        if self.subitems is not None:
            subLen = len(self.subitems)
        return "[t:%s d:%s c:%s p:%s subs: %s]" % (
            self.title, self.description,
            self._completed, self.priority, subLen )
