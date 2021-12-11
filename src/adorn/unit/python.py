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
"""Representation of python's std lib"""
import collections
from copy import deepcopy
from inspect import isclass
from typing import _GenericAlias
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Mapping
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Type
from typing import TYPE_CHECKING
from typing import Union

if TYPE_CHECKING:  # pragma: no cover
    from adorn.orchestrator.orchestrator import Orchestrator

from adorn.exception.type_check_error import (
    HashableError,
    KeyValueError,
    TupleArgLenError,
    TypeCheckError,
    UnRepresentedTypeError,
    WrongTypeError,
)
from adorn.unit.simple import Simple


class Python(Simple):
    """:class:`~adorn.unit.unit.Unit` that holds types in python's std lib."""

    _registry = collections.defaultdict(dict)

    def get(self, key: Any, orchestrator: "Orchestrator") -> Optional[type]:
        """Return the relevant python std lib type

        Args:
            key (Any): the type that may be part of python's
                std lib
            orchestrator (Orchestrator): container of all types, typically
                used to recurse nested types

        Returns:
            Optional[type]: if ``key`` is part of python's std lib,
                then the type that is meant to represent the python
                std lib type will be returned, otherwise ``None``
        """
        if isclass(key) or isinstance(key, _GenericAlias):
            return self._get(key, orchestrator)
        return None

    def contains(self, obj: Any, orchestrator: "Orchestrator") -> bool:
        """Check if the type is part of python's std lib.

        Args:
            obj (Any): the type that may be part of python's
                std lib
            orchestrator (Orchestrator): container of all types, typically
                used to recurse nested types

        Returns:
            bool: if ``True``, the type is part of python's std lib
        """
        if not (isclass(obj) or isinstance(obj, _GenericAlias)):
            return False
        return any(self.relevant_types(obj, orchestrator))


class BuiltIn(Python):
    """Representation of python's built-in types"""

    base_type: type
    """the built-in python type the subclass is supposed to represent"""

    hashable: bool = True
    """python's built-in types are hashable"""

    unacceptable_subtype: Set[type] = {}
    """types that do not map to the
       given python built-in type.  This exists to prevent ``bool``
       from being confused as an ``int``."""

    @classmethod
    def _contains(cls, obj: Type, orchestrator: "Orchestrator") -> bool:
        """Check if the type is part of python's built-in types.

        Args:
            obj (Type): the type that may be part of python's
                built-in types
            orchestrator (Orchestrator): container of all types, which
                is unused, since there are no nested types

        Returns:
            bool: if ``True``, the type is part of python's std lib
        """
        return (not isinstance(obj, _GenericAlias)) and (
            (issubclass(obj, cls.base_type) or (issubclass(obj, cls)))
            and obj not in cls.unacceptable_subtype
        )

    @classmethod
    def _from_obj(cls, target_cls: type, orchestrator: "Orchestrator", obj: Any) -> Any:
        """Instantiate an instance of the python built-in type

        Args:
            target_cls (type): The python built-in class, an
                instance will be generated of
            orchestrator (Orchestrator): container of all types,
                which is unused
            obj (Any): an instance that will be converted to an
                instance of type ``target_cls``

        Returns:
            Any: an instance of the python built-in type, as specified
                by ``target_cls``
        """
        return cls.base_type(obj)

    @classmethod
    def additional_checks(
        cls, orchestrator: "Orchestrator", obj: Any
    ) -> Optional[TypeCheckError]:
        """Type checks specific to a given type

        Args:
            orchestrator (Orchestrator): container of all types,
                typically unused
            obj (Any): an instance that will have additional
                type checking performed against it

        Returns:
            Optional[TypeCheckError]: either a ``TypeCheckError`` containing
                the reason why the ``obj`` didn't pass the additional checks,
                otherwise ``None``
        """
        return None

    @classmethod
    def _type_check(
        cls, target_cls: Type, orchestrator: "Orchestrator", obj: Any
    ) -> Optional[TypeCheckError]:
        """Check if an instance could be converted to the desired python built-in type

        Exceptions:
            - :class:`~adorn.exception.type_check_error.WrongTypeError`:
                ``obj`` was not of the appropriate type

        Args:
            target_cls (Type): The python built-in class, ``obj``
                will be checked against
            orchestrator (Orchestrator): container of all types,
                which is unused
            obj (Any): an instance that will be checked against
                the type ``target_cls``

        Returns:
            Optional[TypeCheckError]: either a ``TypeCheckError`` containing
                the reason why the ``obj`` didn't type check, otherwise
                ``None``
        """
        if not isinstance(obj, cls.base_type):
            return WrongTypeError(target_cls=cls.base_type, obj=obj)
        return cls.additional_checks(orchestrator=orchestrator, obj=obj)


class Wrapper(Python):
    """Base class for python wrapper types."""

    @staticmethod
    def is_hashable(
        target_cls: Type,
        target_arg: Type,
        orchestrator: "Orchestrator",
        obj: Iterable[Any],
    ) -> Optional[TypeCheckError]:
        """Check if a given type may be hashed.

        Exceptions:
            - :class:`~adorn.exception.type_check_error.UnRepresentedTypeError`:
                the nested argument, did not map to any of the types contained in
                the :class:`~adorn.orchestrator.orchestrator.Orchestrator`
            - :class:`~adorn.exception.type_check_error.HashableError`:
                the nested argument, could not be hashed

        Args:
            target_cls (Type): fully instantiated wrapper type
            target_arg (Type): nested type, that is required to be hashable
            orchestrator (Orchestrator): container of all types, used to recurse
            obj (Iterable[Any]): the instance, pre conversion, used to enrich
                error messages, if they occur

        Returns:
            Optional[TypeCheckError]: if ``TypeCheckError`` then there was
                an issue with the nested type, otherwise ``None``
        """
        if not orchestrator.contains(target_arg):
            return UnRepresentedTypeError(
                target_cls=target_cls, unit=orchestrator, obj=obj
            )
        unit = orchestrator.get(target_arg).get(target_arg, orchestrator)
        if not unit.hashable:
            return HashableError(target_cls=target_cls, unit=unit, obj=obj)


@Python.register("int")
class Int(BuiltIn):
    """Representation of python's ``int`` type"""

    base_type = int
    unacceptable_subtype: Set[type] = {bool}

    @classmethod
    def additional_checks(
        cls, orchestrator: "Orchestrator", obj: Any
    ) -> Optional[TypeCheckError]:
        """Type checks specific to ``int``

        Exceptions:
            - :class:`~adorn.exception.type_check_error.WrongTypeError`:
                ``obj`` was of type ``bool``, not ``int``

        Args:
            orchestrator (Orchestrator): container of all types,
                unused
            obj (Any): an instance that will have additional
                type checking performed against it

        Returns:
            Optional[TypeCheckError]: either a ``TypeCheckError`` containing
                the reason why the ``obj`` didn't pass the additional checks,
                otherwise ``None``
        """
        if type(obj) == bool:
            return WrongTypeError(int, obj)


@Python.register("str")
class Str(BuiltIn):
    """Representation of python's ``str`` type"""

    base_type = str


@Python.register("bool")
class Bool(BuiltIn):
    """Representation of python's ``bool`` type"""

    base_type = bool


@Python.register("float")
class Float(BuiltIn):
    """Representation of python's ``float`` type"""

    base_type = float


@Python.register("list")
class Rterable(Wrapper):
    """Representation of python's ``Iterable`` type"""

    @classmethod
    def _contains(cls, obj: Type, orchestrator: "Orchestrator") -> bool:
        """Check if the type is ``Iterable``

        Args:
            obj (Type): the type that may be ``Iterable``
            orchestrator (Orchestrator): container of all types,
                used to recurse nested type

        Returns:
            bool: if ``True``, the type is ``Iterable``
        """
        origin = getattr(obj, "__origin__", None)
        args = getattr(obj, "__args__", [])
        return (
            origin in {collections.abc.Iterable, Iterable, List, list}
            and len(args) == 1
            and orchestrator.contains(args[0])
        )

    @classmethod
    def _from_obj(
        cls, target_cls: type, orchestrator: "Orchestrator", obj: Iterable[Any]
    ) -> Any:
        """Instantiate an instance of ``Iterable``

        Args:
            target_cls (type): The fully instantiated ``Iterable`` type, an
                instance will be generated of
            orchestrator (Orchestrator): container of all types,
                which is used to instantiate the elements of the ``Iterable``
            obj (Any): an instance that will be converted to an
                instance of type ``target_cls``

        Returns:
            Any: an instance of ``Iterable``, as specified
                by ``target_cls``
        """
        args = getattr(target_cls, "__args__", [])
        return [orchestrator.from_obj(args[0], i) for i in obj]

    @classmethod
    def _type_check(
        cls, target_cls: Type, orchestrator: "Orchestrator", obj: Iterable[Any]
    ) -> Optional[TypeCheckError]:
        """Check if an instance could be converted to ``Iterable``

        Exceptions:
            - :class:`~adorn.exception.type_check_error.KeyValueError`:
                ``obj`` contained elements that couldn't be converted
                to the nested type the ``Iterable`` wraps
            - :class:`~adorn.exception.type_check_error.WrongTypeError`:
                ``obj`` couldn't be converted to an ``Iterable``

        Args:
            target_cls (Type): The fully instantiated ``Iterable`` type, an
                instance will be checked against
            orchestrator (Orchestrator): container of all types,
                which is used to check the elements of the ``Iterable``
            obj (Any): an instance that will be checked against the
                type ``target_cls``

        Returns:
            Optional[TypeCheckError]: Reason why ``obj`` can't be converted
                to an instance of ``target_cls``, otherwise ``None``
        """
        target_arg = getattr(target_cls, "__args__", [])[0]
        if (not isinstance(obj, set)) and any(
            isinstance(obj, i) for i in [collections.abc.Iterable, Iterable, List, list]
        ):
            list_checks = (orchestrator.type_check(target_arg, i) for i in obj)
            relevant_checks = [
                (en, i) for en, i in enumerate(list_checks) if i is not None
            ]
            if relevant_checks:
                key_values = dict(relevant_checks)
                return KeyValueError(
                    target_cls=target_cls, key_values=key_values, obj=obj
                )
            return None
        return WrongTypeError(target_cls=target_cls, obj=obj)


@Python.register("set")
class Ret(Wrapper):
    """Represents Python's ``Set`` type"""

    @classmethod
    def _contains(cls, obj: Type, orchestrator: "Orchestrator") -> bool:
        """Check if the type is ``Set``

        Args:
            obj (Type): the type that may be ``Set``
            orchestrator (Orchestrator): container of all types,
                used to recurse nested type

        Returns:
            bool: if ``True``, the type is ``Set``
        """
        origin = getattr(obj, "__origin__", None)
        args = getattr(obj, "__args__", [])
        return (
            origin in {Set, set} and len(args) == 1 and orchestrator.contains(args[0])
        )

    @classmethod
    def _from_obj(
        cls, target_cls: type, orchestrator: "Orchestrator", obj: Iterable[Any]
    ) -> Set[Any]:
        """Instantiate an instance of ``Set``

        Args:
            target_cls (type): The fully instantiated ``Set`` type, an
                instance will be generated of
            orchestrator (Orchestrator): container of all types,
                which is used to instantiate the elements of the ``Set``
            obj (Any): an instance that will be converted to an
                instance of type ``target_cls``

        Returns:
            Any: an instance of ``Set``, as specified
                by ``target_cls``
        """
        args = getattr(target_cls, "__args__", [])
        return {orchestrator.from_obj(args[0], i) for i in obj}

    @classmethod
    def _type_check(
        cls, target_cls: Type, orchestrator: "Orchestrator", obj: Iterable[Any]
    ) -> Optional[str]:
        """Check if an instance could be converted to ``Set``

        Exceptions:
            - :class:`~adorn.exception.type_check_error.UnRepresentedTypeError`:
                the nested argument of ``Set``, did not map to any of the types
                contained in the :class:`~adorn.orchestrator.orchestrator.Orchestrator`
            - :class:`~adorn.exception.type_check_error.HashableError`:
                the nested argument of ``Set`` wasn't hashable
            - :class:`~adorn.exception.type_check_error.KeyValueError`:
                ``obj`` contained elements that couldn't be converted
                to the nested type the ``Set`` wraps
            - :class:`~adorn.exception.type_check_error.WrongTypeError`:
                ``obj`` couldn't be converted to a ``Set``

        Args:
            target_cls (Type): The fully instantiated ``Set`` type, an
                instance will be checked against
            orchestrator (Orchestrator): container of all types,
                which is used to check the elements of the ``Set``
            obj (Any): an instance that will be checked against the
                type ``target_cls``

        Returns:
            Optional[TypeCheckError]: Reason why ``obj`` can't be converted
                to an instance of ``target_cls``, otherwise ``None``
        """
        target_arg = getattr(target_cls, "__args__", [None])[0]
        if (target_arg is not None) and any(
            isinstance(obj, i) for i in [collections.abc.Iterable, Iterable, List, list]
        ):
            hashable_error = cls.is_hashable(
                target_cls=target_cls,
                target_arg=target_arg,
                orchestrator=orchestrator,
                obj=obj,
            )
            if hashable_error is not None:
                return hashable_error
            list_checks = (orchestrator.type_check(target_arg, i) for i in obj)
            relevant_checks = [i for i in list_checks if i is not None]
            if relevant_checks:
                key_values = dict(enumerate(relevant_checks))
                return KeyValueError(
                    target_cls=target_cls, key_values=key_values, obj=obj
                )
            return None
        return WrongTypeError(target_cls=target_cls, obj=obj)


@Python.register("tuple")
class Ruple(Wrapper):
    """Represents Python's ``Tuple`` type

    .. note::

        This representation of ``Tuple`` does not handle tuples of
        arbitrary length.  The full length of the ``Tuple`` must
        be specified in the type signature at instantiation time.
    """

    @classmethod
    def _contains(cls, obj: Type, orchestrator: "Orchestrator") -> bool:
        """Check if the type is ``Tuple``

        Args:
            obj (Type): the type that may be ``Tuple``
            orchestrator (Orchestrator): container of all types,
                used to recurse nested types

        Returns:
            bool: if ``True``, the type is ``Tuple``
        """
        origin = getattr(obj, "__origin__", None)
        args = getattr(obj, "__args__", [])
        return origin in {Tuple, tuple} and all(orchestrator.contains(i) for i in args)

    @classmethod
    def _from_obj(
        cls, target_cls: type, orchestrator: "Orchestrator", obj: Tuple[Any, ...]
    ) -> Any:
        """Instantiate an instance of ``Tuple``

        Args:
            target_cls (type): The fully instantiated ``Tuple`` type, an
                instance will be generated of
            orchestrator (Orchestrator): container of all types,
                which is used to instantiate the elements of the ``Tuple``
            obj (Any): an instance that will be converted to an
                instance of type ``target_cls``

        Returns:
            Any: an instance of ``Tuple``, as specified
                by ``target_cls``
        """
        args = getattr(target_cls, "__args__", [])
        return tuple(orchestrator.from_obj(i, j) for i, j in zip(args, obj))

    @classmethod
    def _type_check(
        cls, target_cls: Type, orchestrator: "Orchestrator", obj: Tuple[Any, ...]
    ) -> Optional[str]:
        """Check if an instance could be converted to ``Tuple``

        Exceptions:
            - :class:`~adorn.exception.type_check_error.KeyValueError`:
                ``obj`` contained elements that couldn't be converted
                to the nested type the ``Tuple`` wraps
            - :class:`~adorn.exception.type_check_error.WrongTypeError`:
                ``obj`` couldn't be converted to a ``Tuple``

        Args:
            target_cls (Type): The fully instantiated ``Tuple`` type, an
                instance will be checked against
            orchestrator (Orchestrator): container of all types,
                which is used to check the elements of the ``Tuple``
            obj (Any): an instance that will be checked against the
                type ``target_cls``

        Returns:
            Optional[TypeCheckError]: Reason why ``obj`` can't be converted
                to an instance of ``target_cls``, otherwise ``None``
        """
        target_args = getattr(target_cls, "__args__", [])
        if (
            not isinstance(obj, dict)
            and (target_args != [])
            and (not isinstance(obj, _GenericAlias))
            and isinstance(obj, Iterable)
        ):
            if len(target_args) != len(obj):
                return TupleArgLenError(target_cls, obj)
            list_checks = [
                orchestrator.type_check(i, j) for i, j in zip(target_args, obj)
            ]
            relevant_checks = [
                (en, i) for en, i in enumerate(list_checks) if i is not None
            ]
            if relevant_checks:
                key_values = dict(relevant_checks)
                return KeyValueError(
                    target_cls=target_cls, key_values=key_values, obj=obj
                )
            return None
        return WrongTypeError(target_cls=target_cls, obj=obj)


@Python.register("union")
class Rnion(Wrapper):
    """Represents Python's ``Union`` type"""

    @classmethod
    def _contains(cls, obj: Type, orchestrator: "Orchestrator") -> bool:
        """Check if the type is ``Union``

        Args:
            obj (Type): the type that may be ``Union``
            orchestrator (Orchestrator): container of all types,
                used to recurse nested types

        Returns:
            bool: if ``True``, the type is ``Tuple``
        """
        origin = getattr(obj, "__origin__", None)
        args = getattr(obj, "__args__", [])
        return origin == Union and all(orchestrator.contains(i) for i in args)

    @classmethod
    def _from_obj(cls, target_cls: type, orchestrator: "Orchestrator", obj: Any) -> Any:
        """Instantiate an instance of ``Union``

        Args:
            target_cls (type): The fully instantiated ``Union`` type, an
                instance will be generated of
            orchestrator (Orchestrator): container of all types,
                which is used to instantiate an element of the ``Union``
            obj (Any): an instance that will be converted to an
                instance of type ``target_cls``

        Returns:
            Any: an instance of ``Union``, as specified
                by ``target_cls``

        Raises:
            KeyValueError: couldn't convert ``obj`` to any of the
                types specified in ``Union``
        """
        args = getattr(target_cls, "__args__", [])
        failed_args = []
        for arg in args:
            # do we really need to copy
            obj_prime = deepcopy(obj)
            output = orchestrator.type_check(arg, obj_prime)
            if output is None:
                return orchestrator.from_obj(arg, obj)
            else:
                failed_args.append((arg, output))

        key_values = {k: v for k, v in failed_args}
        raise KeyValueError(target_cls=target_cls, key_values=key_values, obj=obj)

    @classmethod
    def _type_check(
        cls, target_cls: Type, orchestrator: "Orchestrator", obj: Any
    ) -> Optional[str]:
        """Check if an instance could be converted to ``Union``

        Exceptions:
            - :class:`~adorn.exception.type_check_error.KeyValueError`:
                ``obj`` contained elements that couldn't be converted
                to a type specified in the ``Union``

        Args:
            target_cls (Type): The fully instantiated ``Union`` type, an
                instance will be checked against
            orchestrator (Orchestrator): container of all types,
                which is used to check the elements of the ``Union``
            obj (Any): an instance that will be checked against the
                type ``target_cls``

        Returns:
            Optional[TypeCheckError]: Reason why ``obj`` can't be converted
                to an instance of ``target_cls``, otherwise ``None``
        """
        target_args = getattr(target_cls, "__args__", [])
        list_checks = [(i, orchestrator.type_check(i, obj)) for i in target_args]
        if all(i is not None for _, i in list_checks):
            key_values = {k: v for k, v in list_checks}
            return KeyValueError(target_cls=target_cls, key_values=key_values, obj=obj)
        return None


@Python.register("dict")
class Rict(Wrapper):
    """Represents Python's ``Dict`` type"""

    @classmethod
    def _contains(cls, obj: Type, orchestrator: "Orchestrator") -> bool:
        """Check if the type is ``Dict``

        Args:
            obj (Type): the type that may be ``Dict``
            orchestrator (Orchestrator): container of all types,
                used to recurse nested types

        Returns:
            bool: if ``True``, the type is ``Dict``
        """
        origin = getattr(obj, "__origin__", None)
        args = getattr(obj, "__args__", [])
        return (
            origin in {collections.abc.Mapping, Mapping, Dict, dict}
            and len(args) == 2
            and all(orchestrator.contains(i) for i in args)
        )

    @classmethod
    def _from_obj(
        cls, target_cls: type, orchestrator: "Orchestrator", obj: Dict[Any, Any]
    ) -> Dict[Any, Any]:
        """Instantiate an instance of ``Dict``

        Args:
            target_cls (type): The fully instantiated ``Dict`` type, an
                instance will be generated of
            orchestrator (Orchestrator): container of all types,
                which is used to instantiate the keys and values
                of the ``Dict``
            obj (Any): an instance that will be converted to an
                instance of type ``target_cls``

        Returns:
            Any: an instance of ``Dict``, as specified
                by ``target_cls``
        """
        args = getattr(target_cls, "__args__", [])
        return {
            orchestrator.from_obj(args[0], k): orchestrator.from_obj(args[1], v)
            for k, v in obj.items()
        }

    @classmethod
    def _type_check(
        cls, target_cls: Type, orchestrator: "Orchestrator", obj: Dict[Any, Any]
    ) -> Optional[str]:
        """Check if an instance could be converted to ``Dict``

        Exceptions:
            - :class:`~adorn.exception.type_check_error.UnRepresentedTypeError`:
                the key type of ``Dict``, did not map to any of the types
                contained in the :class:`~adorn.orchestrator.orchestrator.Orchestrator`
            - :class:`~adorn.exception.type_check_error.HashableError`:
                the key type of ``Dict`` wasn't hashable
            - :class:`~adorn.exception.type_check_error.KeyValueError`:
                ``obj`` contained elements that couldn't
                be converted to the key or value type the ``Dict`` wraps
            - :class:`~adorn.exception.type_check_error.WrongTypeError`:
                ``obj`` couldn't be converted to a ``Dict``

        Args:
            target_cls (Type): The fully instantiated ``Dict`` type, an
                instance will be checked against
            orchestrator (Orchestrator): container of all types,
                which is used to check the elements of the ``Dict``
            obj (Any): an instance that will be checked against the
                type ``target_cls``

        Returns:
            Optional[TypeCheckError]: Reason why ``obj`` can't be converted
                to an instance of ``target_cls``, otherwise ``None``
        """
        target_args = getattr(target_cls, "__args__", [])
        if all(
            not isinstance(obj, i)
            for i in [collections.abc.Mapping, Mapping, Dict, dict]
        ):
            return WrongTypeError(target_cls=target_cls, obj=obj)
        hashable_error = cls.is_hashable(
            target_cls=target_cls,
            target_arg=target_args[0],
            orchestrator=orchestrator,
            obj=obj,
        )
        if hashable_error is not None:
            return hashable_error
        keys = []
        values = []
        for k, v in obj.items():
            # check key
            k_tc = orchestrator.type_check(target_args[0], k)
            if k_tc is not None:
                keys.append(k_tc)
            # check value
            v_tc = orchestrator.type_check(target_args[1], v)
            if v_tc:
                values.append(v_tc)

        if keys or values:
            # key(s) and/or value(s) didn't pass type_check
            key_values = dict()
            for en, (prefix, lst) in enumerate([("key", keys), ("value", values)]):
                for en_prime, i in enumerate(lst):
                    key_values[f"{prefix}_{target_args[en]}_{en_prime}"] = i
            return KeyValueError(target_cls=target_cls, key_values=key_values, obj=obj)
        return None
