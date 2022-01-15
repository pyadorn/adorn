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
"""Vanilla coordinator"""
from collections import OrderedDict
from typing import Any
from typing import List
from typing import Optional
from typing import Type
from typing import Union

from adorn.alter.alter import Alter
from adorn.exception.type_check_error import TypeCheckError
from adorn.orchestrator.orchestrator import Orchestrator
from adorn.unit.unit import Unit


class Base(Orchestrator):
    """Vanilla coordinator between different :class:`~adorn.unit.unit.Unit`

    ``Base`` finds the first :class:`~adorn.unit.unit.Unit` specified in
    the list of :class:`~adorn.unit.unit.Unit` that contains a type
    and delegates the action to the given :class:`~adorn.unit.unit.Unit`.
    Therefore, the earlier a :class:`~adorn.unit.unit.Unit` appears in
    ``units`` the higher priority it has in the orchestrator.

    Args:
        units (List[Unit]): a collection of collection of types
        alters (List[Alter]): a collection of ways to dynamically alter
            a configuration

    Attributes:
        unit_dict (OrderedDict[Type, Unit]): a mapping from a type of a
            :class:`~adorn.unit.unit.Unit` to an instance of the
            :class:`~adorn.unit.unit.Unit`
    """

    def __init__(self, units: List[Unit], alters: Optional[List[Alter]] = None) -> None:
        super().__init__()
        self.units = units
        self.alters = alters or []
        self.unit_dict = OrderedDict([(type(i), i) for i in self.units])

    def contains(self, cls: Type) -> bool:
        """Check if ``Type`` is contained in one of the :class:`~adorn.unit.unit.Unit` objects

        Args:
            cls (Type): a type that is being checked to see if
                it exists in one of the :class:`~adorn.unit.unit.Unit`

        Returns:
            bool: if ``True`` a :class:`~adorn.unit.unit.Unit`
                contained in the orchestrator contains
                the provided type
        """  # noqa: B950
        return any(i.contains(cls, self) for i in self.units)

    def get(self, cls: Type) -> Unit:
        """Finds the :class:`~adorn.unit.unit.Unit` associated with `cls`

        .. note::

            The first :class:`~adorn.unit.unit.Unit` will be returned,
            where order is determined by a
            :class:`~adorn.unit.unit.Unit` location in ``units``.

        Args:
            cls (Type): a type that you want the associated ``Unit`` of

        Returns:
            Unit: The collection of types that contains ``cls``

        Raises:
            TypeCheckError: ``cls`` cannot be represented by any of
                the :class:`~adorn.unit.unit.Unit` contained in the
                orchestrator
        """
        for i in self.units:
            if i.contains(cls, self):
                return i
        ru_str = "\n".join([f"{type(i)}" for i in self.units])
        raise TypeCheckError(
            target_cls=cls,
            msg=[
                f"{cls} is not supported by any of the following Unit's:",
                f"{ru_str}",
            ],
        )

    def a_get(self, cls: Type, obj: Any) -> List[Alter]:
        """Finds all the :class:`~adorn.alter.alter.Alter` associated with `cls`

        .. note::

            The list of :class:`~adorn.alter.alter.Alter` will be returned,
            in the order :class:`~adorn.alter.alter.Alter` were passed.

        Args:
            cls (Type): a type that you want to check or convert the ``obj`` into
            obj (Any): the object to be type checked or converted into ``cls``

        Returns:
            List[Alter]: the classes requested to perform a dynamic alteration
                to the ``obj``
        """
        return [i for i in self.alters if i.a_contains(cls, self, obj)]

    def alter_obj(self, cls: Type, obj: Any) -> Union[Any, TypeCheckError]:
        """Poterntially perform a dynamic alteration to an object

        Args:
            cls (Type): a type that you want to check or convert the ``obj`` into
            obj (Any): the object to be type checked or converted into ``cls``

        Returns:
            Union[Any, TypeCheckError]: Either an unaltered ``obj`` is returned, when no
                :class`~adorn.alter.alter.Alter` in ``alters`` contains the
                given ``cls`` and ``obj``, an altered ``obj`` is returned when the
                given ``cls`` and ``obj`` is contained by an
                :class`~adorn.alter.alter.Alter` in ``alters``, or a ``TypeCheckError``,
                when there was an issue performing a dynamic alteration to the ``obj``
        """
        alter_list = self.a_get(cls, obj)
        for alter in alter_list:
            obj = alter.alter_obj(cls, self, obj)
        return obj

    def type_check(self, cls: Type, obj: Any) -> Optional[TypeCheckError]:
        """Check if `obj` can be converted to type of `cls`

        First, the code gets the :class:`~adorn.unit.unit.Unit` that
        contains ``cls``.  Then the type checking is delegated to the
        relevant :class:`~adorn.unit.unit.Unit`.

        Args:
            cls (Type): the type ``obj`` would be converted into
            obj (Any): an instance to be converted into type ``cls``

        Returns:
            Optional[TypeCheckError]: if ``None``, ``obj`` can be converted to an
                instance of ``cls``, otherwise an error is returned explaining
                why an ``obj`` cannot be converted to an instance of ``cls``
        """
        obj = self.alter_obj(cls, obj)
        if isinstance(obj, TypeCheckError):
            return obj
        ru = self.get(cls)
        return ru.type_check(cls, self, obj)

    def from_obj(self, cls: Type, obj: Any) -> Any:
        """Generate an instance of type `cls` from `obj`

        First, the code gets the :class:`~adorn.unit.unit.Unit` that
        contains ``cls``.  Then the instantiating is delegated to the
        relevant :class:`~adorn.unit.unit.Unit`.

        Args:
            cls (Type): the type ``obj`` would be converted into
            obj (Any): an instance to be converted into type ``cls``

        Returns:
            Any: an instance of type ``cls``, that was created from ``obj``

        Raises:
            obj: obj is a ``TypeCheckError`` indicating there was an issue
                applying a dynamic alteration to ``obj``
        """
        obj = self.alter_obj(cls, obj)
        if isinstance(obj, TypeCheckError):
            raise obj
        ru = self.get(cls)
        return ru.from_obj(cls, self, obj)
