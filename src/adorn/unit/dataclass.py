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
"""Representation of ``dataclasses.dataclass``"""
from dataclasses import is_dataclass
from inspect import isclass
from typing import Any
from typing import Callable
from typing import ClassVar
from typing import Dict
from typing import Optional
from typing import Type
from typing import TYPE_CHECKING
from typing import TypeVar

if TYPE_CHECKING:  # pragma: no cover
    from adorn.orchestrator.orchestrator import Orchestrator

from adorn.data.constructor import Constructor
from adorn.exception.type_check_error import (
    ParamError,
    TypeCheckError,
    UnRepresentedTypeError,
)
from adorn.params import Params
from adorn.unit.unit import Unit


_D = TypeVar("_D")


class DataClass(Unit):
    """A wrapper around :meth:`~dataclasses.dataclass`

    .. code-block:: python

        from dataclasses import dataclass

        from adorn.orchestrator.base import Base
        from adorn.params import Params
        from adorn.unit.dataclass import DataClass

        class Example(DataClass):
            _registry = dict()

        @Example.register()
        @dataclass
        class A:
            a: int
            b: bool

        base = Base([Example()])
        assert base.from_obj(A, Params({"a": 1, "b": False})) == A(1, False)

    """  # noqa: RST304

    _registry: ClassVar[Dict[type, type]]

    @classmethod
    def register(cls) -> Callable[[Type[_D]], Type[_D]]:  # pragma: no cover
        """Add :meth:`~dataclasses.dataclass` to the :attr:`~adorn.unit.anum.Anum._registry`

        Returns:
            Callable[[Type[_D]], Type[_D]]: funcion that adds the decorated
                :meth:`~dataclasses.dataclass` to the ``_registry``
        """  # noqa: B950, D202, RST304

        def add_members(subclass: Type[_D]) -> Type[_D]:
            cls._registry[subclass] = subclass
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
        """Check if `obj` is registered to ``DataClass``

        Args:
            obj (Any): the Type that may be a subclass of ``Anum``
            orchestrator (Orchestrator): container of all types, not used

        Returns:
            bool: if ``True`` then ``obj`` is represented by ``Anum``,
                otherwise ``False``
        """
        return isclass(obj) and is_dataclass(obj) and obj in self._registry

    def type_check(
        self, target_cls: Type, orchestrator: "Orchestrator", obj: Any
    ) -> Optional[TypeCheckError]:  # pragma: no cover
        """Ensure `obj` can be converted to the type ``target_cls``

        Exceptions:
            - :class:`~adorn.exception.type_check_error.UnRepresentedTypeError`:
                ``obj`` did not map to any of the types contained in
                the ``_registry``
            - :class:`~adorn.exception.type_check_error.ParamError`:
                ``obj`` was not of type :class:`~adorn.params.Params`

        Args:
            target_cls (Type): the target Type, the given ``obj`` will be checked
                against
            orchestrator (Orchestrator): container of all types, used to check the
                arguments of the constructor for the given ``dataclass``
            obj (Any): a :class:`~adorn.params.Params`, that will be checked to
                see if it can be converted to an instance of ``target_cls``

        Returns:
            Optional[TypeCheckError]: if ``TypeCheckError`` then there was
                an issue which would prevent converting ``obj`` to an instance
                of ``target_cls``, otherwise ``None``
        """
        if not self.contains(target_cls, orchestrator):
            return UnRepresentedTypeError(target_cls=target_cls, unit=self, obj=obj)

        if not isinstance(obj, Params):
            return ParamError(target_cls=target_cls, obj=obj)

        return orchestrator.type_check(Constructor(target_cls), obj)

    def from_obj(self, target_cls: Type, orchestrator: "Orchestrator", obj: Any) -> _D:
        """Convert `obj` to an instance of the type ``target_cls``

        Args:
            target_cls (Type): the target Type, the given ``obj`` will be converted
                into
            orchestrator (Orchestrator): container of all types, used to instantiate
                the arguments for the constructor of the given ``dataclass``
            obj (Any): an instance, that will be converted to an
                instance of ``target_cls``

        Returns:
            _D: an instantiated :meth:`~dataclasses.dataclass`
        """
        return orchestrator.from_obj(Constructor(target_cls), obj)
