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
"""Container of types with a class hierarchy."""
import inspect
import logging
from collections import defaultdict
from typing import _GenericAlias
from typing import Any
from typing import Callable
from typing import cast
from typing import ClassVar
from typing import DefaultDict
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import TYPE_CHECKING
from typing import TypeVar
from typing import Union

if TYPE_CHECKING:  # pragma: no cover
    from adorn.orchestrator.orchestrator import Orchestrator

from adorn.data.constructor import Constructor
from adorn.exception.configuration_error import ConfigurationError
from adorn.exception.type_check_error import (
    ComplexTypeMismatchError,
    ParamError,
    TypeCheckError,
    UnRepresentedTypeError,
)
from adorn.params import Params
from adorn.unit.unit import Unit

logger = logging.getLogger(__name__)

_T = TypeVar("_T")
_UnitT = TypeVar("_UnitT", bound="Unit")
_ComplexT = TypeVar("_ComplexT", bound="Complex")
_SubclassRegistry = Dict[str, Tuple[type, Optional[str]]]


class Complex(Unit):
    """:class:`~adorn.unit.unit.Unit` that preserves class hierarchy

    It is recommended you use this construct for your custom package.
    """

    _registry: ClassVar[DefaultDict[type, _SubclassRegistry]]
    """maps a parent class to all of its subclasses and their associated names"""
    _subclass_registry: Dict[type, Tuple[type, str]]
    """classes that can be instantiated, mapped to their parent and name"""
    _intermediate_registry: DefaultDict[type, List[type]]
    """mapping of classes, who are parents, to their parents"""
    _parent_registry: DefaultDict[_ComplexT, List[_ComplexT]]
    """mapping of parents to their children, who are also parents"""

    constructor_type: Optional[str] = None
    """The name of the :class:`~adorn.unit.constructor_value.ConstructorValue`
       you want to instantiate the arguments for your class"""
    parameter_order: Optional[List[str]] = None
    """The order in which the
       parameters for a class should be instantiated"""
    constructor_name: Optional[str] = None
    """Name of the constructor to use to instantiate the class"""

    @classmethod
    def root(cls: Type[_ComplexT]) -> Callable[[Type[_T]], Type[_T]]:
        """Initialize all the class attributes needed to track the class hieracrchy

        This decorator is typically called on a direct descendant of
        :class:`~adorn.unit.complex.Complex` enabling all of the direct
        descendant's children to be tracked.

        Returns:
            Callable[[Type[_T]], Type[_T]]: decorator that initializes the
                class attributes for tracking
        """

        def _root(subclass: Type[_T]) -> Type[_T]:
            subclass._registry = defaultdict(dict)
            subclass._subclass_registry = dict()
            subclass._intermediate_registry = defaultdict(list)
            subclass._parent_registry = defaultdict(list)
            return subclass

        return _root

    @classmethod
    def register(
        cls: Type[_ComplexT], name: Optional[str]
    ) -> Callable[[Type[_T]], Type[_T]]:
        """Decorator that adds a class to the class hierarchy

        Args:
            name (Optional[str]): The ``str`` that will map to the given type, if
                ``None``, then the class is both a child of another ``Complex`` type
                and a parent of other ``Complex`` type(s), but cannot be
                instantiated

        Returns:
            Callable[[Type[_T]], Type[_T]]: funcion that adds the decorated type
                to the ``_registry`` with the ``name`` being the key and the decorated
                class being the value
        """
        registry = cls._registry[cls]

        def add_subclass_to_registry(subclass: Type[_T]) -> Type[_T]:
            # Add to registry, raise an error if key has already been used.
            if name is not None:
                if name in registry:
                    message = (
                        f"Cannot register {name} as {cls.__name__}; "
                        f"name already in use for {registry[name].__name__}"
                    )
                    raise ConfigurationError(message)
                registry[name] = subclass
                cls._subclass_registry[subclass] = (cls, name)
                if cls in cls._subclass_registry:
                    parent, _ = cls._subclass_registry[cls]
                    cls._parent_registry[parent].append(cls)
            else:
                cls._intermediate_registry[subclass].append(cls)
                cls._parent_registry[cls].append(subclass)
            return subclass

        return add_subclass_to_registry

    @classmethod
    def get_instantiate_children(cls: Type[_ComplexT]) -> Dict[str, _ComplexT]:
        """Get the subclasses for a class that can be instantiated

        Returns:
            Dict[str, _ComplexT]: All the subclasses of a class that can be instantiated
        """
        instantiate_children = cls._explode_registry()
        for i in cls.get_intermediate_children():
            instantiate_children = {
                **i.get_instantiate_children(),
                **instantiate_children,
                **i._explode_registry(),
            }
        return instantiate_children

    @classmethod
    def _explode_registry(cls: Type[_ComplexT]) -> Dict[str, _ComplexT]:
        """Helper method, to get all the descendants of a class

        Returns:
            Dict[str, _ComplexT]: Dictionary containing all the descendants of a class
        """
        instantiate_children = (
            dict() if cls not in cls._subclass_registry else {cls.name(): cls}
        )
        for v in cls._registry[cls].values():
            instantiate_children = {
                **instantiate_children,
                **v.get_instantiate_children(),
            }
        return instantiate_children

    @classmethod
    def get_direct_parent(
        cls: Type[_ComplexT],
    ) -> Optional[Union[_ComplexT, List[_ComplexT]]]:
        """Get the parent(s) of a class

        Returns:
            Optional[Union[_ComplexT, List[_ComplexT]]]: if ``None``, then the class
                has no parents, if ``_ComplexT`` then the class has a parent,
                if ``List[_ComplexT]`` then the class has multiple parents
        """
        if cls in cls._parent_registry:
            return None

        if cls in cls._intermediate_registry:
            return cls._intermediate_registry[cls]

        return cls._subclass_registry[cls][0]

    @classmethod
    def get_intermediate_children(cls: Type[_ComplexT]) -> List[_ComplexT]:
        """Get the children of a class, that are also parents

        .. note::
            Some of the classes in the list may not be able to be instantiated

        Returns:
            List[_ComplexT]: list of subclasses of that are also parents
        """
        return cls._parent_registry.get(cls, [])

    @classmethod
    def name(cls: Type[_ComplexT]) -> str:
        """Get the string associated with a given class

        Returns:
            str: the string associated with a class

        Raises:
            Exception: the given class, cannot be instantiated and therefore
                does not have a name
        """
        if cls not in cls._subclass_registry:
            raise Exception(f"{cls} was not registered as a constructable subclass")
        return cls._subclass_registry[cls][1]

    @classmethod
    def by_name(
        cls: Type[_ComplexT], name: Optional[str] = None
    ) -> Callable[..., _ComplexT]:
        """Returns a callable function that constructs an argument of the class.

        Args:
            name (Optional[str]): name of the class you want the constructor for,
                if ``None``, :meth:`~adorn.unit.complex.Complex.name` will be used

        Returns:
            Callable[..., _ComplexT]: constructor for the requested class
        """
        if cls not in cls._subclass_registry:
            return cls
        name = name or cls.name()
        logger.debug(f"instantiating registered subclass {name} of {cls}")
        subclass = cls.resolve_class_name(name)
        return cast(Type[_ComplexT], subclass)

    @classmethod
    def resolve_class_name(
        cls: Type[_ComplexT], name: Optional[str] = None
    ) -> Type[_ComplexT]:
        """Returns the class that corresponds to the given `name`

        Args:
            name (str): name of the class the caller wants

        Returns:
            Type[_ComplexT]: the type associated with ``name`` specified
        """
        name = name or cls.name()
        children = cls.get_instantiate_children()
        return children[name]

    @classmethod
    def list_available(cls: Type[_ComplexT]) -> List[str]:
        """List all the names of subclasses that can be instantiated

        Returns:
            List[str]: names of subclasses that can be instantiated
        """
        return list(cls.get_instantiate_children().values())

    def match(self, key: Any) -> bool:
        """Check if the key is a subclass of ``Complex``

        Args:
            key (Any): potential type to be checked

        Returns:
            bool: if ``True`` then key is a Type of the appropriate type
        """
        return (
            (not isinstance(key, _GenericAlias))
            and inspect.isclass(key)
            and issubclass(key, type(self))
        )

    def get(self, key: Any, orchestrator: "Orchestrator") -> Optional[type]:
        """Return the relevant registered type

        Args:
            key (Any): the type that may be a registered value
            orchestrator (Orchestrator): container of all types, typically
                used to recurse nested types

        Returns:
            Optional[type]: if ``key`` is a registered value,
                then the registered value is returned, otherwise ``None``
        """
        if self.match(key):
            return key._get()
        return None

    @classmethod
    def _get(cls: Type[_ComplexT]) -> Optional[type]:
        """Get the relevant class

        This method exists to faciliate potential future use cases
        that may require additional logic for getting the correct class

        Returns:
            Optional[type]: return the class associated with the classmethod
        """
        return cls

    def contains(self, obj: Any, orchestrator: "Orchestrator") -> bool:
        """Check if the ``obj`` is registered

        Args:
            obj (Any): potentially a type that may be registered
            orchestrator (Orchestrator): container of all types, which
                is used for nested types

        Returns:
            bool: if ``True``, the type is registered
        """
        if self.match(obj):
            return obj._contains(obj, orchestrator)
        return False

    @classmethod
    def _contains(cls: Type[_ComplexT], obj: Any, orchestrator: "Orchestrator") -> bool:
        """Check if the ``cls`` has been registered

        Args:
            obj (Any): this is unused
            orchestrator (Orchestrator): this is unused

        Returns:
            bool: if ``True``, the type can be represented by ``cls``
        """
        return cls in cls._subclass_registry or cls in cls._registry

    def general_check(
        self,
        cls: Type,
        orchestrator: "Orchestrator",
        obj: Any,
        is_from_obj: bool = False,
    ) -> Optional[TypeCheckError]:
        """Checks that need to be performed for both ``type_check`` and ``from_obj``

        Exceptions:
            - :class:`~adorn.exception.type_check_error.UnRepresentedTypeError`:
                ``obj`` did not map to any of the types contained in
                the ``_registry``
            - :class:`~adorn.exception.type_check_error.ParamError`:
                ``obj`` was not of type :class:`~adorn.params.Params`
            - :class:`~adorn.exception.type_check_error.ComplexTypeMismatchError`:
                The ``type`` key contained in ``obj`` had a value that did not
                map to any of the valid subclasses of ``target_cls``

        Args:
            cls (Type): the target class that ``obj`` is trying to be converted
                into
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): the instance that will have the sanity checks applied
                to it
            is_from_obj (bool): if ``True`` this check is being done for
                :meth:`~adorn.unit.complex.Complex.from_obj`, which allows
                instances of ``cls`` to be considered valid

        Returns:
            Optional[TypeCheckError]: if ``TypeCheckError`` then there was
                an issue which would prevent converting ``obj`` to an instance
                of ``target_cls``, otherwise ``None``
        """
        if not self.contains(cls, orchestrator):
            return UnRepresentedTypeError(cls, self, obj)
        if is_from_obj and isinstance(obj, cls):
            return obj
        if not isinstance(obj, Params):
            return ParamError(target_cls=cls, obj=obj)

        children = cls.get_instantiate_children()
        if obj.get("type") not in children:
            return ComplexTypeMismatchError(cls, children, obj)

    def type_check(
        self, target_cls: Type, orchestrator: "Orchestrator", obj: Any
    ) -> Optional[TypeCheckError]:
        """Ensure `obj` can be converted to the type ``target_cls``

        Exceptions:
            - :class:`~adorn.exception.type_check_error.UnRepresentedTypeError`:
                ``obj`` did not map to any of the types contained in
                the ``_registry``
            - :class:`~adorn.exception.type_check_error.ParamError`:
                ``obj`` was not of type :class:`~adorn.params.Params`
            - :class:`~adorn.exception.type_check_error.ComplexTypeMismatchError`:
                The ``type`` key contained in ``obj`` had a value that did not
                map to any of the valid subclasses of ``target_cls``

        Args:
            target_cls (Type): the target Type, the given ``obj`` will be checked
                against
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): an instance, usually of type :class:`~adorn.params.Params`,
                that will be checked to see if it can be converted to an
                instance of ``target_cls``

        Returns:
            Optional[TypeCheckError]: if ``TypeCheckError`` then there was
                an issue which would prevent converting ``obj`` to an instance
                of ``target_cls``, otherwise ``None``
        """
        general_check_output = self.general_check(target_cls, orchestrator, obj)
        if general_check_output is not None:
            return general_check_output
        ru = target_cls.resolve_class_name(obj.get("type"))
        return ru._type_check(target_cls, orchestrator, obj)

    @classmethod
    def _type_check(
        cls: Type[_ComplexT], target_cls: Type, orchestrator: "Orchestrator", obj: Any
    ) -> Optional[TypeCheckError]:
        """Check that the args, specified in ``obj``, for ``target_cls`` type check

        The checking of arguments for a ``target_cls`` is delegated to
        :class:`~adorn.unit.constructor_value.ConstructorValue`

        Args:
            target_cls (Type): the target Type, the given ``obj`` will be checked
                against
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): an instance, usually of type :class:`~adorn.params.Params`,
                that will be checked to see if it can be converted to an
                instance of ``target_cls``

        Returns:
            Optional[TypeCheckError]: if ``TypeCheckError`` then there was
                an issue which would prevent converting ``obj`` to an instance
                of ``target_cls``, otherwise ``None``
        """
        return orchestrator.type_check(Constructor(cls), obj)

    def from_obj(self, target_cls: Type, orchestrator: "Orchestrator", obj: Any) -> Any:
        """Convert `obj` to an instance of ``target_cls``

        Args:
            target_cls (Type): the target Type, the given ``obj`` will be converted
                into
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): an instance, usually of type :class:`~adorn.params.Params`,
                that will be converted into an instance of ``target_cls``

        Returns:
            Any: an instance of ``target_cls`` derived from ``obj``

        Raises:
            UnRepresentedTypeError: ``obj`` did not map to any of the types contained in
                the ``_registry``
            ParamError: ``obj`` was not of type :class:`~adorn.params.Params`
            ComplexTypeMismatchError: The ``type`` key contained in ``obj`` had a value
                that did not map to any of the valid subclasses of ``target_cls``
        """  # noqa: DAR401, DAR402
        general_check_output = self.general_check(
            target_cls, orchestrator, obj, is_from_obj=True
        )
        if isinstance(general_check_output, TypeCheckError):
            raise general_check_output
        if general_check_output is not None:
            return general_check_output

        ru = target_cls.resolve_class_name(obj.get("type"))
        return ru._from_obj(target_cls, orchestrator, obj)

    @classmethod
    def _from_obj(
        cls: Type[_ComplexT], target_cls: Type, orchestrator: "Orchestrator", obj: Any
    ) -> Any:
        """Convert the args, specified in ``obj``, to instances to be passed ``target_cls`` constructor

        The instantiation of arguments for the``target_cls`` and instantiation of the ``target_cls``
        are delegated to :class:`~adorn.unit.constructor_value.ConstructorValue`

        Args:
            target_cls (Type): the target Type, the given ``obj`` will be converted
                into
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): an instance, usually of type :class:`~adorn.params.Params`,
                that will be converted into an instance of ``target_cls``

        Returns:
            Any: an instance of ``target_cls`` derived from ``obj``
        """  # noqa: B950
        if isinstance(obj, cls):
            return obj
        return orchestrator.from_obj(Constructor(cls), obj)
