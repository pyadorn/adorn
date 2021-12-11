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
"""Coordinator between different collections of types."""
from typing import Any
from typing import List
from typing import Optional
from typing import Type

from adorn.exception.type_check_error import TypeCheckError
from adorn.unit.unit import Unit


class Orchestrator:
    """Coordinate actions between a collection of :class:`~adorn.unit.unit.Unit`"""

    units: List[Unit]
    """a collection of collection of types"""

    def contains(self, cls: Type) -> bool:  # pragma: no cover
        """Check if ``Type`` exists in the ``Orchestrator``

        Args:
            cls (Type): a type that is being checked to see if
                it exists in the ``Orchestrator``

        Raises:
            NotImplementedError: This method must be overriden by a subclass
        """
        raise NotImplementedError

    def get(self, cls: Type) -> Unit:  # pragma: no cover
        """Finds the :class:`~adorn.unit.unit.Unit` associated with `cls`

        Args:
            cls (Type): a type that you want the associated ``Unit`` of

        Raises:
            NotImplementedError: This method must be overriden by a subclass
        """
        raise NotImplementedError

    def type_check(
        self, cls: Type, obj: Any
    ) -> Optional[TypeCheckError]:  # pragma: no cover
        """Check if `obj` can be converted to type of `cls`

        Args:
            cls (Type): the type ``obj`` would be converted into
            obj (Any): an instance to be converted into type ``cls``

        Raises:
            NotImplementedError: This method must be overriden by a subclass
        """
        raise NotImplementedError

    def from_obj(self, cls: Type, obj: Any) -> Any:  # pragma: no cover
        """Generate an instance of type `cls` from `obj`

        Args:
            cls (Type): the type ``obj`` would be converted into
            obj (Any): an instance to be converted into type ``cls``

        Raises:
            NotImplementedError: This method must be overriden by a subclass
        """
        raise NotImplementedError
