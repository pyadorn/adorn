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
"""Different ways to handle instances of :class:`~adorn.data.constructor.Constructor`"""
import inspect
from collections import defaultdict
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Set
from typing import Type
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from adorn.orchestrator.orchestrator import Orchestrator

from adorn.data.parameter import Parameter
from adorn.data.constructor import Constructor
from adorn.exception.type_check_error import (
    KeyValueDiffError,
    KeyValueError,
    ParameterOrderError,
    TypeCheckError,
    WrongTypeError,
)
from adorn.unit.simple import Simple


class ConstructorValue(Simple):
    """:class:`~adorn.unit.unit.Unit` that contains all the ways to handle :class:`~adorn.data.constructor.Constructor` instances."""  # noqa: B950

    _registry = defaultdict(dict)

    def contains(self, obj: Any, orchestrator: "Orchestrator") -> bool:
        """Check if the ``obj`` is an instance of :class:`~adorn.data.constructor.Constructor`

        Args:
            obj (Any): potentially an instance of
                :class:`~adorn.data.constructor.Constructor`
            orchestrator (Orchestrator): this is unused

        Returns:
            bool: if ``True``, ``obj`` is an instance of
                :class:`~adorn.data.constructor.Constructor`
        """  # noqa: B950
        return isinstance(obj, Constructor)

    def get(
        self, key: Any, orchestrator: "Orchestrator"
    ) -> Optional["ConstructorValue"]:
        """Get the relevant class to handle the given :class:`~adorn.data.constructor.Constructor` instance.

        The :attr:`~adorn.unit.complex.Complex.constructor_type` attached to the
        :attr:`~adorn.data.constructor.Constructor.subclass` is used to determine which
        subclass of ``ConstructorValue`` to use.  If
        :attr:`~adorn.unit.complex.Complex.constructor_type` is ``None`` then
        :class:`~adorn.unit.constructor_value.BaseConstructorValue` will be returned

        Args:
            key (Any): potentially an instance of
                :class:`~adorn.data.constructor.Constructor``
            orchestrator (Orchestrator): container of all types, typically
                used to recurse nested types

        Returns:
            Optional[ConstructorValue]: if ``key`` is an instance of
                :class:`~adorn.data.constructor.Constructor` then a subclass of
                ``ConstructorValue`` will be returned, otherwise ``None``
        """  # noqa: B950, RST304
        if not self.contains(key, orchestrator):
            return None
        return self._registry[ConstructorValue].get(key.constructor_type or "base")

    def from_obj(
        self, target_cls: Constructor, orchestrator: "Orchestrator", obj: Any
    ) -> Any:
        """Instantiate the arguments and an instance of :attr:`~adorn.data.constructor.Constructor.subclass`

        Args:
            target_cls (Constructor): instance of
                :class:`~adorn.data.constructor.Constructor`
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): an instance, containing the arguments for
                :attr:`~adorn.data.constructor.Constructor.subclass`

        Returns:
            Any: An instance of :attr:`~adorn.data.constructor.Constructor.subclass`
        """  # noqa: B950, RST304
        constructor_value = self.get(target_cls, orchestrator)
        return constructor_value._from_obj(target_cls, orchestrator, obj)

    def type_check(
        self, target_cls: Constructor, orchestrator: "Orchestrator", obj: Any
    ) -> Optional[TypeCheckError]:
        """Check the arguments for :attr:`~adorn.data.constructor.Constructor.subclass`

        Exceptions:
            - :class:`~adorn.exception.type_check_error.WrongTypeError`:
                ``target_cls`` was not an instance of
                :class:`~adorn.data.constructor.Constructor`


        Args:
            target_cls (Constructor): instance of
                :class:`~adorn.data.constructor.Constructor`
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): an instance, containing the arguments for
                :attr:`~adorn.data.constructor.Constructor.subclass`

        Returns:
            Optional[TypeCheckError]: if ``TypeCheckError`` then either
                ``target_cls`` was not an instance of
                :class:`~adorn.data.constructor.Constructor`
                or there are issues which would prevent creating the arguments
                for :attr:`~adorn.data.constructor.Constructor.subclass`,
                otherwise ``None``
        """  # noqa: RST304
        if not self.contains(target_cls, orchestrator):
            return WrongTypeError(Constructor, target_cls)

        constructor_value = self.get(target_cls, orchestrator)
        return constructor_value._type_check(target_cls, orchestrator, obj)

    @staticmethod
    def get_kv(
        main: Dict[str, Any],
        alter_value: Callable[..., type],
        sub: Dict[str, Any],
        missing: Set[str],
        check: Callable[..., bool] = lambda _: False,
    ) -> Optional[Dict[str, Type]]:
        """Generate the difference in keys between ``main`` and ``sub``.

        Args:
            main (Dict[str, Any]): a dict, whose keys are considered necessary
            alter_value (Callable[..., type]): an alteration performed to a value
                of ``main`` before it is added to the returned result
            sub (Dict[str, Any]): a dict which is checked that it contains the
                keys in ``main``
            missing (Set[str]): a collection of keys to be ignored in ``main``
            check (Callable[..., bool]): an additional check on the keys of ``main``,
                which if ``True`` will prevent the key from being checked

        Returns:
            Optional[Dict[str, Type]]: the keys and associated types that were missing
                in ``sub``.  If no keys were missing then ``None``
        """
        extras = dict()
        for k in main.keys():
            if k in missing or check(main[k]):
                continue
            if k not in sub:
                extras[k] = alter_value(main[k])
        if extras:
            return extras

    @staticmethod
    def parameter_consistency(
        target_cls: Constructor, obj: Dict[Any, Any]
    ) -> Optional[KeyValueDiffError]:
        """Check that ``obj`` has all the necessary arguments, and nothing more.

        Args:
            target_cls (Constructor): contains the parameters required by
                :attr:`~adorn.data.constructor.Constructor.subclass`
            obj (Dict[Any, Any]): collection of potential arguments for
                :attr:`~adorn.data.constructor.Constructor.subclass`

        Returns:
            Optional[KeyValueDiffError]: ``None`` if ``obj`` contained the correct
                set of keys, otherwise ``KeyValueDiffError`` is returned which specifies
                the missing and/or additional arguments in ``obj``
        """  # noqa: RST304
        parameter_kv = ConstructorValue.get_kv(
            target_cls.parameters,
            lambda i: i.annotation,
            obj,
            {"self"},
            lambda i: i.default != inspect._empty,
        )
        obj_kv = ConstructorValue.get_kv(obj, type, target_cls.parameters, {"type"})

        if parameter_kv or obj_kv:
            return KeyValueDiffError(
                target_cls=target_cls.subclass,
                parameter_kv=parameter_kv,
                obj_kv=obj_kv,
                obj=obj,
            )
        return None

    @staticmethod
    def dict_type_check(
        target_cls: Constructor,
        orchestrator: "Orchestrator",
        obj: Dict[Any, Any],
    ) -> Optional[KeyValueError]:
        """Type check all the arguments in ``obj``

        Args:
            target_cls (Constructor): instance of
                :class:`~adorn.data.constructor.Constructor`, which
                specifies the parameters for the constructor
            orchestrator (Orchestrator): container of all types, used
                to check the arguments
            obj (Any): an instance, containing the arguments for
                :attr:`~adorn.data.constructor.Constructor.subclass`

        Returns:
            Optional[KeyValueError]: if all the args type check then ``None``,
                otherwise ``KeyValueError``, which specifies the args that
                failed and why
        """  # noqa: RST304
        exception_dict = dict()
        for k in target_cls.parameter_order or obj.keys():
            if k in obj and (k not in {"type"}):
                parameter = Parameter(
                    target_cls.parameters[k].annotation, target_cls, obj, k
                )
                output = orchestrator.type_check(parameter, obj[k])
                if output is not None:
                    exception_dict[k] = output

        if exception_dict:
            return KeyValueError(
                target_cls=target_cls.subclass, key_values=exception_dict, obj=obj
            )
        return None

    @staticmethod
    def check_parameter_order(target_cls: Constructor) -> Optional[ParameterOrderError]:
        """Ensure :attr:`~adorn.unit.complex.Complex.parameter_order` specifies all the parameters.

        Args:
            target_cls (Constructor): :attr:`~adorn.data.constructor.Constructor.subclass`
                specifies a :attr:`~adorn.unit.complex.Complex.parameter_order`

        Returns:
            Optional[ParameterOrderError]: if :attr:`~adorn.unit.complex.Complex.parameter_order`
                is complete then ``None``, otherwise ``ParameterOrderError``, which specifies
                the additional and/or missing parameters in
                :attr:`~adorn.unit.complex.Complex.parameter_order`
        """  # noqa: B950, RST304
        # no parameter_order, then nothing to check
        if target_cls.parameter_order is None:
            return None

        po_set = set(target_cls.parameter_order)
        pk = target_cls.parameters.keys()
        too_few = pk - po_set
        too_many = po_set - pk
        if too_few or too_many:
            return ParameterOrderError(
                target_cls=target_cls, too_few=too_few, too_many=too_many
            )


@ConstructorValue.register("base")
class BaseConstructorValue(ConstructorValue):
    """Vanilla way of type checking and instantiating :class:`~adorn.data.constructor.Constructor` instances"""  # noqa: B950

    @classmethod
    def _from_obj(
        cls, target_cls: Constructor, orchestrator: "Orchestrator", obj: Dict[Any, Any]
    ) -> Dict[Any, Any]:
        """Instantiate the arguments and an instance of :attr:`~adorn.data.constructor.Constructor.subclass`

        Args:
            target_cls (Constructor): instance of
                :class:`~adorn.data.constructor.Constructor`
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Dict[Any, Any]): an instance, containing the arguments for
                :attr:`~adorn.data.constructor.Constructor.subclass`

        Returns:
            Any: An instance of :attr:`~adorn.data.constructor.Constructor.subclass`

        Raises:
            ParameterOrderError: specifies the additional and/or missing parameters
                in :attr:`~adorn.unit.complex.Complex.parameter_order`
        """  # noqa: B950, DAR401, DAR402, RST304
        type_str = obj.pop("type", None)
        paramterer_order_check = cls.check_parameter_order(target_cls=target_cls)
        if paramterer_order_check is not None:
            raise paramterer_order_check
        kwargs = dict()
        for k in target_cls.parameter_order or obj.keys():
            if k in obj:
                parameter = Parameter(
                    target_cls.parameters[k].annotation, target_cls, kwargs, k
                )
                kwargs[k] = orchestrator.from_obj(parameter, obj[k])
        obj["type"] = type_str
        return target_cls.constructor(**kwargs)

    @classmethod
    def _type_check(
        cls, target_cls: Constructor, orchestrator: "Orchestrator", obj: Dict[Any, Any]
    ) -> Optional[TypeCheckError]:
        """Check the arguments for :attr:`~adorn.data.constructor.Constructor.subclass`

        Exceptions:
            - :class:`~adorn.exception.type_check_error.ParameterOrderError`:
                specifies the additional and/or missing parameters
                in :attr:`~adorn.unit.complex.Complex.parameter_order`
            - :class:`~adorn.exception.type_check_error.KeyValueDiffError`:
                missing and/or additional arguments in ``obj``
            - :class:`~adorn.exception.type_check_error.KeyValueError`:
                args in ``obj`` didn't type check

        Args:
            target_cls (Constructor): instance of
                :class:`~adorn.data.constructor.Constructor`
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Dict[Any, Any]): an instance, containing the arguments for
                :attr:`~adorn.data.constructor.Constructor.subclass`

        Returns:
            Optional[TypeCheckError]: if ``TypeCheckError`` there are
                issues which would prevent creating the arguments
                for :attr:`~adorn.data.constructor.Constructor.subclass`,
                otherwise ``None``
        """  # noqa: RST304
        paramterer_order_check = cls.check_parameter_order(target_cls=target_cls)
        if paramterer_order_check is not None:
            return paramterer_order_check
        consistency_message = cls.parameter_consistency(target_cls, obj)
        if consistency_message:
            return consistency_message
        return cls.dict_type_check(
            target_cls=target_cls, orchestrator=orchestrator, obj=obj
        )
