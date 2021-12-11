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
"""Collection of similar types or values."""
from typing import Any
from typing import Callable
from typing import Optional
from typing import Type
from typing import TYPE_CHECKING
from typing import TypeVar

if TYPE_CHECKING:  # pragma: no cover
    from adorn.orchestrator.orchestrator import Orchestrator

from adorn.exception.type_check_error import TypeCheckError

_T = TypeVar("_T")
A = TypeVar("A")


class Unit:
    """A collection of types or values, that usually have some shared characteristic(s)."""  # noqa: B950

    hashable: bool = False
    """If ``True`` then instances of the given type are hashable"""

    @classmethod
    def register(cls, name: str) -> Callable[[Type[_T]], Type[_T]]:  # pragma: no cover
        """Decorator that maps a string to the type

        Args:
            name (str): a string that will be the key for a ``Type``

        Raises:
            NotImplementedError: This method must be overriden by a subclass
        """
        raise NotImplementedError

    def get(
        self, key: Any, orchestrator: "Orchestrator"
    ) -> Optional[type]:  # pragma: no cover
        """Return the relevant ``Type`` for the `key`

        Args:
            key (Any): the Type that may be a subclass of the ``Unit``
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types

        Raises:
            NotImplementedError: This method must be overriden by a subclass
        """
        raise NotImplementedError

    def contains(
        self, obj: Any, orchestrator: "Orchestrator"
    ) -> bool:  # pragma: no cover
        """Check if `obj` has a corresponding type in `Unit`

        Args:
            obj (Any): the Type that may be a subclass of the given ``Unit``
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types

        Raises:
            NotImplementedError: This method must be overriden by a subclass
        """
        raise NotImplementedError

    def type_check(
        self, target_cls: Type, orchestrator: "Orchestrator", obj: Any
    ) -> Optional[TypeCheckError]:  # pragma: no cover
        """Ensure `obj` can be converted to the type ``target_cls``

        Args:
            target_cls (Type): the target Type, the given ``obj`` will be checked
                against
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): an instance, that will be checked to see if it
                can be converted to an instance of ``target_cls``

        Raises:
            NotImplementedError: This method must be overriden by a subclass
        """
        raise NotImplementedError

    def from_obj(
        self, target_cls: Type, orchestrator: "Orchestrator", obj: Any
    ) -> Any:  # pragma: no cover
        """Convert `obj` to an instance of the type ``target_cls``

        Args:
            target_cls (Type): the target Type, the given ``obj`` will be converted
                into
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): an instance, that will be converted to an
                instance of ``target_cls``

        Raises:
            NotImplementedError: This method must be overriden by a subclass
        """
        raise NotImplementedError
