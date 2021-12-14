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
"""Representation of instances, specifically ``None`` and ``typing.Any``"""
from collections import defaultdict
from typing import Any
from typing import Optional
from typing import Type
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from adorn.orchestrator.orchestrator import Orchestrator

from adorn.exception.type_check_error import TypeCheckError, WrongTypeError
from adorn.unit.simple import Simple


class Value(Simple):
    """:class:`~adorn.unit.unit.Unit` that holds instances

    This class exists to handle ``None``, which is allowed to
    be used as a type and a value, as well as ``typing.Any``.
    """

    _registry = defaultdict(dict)

    def get(self, key: Any, orchestrator: "Orchestrator") -> Optional[Type]:
        """Return the relevant type that represents a value

        Args:
            key (Any): the type or instance that may be part of ``Value``
            orchestrator (Orchestrator): container of all types, typically
                unused

        Returns:
            Optional[Type]: if ``key`` is represented by ``Value``,
                then the type that is meant to represent an instance
                will be returned, otherwise ``None``
        """
        return self._get(key, orchestrator)

    def contains(self, obj: Any, orchestrator: "Orchestrator") -> bool:
        """Check if the type or instance is part of ``Value``

        Args:
            obj (Any): the type or instance that may be part of ``Value``
            orchestrator (Orchestrator): container of all types, typically
                unused

        Returns:
            bool: if ``True``, the type or instance is contained in ``Value``
        """
        return any(self.relevant_types(obj, orchestrator))


@Value.register("none")
class Rone(Value):
    """Representation of python's `NoneType`, aka ``None``"""

    NoneType = type(None)

    @classmethod
    def _contains(cls, obj: Type, orchestrator: "Orchestrator") -> bool:
        """Check if the type or instance is ``None``

        Args:
            obj (Type): the type or instance that may be ``None``
            orchestrator (Orchestrator): container of all types, which
                is unused, since there are no nested types

        Returns:
            bool: if ``True``, ``obj`` was ``None`` or ``NoneType``
        """
        return obj is None or obj == cls.NoneType

    @classmethod
    def _from_obj(
        cls, target_cls: Type, orchestrator: "Orchestrator", obj: Any
    ) -> None:
        """Generate an instance of ``None``

        Args:
            target_cls (Type): This is ignored
            orchestrator (Orchestrator): This is ignored
            obj (Any): This is ignored

        Returns:
            None: an instance of ``None`` is returned
        """
        return None

    @classmethod
    def _type_check(
        cls, target_cls: Type, orchestrator: "Orchestrator", obj: Any
    ) -> Optional[TypeCheckError]:
        """Check if ``obj`` is ``None``

        Exceptions:
            - :class:`~adorn.exception.type_check_error.WrongTypeError`:
                ``obj`` was not ``None``

        Args:
            target_cls (Type): This is ignored
            orchestrator (Orchestrator): This is ignored
            obj (Any): instance that may be ``None``

        Returns:
            Optional[TypeCheckError]: if ``obj`` wasn't ``None`` an
                exception will be returned, otherwise ``None``
        """
        if not cls._contains(obj, orchestrator):
            return WrongTypeError(cls.NoneType, obj)


@Value.register("any")
class Nny(Value):
    """Representation of python's ``typing.Any``"""

    @classmethod
    def _contains(cls, obj: Type, orchestrator: "Orchestrator") -> bool:
        """Check if the type or instance is ``typing.Any``

        Args:
            obj (Type): the type or instance that may be ``typing.Any``
            orchestrator (Orchestrator): container of all types, which
                is unused, since there are no nested types

        Returns:
            bool: if ``True``, ``obj`` was ``typing.Any``
        """
        return obj == Any

    @classmethod
    def _from_obj(cls, target_cls: Type, orchestrator: "Orchestrator", obj: Any) -> Any:
        """Generate an instance of ``typing.Any``

        Args:
            target_cls (Type): This is ignored
            orchestrator (Orchestrator): This is ignored
            obj (Any): This is returned

        Returns:
            Any: return the ``obj`` that was passed
        """
        return obj

    @classmethod
    def _type_check(
        cls, target_cls: Type, orchestrator: "Orchestrator", obj: Any
    ) -> Optional[TypeCheckError]:
        """Check if ``obj`` is ``typing.Any``.

        This will never produce an exception, since any object in python
        is always a ``typing.Any``

        Args:
            target_cls (Type): This is ignored
            orchestrator (Orchestrator): This is ignored
            obj (Any): This is ignored

        Returns:
            Optional[TypeCheckError]: always ``None``
        """
        return None
