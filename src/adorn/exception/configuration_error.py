# Copyright 2021 Jacob Baumbach
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Generic exception for a misconfigured object."""


class ConfigurationError(Exception):
    """The exception raised by any object when it's misconfigured.

    (e.g. missing properties, invalid properties, unknown properties).

    .. note::

        This ``Exception`` should typically be avoided, and instead an
        exception that subclasses
        :class:`~adorn.exception.type_check_error.TypeCheckError`
        or a new custom ``Exception`` should be used.  These alternate
        ``Exception`` objects contain more information, and are therefore
        more useful for the caller.
    """

    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def __str__(self):
        return self.message
