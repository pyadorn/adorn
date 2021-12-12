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
"""Representation of ``enum.Enum``"""
from enum import Enum
from inspect import isclass
from typing import Any
from typing import Callable
from typing import ClassVar
from typing import DefaultDict
from typing import Dict
from typing import Optional
from typing import Type
from typing import TYPE_CHECKING
from typing import TypeVar

if TYPE_CHECKING:  # pragma: no cover
    from adorn.orchestrator.orchestrator import Orchestrator

from adorn.exception.type_check_error import (
    AnumMemberError,
    AnumWrongTypeError,
    TypeCheckError,
    UnRepresentedTypeError,
)
from adorn.unit.unit import Unit


_E = TypeVar("_E", bound=Enum)


class Anum(Unit):
    """A wrapper around :class:`~enum.Enum`

    The members of the enumeration are added to
    :attr:`~adorn.unit.anum.Anum._registry` and are accessible
    by specifying the enumeration they belong to and the ``str``
    representation of their name

    .. code-block:: python

        from collections import defaultdict
        from enum import auto, Enum

        from adorn.orchestrator.base import Base
        from adorn.unit.anum import Anum

        class Example(Anum):
            _registry = defaultdict(dict)

        @Example.register()
        class AB(Enum):
            a = auto
            b = auto

        base = Base([Example()])
        assert base.from_obj(AB, "a") == AB.a

    """  # noqa: RST304

    _registry: ClassVar[DefaultDict[type, Dict[str, type]]]

    @classmethod
    def register(cls) -> Callable[[Type[_E]], Type[_E]]:  # pragma: no cover
        """Add :class:`~enum.Enum` and it's members to the :attr:`~adorn.unit.anum.Anum._registry`

        Returns:
            Callable[[Type[_E]], Type[_E]]: funcion that adds the decorated
                :class:`~enum.Enum` and its members to the ``_registry``
        """  # noqa: B950, D202, RST304

        def add_members(subclass: Type[_E]) -> Type[_E]:
            registry = cls._registry[subclass]
            for k, v in subclass.__members__.items():
                registry[k] = v
            return subclass

        return add_members

    def get(
        self, key: Any, orchestrator: "Orchestrator"
    ) -> Optional[type]:  # pragma: no cover
        """Return the relevant ``Anum`` for the `key`

        Args:
            key (Any): the Type that may be a subclass of the ``Unit``
            orchestrator (Orchestrator): container of all types, not used

        Returns:
            Optional[type]: if ``key`` is an ``Anum`` then return it,
                otherwise ``None``
        """
        if self.contains(key, orchestrator):
            return key

    def contains(
        self, obj: Any, orchestrator: "Orchestrator"
    ) -> bool:  # pragma: no cover
        """Check if `obj` is registered to ``Anum``

        Args:
            obj (Any): the Type that may be a subclass of ``Anum``
            orchestrator (Orchestrator): container of all types, not used

        Returns:
            bool: if ``True`` then ``obj`` is represented by ``Anum``,
                otherwise ``False``
        """
        return isclass(obj) and issubclass(obj, Enum) and obj in self._registry

    def type_check(
        self, target_cls: Type, orchestrator: "Orchestrator", obj: Any
    ) -> Optional[TypeCheckError]:  # pragma: no cover
        """Ensure `obj` can be converted to the type ``target_cls``

        Exceptions:
            - :class:`~adorn.exception.type_check_error.UnRepresentedTypeError`:
                ``obj`` did not map to any of the types contained in
                the ``_registry``
            - :class:`~adorn.exception.type_check_error.AnumWrongTypeError`:
                ``obj`` was not of type ``str``
            - :class:`~adorn.exception.type_check_error.AnumMemberError`:
                ``obj`` specified a value that did not map to one of the
                members of ``target_cls``

        Args:
            target_cls (Type): the target Type, the given ``obj`` will be checked
                against
            orchestrator (Orchestrator): container of all types, not used
            obj (Any): an instance, that will be checked to see if it
                can be converted to an instance of ``target_cls``

        Returns:
            Optional[TypeCheckError]: if ``TypeCheckError`` then there was
                an issue which would prevent converting ``obj`` to an instance
                of ``target_cls``, otherwise ``None``
        """
        if not self.contains(target_cls, orchestrator):
            return UnRepresentedTypeError(target_cls=target_cls, unit=self, obj=obj)

        if not isinstance(obj, str):
            return AnumWrongTypeError(target_cls=target_cls, obj=obj)

        if obj not in self._registry[target_cls]:
            return AnumMemberError(target_cls=target_cls, obj=obj)

    def from_obj(self, target_cls: Type, orchestrator: "Orchestrator", obj: Any) -> _E:
        """Convert `obj` to an instance of the type ``target_cls``

        Args:
            target_cls (Type): the target Type, the given ``obj`` will be converted
                into
            orchestrator (Orchestrator): container of all types, not used
            obj (Any): an instance, that will be converted to an
                instance of ``target_cls``

        Returns:
            _E: a member of ``target_cls``
        """
        return self._registry[target_cls][obj]
