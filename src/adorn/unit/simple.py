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
"""Container of types with a flat class hierarchy."""
import logging
from typing import Any
from typing import Callable
from typing import ClassVar
from typing import DefaultDict
from typing import Dict
from typing import Iterable
from typing import Optional
from typing import Type
from typing import TYPE_CHECKING
from typing import TypeVar

if TYPE_CHECKING:  # pragma: no cover
    from adorn.orchestrator.orchestrator import Orchestrator

from adorn.exception.configuration_error import ConfigurationError
from adorn.exception.type_check_error import TypeCheckError, UnRepresentedTypeError
from adorn.unit.unit import Unit

logger = logging.getLogger(__name__)

_T = TypeVar("_T")
A = TypeVar("A")
_SubclassRegistry = Dict[str, type]


class Simple(Unit):
    """:class:`~adorn.unit.unit.Unit` for types with a flat class hierarchy

    Attributes:
        _registry (ClassVar[DefaultDict[type, _SubclassRegistry]]): contains mapping
            from ``str`` to ``Type``
    """

    _registry: ClassVar[DefaultDict[type, _SubclassRegistry]]

    @classmethod
    def register(cls, name: str) -> Callable[[Type[_T]], Type[_T]]:
        """Decorator that adds a type to the ``_registry``

        Args:
            name (str): The ``str`` that will map to the given type

        Returns:
            Callable[[Type[_T]], Type[_T]]: funcion that adds the decorated type
                to the ``_registry`` with the ``name`` being the key and the decorated
                class being the value
        """
        registry = cls._registry[cls]

        def add_subclass_to_registry(subclass: Type[_T]) -> Type[_T]:
            # Add to registry, raise an error if key has already been used.
            if name in registry:
                message = (
                    f"Cannot register {name} as {cls.__name__}; "
                    f"name already in use for {registry[name].__name__}"
                )
                raise ConfigurationError(message)
            registry[name] = subclass
            return subclass

        return add_subclass_to_registry

    def _get(self, key: type, orchestrator: "Orchestrator") -> Optional[type]:
        """Return the relevant type from the ``_registry``

        Args:
            key (type): the type that may be a value in the
                ``_registry``
            orchestrator (Orchestrator): container of all types, typically
                used to recurse nested types

        Returns:
            Optional[type]: if ``key`` is a value in the ``_registry``,
                then the value is returned, otherwise ``None``
        """
        try:
            return next(self.relevant_types(key, orchestrator))
        except StopIteration:
            return None

    @classmethod
    def _contains(cls, obj: Type, orchestrator: "Orchestrator") -> bool:
        """Check if the ``obj`` can be represented by ``cls``

        .. note::

            This method should typically be overriden by all subclasses of
            ``Simple``.

        Args:
            obj (Type): the type that may be represented by ``cls``
            orchestrator (Orchestrator): container of all types, which
                is used for nested types

        Returns:
            bool: if ``True``, the type can be represented by ``cls``
        """
        return False

    def type_check(
        self, target_cls: Type, orchestrator: "Orchestrator", obj: Any
    ) -> Optional[TypeCheckError]:
        """Ensure `obj` can be converted to the type ``target_cls``

        Exceptions:
            - :class:`~adorn.exception.type_check_error.UnRepresentedTypeError`:
                ``obj`` did not map to any of the types contained in
                the ``_registry``

        Args:
            target_cls (Type): the target Type, the given ``obj`` will be checked
                against
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): an instance, that will be checked to see if it
                can be converted to an instance of ``target_cls``

        Returns:
            Optional[TypeCheckError]: if ``TypeCheckError`` then there was
                an issue which would prevent converting ``obj`` to an instance
                of ``target_cls``, otherwise ``None``
        """
        if not self.contains(target_cls, orchestrator):
            return UnRepresentedTypeError(target_cls=target_cls, unit=self, obj=obj)
        ru = self.get(target_cls, orchestrator)
        return ru._type_check(target_cls, orchestrator, obj)

    @classmethod
    def _type_check(
        cls, target_cls: Type, orchestrator: "Orchestrator", obj: Any
    ) -> Optional[TypeCheckError]:
        """Ensure `obj` can be converted to the type ``target_cls``

        .. note::

            This method should typically be overriden by all subclasses of
            ``Simple``.

        Args:
            target_cls (Type): the target Type, the given ``obj`` will be checked
                against
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): an instance, that will be checked to see if it
                can be converted to an instance of ``target_cls``

        Returns:
            Optional[TypeCheckError]: if ``TypeCheckError`` then there was
                an issue which would prevent converting ``obj`` to an instance
                of ``target_cls``, otherwise ``None``
        """
        return None

    def from_obj(self, target_cls: Type, orchestrator: "Orchestrator", obj: Any) -> Any:
        """Convert `obj` to an instance of the type ``target_cls``

        Args:
            target_cls (Type): the target Type, the given ``obj`` will be converted
                into an instance of
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): an instance, that will be converted to an instance of
                ``target_cls``

        Returns:
            Any: an instance of ``target_cls`` that was derived from ``obj``

        Raises:
            UnRepresentedTypeError: ``obj`` did not map to any of the types contained in
                the ``_registry``
        """
        if not self.contains(target_cls, orchestrator):
            raise UnRepresentedTypeError(target_cls=target_cls, unit=self, obj=obj)
        ru = self.get(target_cls, orchestrator)
        return ru._from_obj(target_cls, orchestrator, obj)

    @classmethod
    def _from_obj(cls, target_cls: Type, orchestrator: "Orchestrator", obj: Any) -> Any:
        """Convert `obj` to an instance of the type ``target_cls``

        .. note::

            This method should typically be overriden by all subclasses of
            ``Simple``.

        Args:
            target_cls (Type): the target Type, the given ``obj`` will be converted
                into an instance of
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): an instance, that will be converted to an instance of
                ``target_cls``

        Returns:
            Any: an instance of ``target_cls`` that was derived from ``obj``
        """
        return None

    def relevant_types(self, key: Any, orchestrator: "Orchestrator") -> Iterable[Type]:
        """Iterable containing the types that map to the given ``key``

        Args:
            key (Any): the object to check if it maps to any types in the
                ``_registry``
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types

        Returns:
            Iterable[Type]: collection of types in the ``registry`` that map to ``key``
        """
        return (
            v_prime
            for v in self._registry.values()
            for v_prime in v.values()
            if v_prime._contains(key, orchestrator)
        )
