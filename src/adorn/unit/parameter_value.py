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
"""Handle an argument for a parameter specified in the constructor of a class"""
from collections import defaultdict
from sys import version_info
from typing import Any
from typing import Dict
from typing import Generic
from typing import Optional
from typing import Type
from typing import TYPE_CHECKING
from typing import TypeVar
from typing import Union

if (version_info.major > 3) or (version_info.major == 3 and version_info.minor >= 8):
    from typing import Literal
else:
    from typing_extensions import Literal  # noqa: F401 # pragma: no cover

if TYPE_CHECKING:  # pragma: no cover
    from adorn.orchestrator.orchestrator import Orchestrator

from adorn.data.parameter import Parameter
from adorn.data.constructor import Constructor
from adorn.exception.type_check_error import (
    ExtraLiteralError,
    KeyValueError,
    MalformedDependencyError,
    MalformedLiteralError,
    MissingDependencyError,
    MissingLiteralError,
    TooDeepLiteralError,
    TypeCheckError,
    UnaryLiteralError,
)
from adorn.params import Params
from adorn.unit.complex import _T, Complex
from adorn.unit.simple import Simple

DictStrStr = TypeVar("DictStrStr", bound=Literal[dict()])


class ParameterValue(Simple):
    """:class:`~adorn.unit.unit.Unit` for handling an argument for a parameter specified in a constructor

    :class:`~adorn.data.parameter.Parameter` contains the type and state from the constructor,
    which ``ParameterValue`` allows you to utilize when type checking or instantiating the
    argument associated with the parameter
    """  # noqa: B950

    _registry = defaultdict(dict)

    def contains(self, obj: Any, orchestrator: "Orchestrator") -> bool:
        """Check if the ``obj`` is an instance of :class:`~adorn.data.parameter.Parameter`

        Args:
            obj (Any): potentially an instance of
                :class:`~adorn.data.parameter.Parameter`
            orchestrator (Orchestrator): container of all types, typically
                used to recurse nested types

        Returns:
            bool: if ``True``, ``obj`` is an instance of
                :class:`~adorn.data.parameter.Parameter`
        """  # noqa: B950
        return isinstance(obj, Parameter) and (self.get(obj, orchestrator) is not None)

    def get(self, key: Any, orchestrator: "Orchestrator") -> Optional["ParameterValue"]:
        """Get the relevant class to handle the given :class:`~adorn.data.parameter.Parameter` instance.

        Args:
            key (Any): potentially an instance of
                :class:`~adorn.data.parameter.Parameter``
            orchestrator (Orchestrator): container of all types, typically
                used to recurse nested types

        Returns:
            Optional[ParameterValue]: if ``key`` is an instance of
                :class:`~adorn.data.parameter.Parameter` then a subclass of
                ``ParameterValue`` will be returned, otherwise ``None``
        """  # noqa: B950
        if not isinstance(key, Parameter):
            return None
        # we default all Parameter's to use Identity
        return self._get(key=key, orchestrator=orchestrator) or (
            self._registry[ParameterValue]["identity"]
            if orchestrator.contains(key.cls)
            else None
        )


@ParameterValue.register("identity")
class Identity(ParameterValue):
    """Ignore the additional state in the :class:`~adorn.data.parameter.Parameter`

    We extract the type information from :class:`~adorn.data.parameter.Parameter`
    and pass off the object back to the :class:`~adorn.orchestrator.Orchestrator`
    """

    @classmethod
    def _from_obj(
        cls, target_cls: Parameter, orchestrator: "Orchestrator", obj: Dict[Any, Any]
    ) -> Any:
        """Delegate to the :class:`~adorn.orchestrator.Orchestrator` to instantiate the argument, ``obj``

        Args:
            target_cls (Parameter): instance of
                :class:`~adorn.data.parameter.Parameter`
            orchestrator (Orchestrator): container of all types, used to instantiate
                the argument
            obj (Any): an instance, containing the information to instantiate
                an instance of :attr:`~adorn.data.parameter.Parameter.cls`

        Returns:
            Any: An instance of :attr:`~adorn.data.parameter.Parameter.cls`
        """  # noqa: B950, RST304
        return orchestrator.from_obj(target_cls.cls, obj)

    @classmethod
    def _type_check(
        cls, target_cls: Parameter, orchestrator: "Orchestrator", obj: Dict[Any, Any]
    ) -> Optional[TypeCheckError]:
        """Delegate to the :class:`~adorn.orchestrator.Orchestrator` to type check the argument, ``obj``

        Args:
            target_cls (Parameter): instance of
                :class:`~adorn.data.parameter.Parameter`
            orchestrator (Orchestrator): container of all types, used to type
                check the argument
            obj (Any): an instance, containing the information to instantiate
                an instance of :attr:`~adorn.data.parameter.Parameter.cls`

        Returns:
            Optional[TypeCheckError]: If ``TypeCheckError``, there is an
                issue that would prevent ``obj`` from being converted to an
                instance of :attr:`~adorn.data.parameter.Parameter.cls`,
                otherwise ``None``
        """  # noqa: B950, RST304
        if (target_cls.cls == Any) or (
            getattr(target_cls.cls, "__origin__", None) is None
            and isinstance(obj, target_cls.cls)
        ):
            # object is already instantiated, so we assume it is ok
            return None
        return orchestrator.type_check(target_cls.cls, obj)


class Dependent(ParameterValue):
    """``Dependent`` allows for a parameter to leverage information from other parameters."""  # noqa: B950

    @staticmethod
    def get_constructor(target_cls: Parameter, obj: Dict[Any, Any]) -> Constructor:
        """Generate :class:`~adorn.data.constructor.Constructor` for relevant sub-type

        Args:
            target_cls (Parameter): container of the parent class
            obj (Dict[Any, Any]): arguments to instantiate
                :attr:`~adorn.data.parameter.Parameter.cls`

        Returns:
            Constructor: The constructor for the sub class specified
                 in ``obj``
        """  # noqa: RST304
        subcls = target_cls.args[0].resolve_class_name(obj["type"])
        return Constructor(subcls)

    @staticmethod
    def get_args(
        target_cls: Parameter,
        literal_dict: Dict[str, str],
        dependent_from_obj: bool = False,
        max_depth: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Map the key in literal_dict to its requested dependent state

        Args:
            target_cls (Parameter): container of the local state
            literal_dict (Dict[str, str]): the request for dependent state
            dependent_from_obj (bool): if ``True``, the request is grabbing
                instantiated values, otherwise configured values
            max_depth (Optional[int]): the level at which local state will
                be inspected

        Returns:
            Dict[str, Any]: relevant local state needed by the parameter
        """
        # TODO: currently default args are not supported, this could
        # be accomplished by using the constructor of the object that
        # contains the needed state
        acc = dict()
        for k, v in literal_dict.items():
            local_state = target_cls.local_state
            keys = v.split(".")
            key_len = len(keys)
            upper_bound = (
                max_depth if max_depth is not None and dependent_from_obj else key_len
            )
            not_bad = True
            idx = 0
            while not_bad and idx < upper_bound:
                key = keys[idx]
                if idx == 0 or not dependent_from_obj:
                    # initial key or a DependentTypeCheck._type_check
                    if key not in local_state:
                        not_bad = False
                    else:
                        local_state = local_state[key]
                else:
                    if hasattr(local_state, key):
                        local_state = getattr(local_state, key)
                    else:
                        not_bad = False
                idx += 1
            if not_bad:
                acc[k] = local_state
        return acc

    @classmethod
    def check_args(
        cls, target_cls: Parameter, orchestrator: "Orchestrator"
    ) -> Optional[TypeCheckError]:
        """Ensure type level args are correct

        Exceptions:
            - :class:`~adorn.exception.type_check_error.MalformedDependencyError`:
                the ``Dependent`` type didn't specify the appropriate number of
                arguments
            - :class:`~adorn.exception.type_check_error.MissingLiteralError`:
                the first argument, zero based counting, wasn't a ``typing.Literal``
            - :class:`~adorn.exception.type_check_error.UnaryLiteralError`:
                ``typing.Literal`` specifies more than one argument
            - :class:`~adorn.exception.type_check_error.MalformedLiteralError`:
                ``typing.Literal`` wrapped a value that wasn't of type
                ``Dict[str, str]``

        Args:
            target_cls (Parameter): parameter that is dependent on
                state in the constructor
            orchestrator (Orchestrator): container of types, used
                to check the argument specified in the ``typing.Literal``

        Returns:
            Optional[TypeCheckError]: ``TypeCheckError`` specifying an
                error with the type level dependent argument, otherwise
                ``None``
        """
        if target_cls.args is None or len(target_cls.args) != 2:
            # need to specify a type and a mapping
            return MalformedDependencyError(target_cls=target_cls)

        potential_literal = target_cls.args[1]
        literal_origin = getattr(potential_literal, "__origin__", None)
        if literal_origin != Literal:
            # first arg must be wrapped in a literal
            return MissingLiteralError(target_cls=target_cls)

        literal_arg = getattr(potential_literal, "__args__", None)
        if literal_arg is None or len(literal_arg) != 1:
            # may only provide a single literal arg
            return UnaryLiteralError(target_cls=target_cls)

        literal_arg = literal_arg[0]

        literal_arg_check = orchestrator.type_check(Dict[str, str], literal_arg)
        if literal_arg_check is not None:
            # arg to a literal must be Dict[str, str]
            return MalformedLiteralError(
                target_cls=target_cls,
                literal_type=Dict[str, str],
                child=literal_arg_check,
            )

    @classmethod
    def check_literal_dict(
        cls,
        target_cls: Parameter,
        obj: Dict[Any, Any],
        dependent_from_obj: bool = False,
    ) -> Optional[TypeCheckError]:
        """Ensure literal dict is logical given the class and local state

        Exceptions:
            - :class:`~adorn.exception.type_check_error.ExtraLiteralError`:
                ``typing.Literal`` requested state that weren't part of the
                constructor of the parameter
            - :class:`~adorn.exception.type_check_error.TooDeepLiteralError`:
                ``typing.Literal`` requested state that was more than one layer deep.

        Args:
            target_cls (Parameter): container of the local state and dependency request
            obj (Dict[Any, Any]): arguments for the parameter
            dependent_from_obj (bool): if ``True``, the request is grabbing
                instantiated values, otherwise configured values

        Returns:
            Optional[TypeCheckError]: ``TypeCheckError`` if the request for state
                didn't work with the state that existed, otherwise ``None``
        """
        constructor = cls.get_constructor(target_cls=target_cls, obj=obj)
        literal_dict = target_cls.args[1].__args__[0]
        # check key is actually a parameter to the given class's constructor
        additional_keys = [
            i for i in literal_dict.keys() if i not in constructor.parameters
        ]
        if additional_keys:
            return ExtraLiteralError(target_cls, additional_keys)

        # check values, max, go one layer deep
        split_values = [(i.split("."), i) for i in literal_dict.values()]
        too_deep = [j for i, j in split_values if len(i) > 2]
        if too_deep:
            return TooDeepLiteralError(target_cls, too_deep)

        # check that value exists in the local state
        args = cls.get_args(
            target_cls=target_cls,
            literal_dict=literal_dict,
            dependent_from_obj=dependent_from_obj,
            max_depth=1 if dependent_from_obj else None,
        )
        literal_dict_key_check = cls.check_literal_dict_keys(
            target_cls=target_cls, literal_dict=literal_dict, args=args
        )
        if literal_dict_key_check is not None:
            return literal_dict_key_check

    @classmethod
    def check_literal_dict_keys(
        cls, target_cls: Parameter, literal_dict: Dict[str, str], args: Dict[str, Any]
    ) -> Optional[TypeCheckError]:
        """Ensure all requested args exist in local state

        Exceptions:
            - :class:`~adorn.exception.type_check_error.MissingDependencyError`:
                ``typing.Literal`` requested state that wasn't specified in the
                local state

        Args:
            target_cls (Parameter): container parameter's state
            literal_dict (Dict[str, str]): dependency request
            args (Dict[str, Any]): local state

        Returns:
            Optional[TypeCheckError]: ``TypeCheckError`` if the dependency
                request can't be fulfilled by the local state, otherwise ``None``
        """
        missing_keys = literal_dict.keys() - args.keys()
        if missing_keys:
            return MissingDependencyError(
                target_cls=target_cls,
                missing_dependency={k: literal_dict[k] for k in missing_keys},
            )

    @classmethod
    def perfunctory_type_check(
        cls,
        target_cls: Parameter,
        orchestrator: "Orchestrator",
        obj: Dict[Any, Any],
        dependent_from_obj: bool = False,
    ) -> Optional[TypeCheckError]:
        """Ensure the Dependent type specified is well formed

        Exceptions:
            - see :class:`~adorn.unit.parameter_value.Dependent.check_args`
            - see :class:`~adorn.unit.complex.Complex.general_check`
            - see :class:`~adorn.unit.parameter_value.Dependent.check_literal_dict`

        Args:
            target_cls (Parameter): specification of the parameter
                and its associated state
            orchestrator (Orchestrator): container of types, used
                to check nested types
            obj (Dict[Any, Any]): the arguments to construct the parameter
            dependent_from_obj (bool): if ``True``, the request is grabbing
                instantiated values, otherwise configured values

        Returns:
            Optional[TypeCheckError]: ``TypeCheckError`` if there was an issue
                with the ``DependentType``, otherwise ``None``
        """
        check_arg_ouptut = cls.check_args(
            target_cls=target_cls, orchestrator=orchestrator
        )
        if check_arg_ouptut is not None:
            return check_arg_ouptut

        # perform a Complex.general_check on the given wrapped type
        wrapped_cls = target_cls.args[0]
        cls_unit = orchestrator.get(wrapped_cls)
        wrapped_cls_general_check = cls_unit.general_check(
            wrapped_cls, orchestrator, obj
        )
        if wrapped_cls_general_check is not None:
            return wrapped_cls_general_check

        # check that the literal dict is well specified
        check_literal_dict_output = cls.check_literal_dict(
            target_cls=target_cls, obj=obj, dependent_from_obj=dependent_from_obj
        )
        if check_literal_dict_output is not None:
            return check_literal_dict_output

    @classmethod
    def _from_obj(
        cls, target_cls: Parameter, orchestrator: "Orchestrator", obj: Dict[Any, Any]
    ) -> Dict[Any, Any]:
        """Instantiate a parameter, using arguments and state from the :class:`~adorn.data.constructor.Constructor`

        Exceptions:
            - :class:`~adorn.exception.type_check_error.MalformedDependencyError`:
                the ``Dependent`` type didn't specify the appropriate number of
                arguments
            - :class:`~adorn.exception.type_check_error.MissingLiteralError`:
                the first argument, zero based counting, wasn't a ``typing.Literal``
            - :class:`~adorn.exception.type_check_error.UnaryLiteralError`:
                ``typing.Literal`` specifies more than one argument
            - :class:`~adorn.exception.type_check_error.MalformedLiteralError`:
                ``typing.Literal`` wrapped a value that wasn't of type
                ``Dict[str, str]``

        Args:
            target_cls (Parameter): the requested type and relevant state
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): an instance, containing the arguments for
                :attr:`~adorn.data.parameter.Parameter.cls`

        Returns:
            Any: An instance of :attr:`~adorn.data.parameter.Parameter.cls`
        """  # noqa: B950, DAR401, RST304
        check_arg_ouptut = cls.check_args(
            target_cls=target_cls, orchestrator=orchestrator
        )
        if check_arg_ouptut is not None:
            raise check_arg_ouptut
        literal_dict = target_cls.args[1].__args__[0]

        args = cls.get_args(
            target_cls=target_cls, literal_dict=literal_dict, dependent_from_obj=True
        )

        # check all required state exists
        literal_dict_key_check = cls.check_literal_dict_keys(
            target_cls=target_cls, literal_dict=literal_dict, args=args
        )
        if literal_dict_key_check is not None:
            raise literal_dict_key_check

        # enrich obj with dependent state
        for k, v in args.items():
            if k not in obj:
                obj[k] = v
        subcls = target_cls.args[0].resolve_class_name(obj["type"])
        return orchestrator.from_obj(subcls, obj)


@ParameterValue.register("dependent_type_check")
class DependentTypeCheck(Generic[_T, DictStrStr], Dependent):
    """Parameter that requires local state that is known before instantiation

    The first argument must be a :class:`~adorn.unit.complex.Complex`, that requires
    state, known before construction, from the constructor.  The second argument is
    a ``typing.Literal[Dict[str, str]]`` where the keys specifies the names of the
    dependent parameters and the values are the state needed from the constructor.
    """

    @classmethod
    def _contains(cls, obj: Parameter, orchestrator: "Orchestrator") -> bool:
        """Check if the ``obj`` is an instance of ``DependentTypeCheck``

        Args:
            obj (Parameter): potentially an instance of
                ``DependentTypeCheck``
            orchestrator (Orchestrator): container of all types, typically
                used to recurse nested types

        Returns:
            bool: if ``True``, ``obj`` is an instance of
                ``DependentTypeCheck``
        """  # noqa: B950
        if obj.origin != DependentTypeCheck:
            return False

        return (orchestrator.contains(obj.args[0])) and issubclass(obj.args[0], Complex)

    @classmethod
    def _type_check(
        cls, target_cls: Parameter, orchestrator: "Orchestrator", obj: Dict[Any, Any]
    ) -> Optional[TypeCheckError]:
        """Type check a parameter, using arguments and state from the :class:`~adorn.data.constructor.Constructor`

        Exceptions:
            - see :class:`~adorn.unit.parameter_value.Dependent.perfunctory_type_check`
            - :class:`~adorn.exception.type_check_error.KeyValueError`:
                errors for the argument(s) from ``obj`` and/or local state

        Args:
            target_cls (Parameter): the requested type and relevant state
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): an instance, containing the arguments for
                :attr:`~adorn.data.parameter.Parameter.cls`

        Returns:
            Optional[TypeCheckError]: ``TypeCheckError``, if the state and arguments
                can't generate an instance of :attr:`~adorn.data.parameter.Parameter.cls`,
                otherwise ``None``
        """  # noqa: B950, RST304
        perfunctory_type_check_output = cls.perfunctory_type_check(
            target_cls=target_cls, orchestrator=orchestrator, obj=obj
        )
        if perfunctory_type_check_output is not None:
            return perfunctory_type_check_output

        literal_dict = target_cls.args[1].__args__[0]

        constructor = cls.get_constructor(target_cls=target_cls, obj=obj)
        # perform a Complex.general_check on the requested values
        # need to parse the correct Complex instance for the given
        # parameter's type
        args = Params(cls.get_args(target_cls=target_cls, literal_dict=literal_dict))
        bad_args = dict()
        for k, v in args.items():
            sub = constructor.parameters[k].annotation
            unit = orchestrator.get(sub)
            arg_type_check = None
            if getattr(sub, "__origin__", None) is None and isinstance(v, sub):
                # object is already instantiated, so we assume it is ok
                arg_type_check = None
            elif isinstance(unit, Complex):
                # we do a shallow check on complex types because may contain
                # their own dependencies.
                arg_type_check = unit.general_check(
                    sub, orchestrator=orchestrator, obj=v
                )
            else:
                arg_type_check = orchestrator.type_check(sub, v)
            if arg_type_check is not None:
                bad_args[k] = arg_type_check
        if bad_args:
            return KeyValueError(target_cls, bad_args, obj)

        # generate an instance of Constructor where the key's in the literal_dict
        # are removed from the parameters attribute
        for k in literal_dict:
            if k not in obj:
                constructor.parameters.pop(k)
        return orchestrator.type_check(constructor, obj)


@ParameterValue.register("dependent_from_obj")
class DependentFromObj(Generic[_T, DictStrStr], Dependent):
    """Parameter that requires local state that is known after instantiation

    The first argument must be a :class:`~adorn.unit.complex.Complex`, that requires
    state, known after construction, from the constructor.  The second argument is
    a ``typing.Literal[Dict[str, str]]`` where the keys specifies the names of the
    dependent parameters and the values are the state needed from the constructor.
    """

    @classmethod
    def _contains(cls, obj: Parameter, orchestrator: "Orchestrator") -> bool:
        """Check if the ``obj`` is an instance of ``DependentFromObj``

        Args:
            obj (Parameter): potentially an instance of
                ``DependentFromObj``
            orchestrator (Orchestrator): container of all types, typically
                used to recurse nested types

        Returns:
            bool: if ``True``, ``obj`` is an instance of
                ``DependentFromObj``
        """
        if obj.origin != DependentFromObj:
            return False

        return (orchestrator.contains(obj.args[0])) and issubclass(obj.args[0], Complex)

    @classmethod
    def _type_check(
        cls, target_cls: Parameter, orchestrator: "Orchestrator", obj: Dict[Any, Any]
    ) -> Optional[TypeCheckError]:
        """Type check a parameter, using arguments from ``obj``

        Any local state that has been specified in the second argument to
        ``DependentFromObj`` will not be checked, because nothing has been
        instantiated, yet.

        Exceptions:
            - see :class:`~adorn.unit.parameter_value.Dependent.perfunctory_type_check`

        Args:
            target_cls (Parameter): the requested type and relevant state
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): an instance, containing the arguments for
                :attr:`~adorn.data.parameter.Parameter.cls`

        Returns:
            Optional[TypeCheckError]: ``TypeCheckError``, if the state and arguments
                can't generate an instance of :attr:`~adorn.data.parameter.Parameter.cls`,
                otherwise ``None``
        """  # noqa: B950, RST30
        perfunctory_type_check_output = cls.perfunctory_type_check(
            target_cls=target_cls,
            orchestrator=orchestrator,
            obj=obj,
            dependent_from_obj=True,
        )
        if perfunctory_type_check_output is not None:
            return perfunctory_type_check_output

        literal_dict = target_cls.args[1].__args__[0]
        constructor = cls.get_constructor(target_cls=target_cls, obj=obj)

        # generate an instance of Constructor where the key's in the literal_dict
        # are removed from the parameters attribute
        for k in literal_dict:
            if k not in obj:
                constructor.parameters.pop(k)

        return orchestrator.type_check(constructor, obj)


_DependentT = TypeVar("_DependentT", bound=Dependent)


@ParameterValue.register("dependent_union")
class DependentUnion(Generic[_DependentT, _T], Dependent):
    """Similar to ``typing.Union``, but only accepts two arguments, where the zeroth argument must be :class:`~adorn.unit.parameter_value.Dependent`"""  # noqa: B950

    @staticmethod
    def get_parameter_subtype(target_cls: Parameter, arg: Type) -> Parameter:
        """Generate an Parameter where we update the ``cls`` arg with a type option.

        Args:
            target_cls (Parameter): state and ``DependentUnion`` request
            arg (Type): a type option specified within ``DependentUnion``

        Returns:
            Parameter: state with :attr:`~adorn.data.parameter.Parameter.cls`
                argument specifying a type option specified in ``DependentUnion``
        """  # noqa: RST304
        return Parameter(
            cls=arg,
            parent=target_cls.parent,
            local_state=target_cls.local_state,
            parameter_name=target_cls.parameter_name,
        )

    @classmethod
    def _contains(cls, obj: Parameter, orchestrator: "Orchestrator") -> bool:
        """Check if the ``obj`` is an instance of ``DependentUnion``

        Args:
            obj (Parameter): potentially an instance of
                ``DependentUnion``
            orchestrator (Orchestrator): container of all types, typically
                used to recurse nested types

        Returns:
            bool: if ``True``, ``obj`` is an instance of
                ``DependentUnion``
        """
        if obj.origin != DependentUnion:
            return False
        origin = getattr(obj.args[0], "__origin__", None)
        if origin is None or not issubclass(origin, Dependent):
            return False
        return all(
            orchestrator.contains(
                cls.get_parameter_subtype(target_cls=obj, arg=obj.args[i])
            )
            for i in range(2)
        )

    @classmethod
    def get_parameter(
        cls, target_cls: Parameter, orchestrator: "Orchestrator", obj: Dict[Any, Any]
    ) -> Union[Parameter, KeyValueError]:
        """Type Check the given ``obj`` against all potential types

        Args:
            target_cls (Parameter): state and list of potential types ``obj``
                could be
            orchestrator (Orchestrator): container of all types, typically
                used to recurse nested types
            obj (Dict[Any, Any]): arguments for one of the listed types

        Returns:
            Union[Parameter, KeyValueError]: either a ``Parameter`` which wraps the type
                ``obj`` can be coerced into, otherwise ``KeyValueError`` containing the
                reasons why ``obj`` cannot be coerced into any of the listed types
        """
        key_values = []
        for i in target_cls.args:
            nu_parameter = cls.get_parameter_subtype(target_cls=target_cls, arg=i)
            type_check_output = orchestrator.type_check(nu_parameter, obj)
            if type_check_output is None:
                return nu_parameter
            key_values.append((nu_parameter, type_check_output))
        return KeyValueError(target_cls=target_cls, key_values=key_values, obj=obj)

    @classmethod
    def _from_obj(
        cls, target_cls: Parameter, orchestrator: "Orchestrator", obj: Dict[Any, Any]
    ) -> Dict[Any, Any]:
        """Convert ``obj`` into one of the listed types

        Args:
            target_cls (Parameter): state and list of potential types ``obj``
                could be
            orchestrator (Orchestrator): container of all types, typically
                used to recurse nested types
            obj (Dict[Any, Any]): arguments for one of the listed types

        Returns:
            Any: an instance of one of the listed types

        Raises:
            KeyValueError: ``obj`` can't be coerced into any of the listed types
        """  # noqa: DAR401, DAR402
        output = cls.get_parameter(
            target_cls=target_cls, orchestrator=orchestrator, obj=obj
        )
        if isinstance(output, KeyValueError):
            raise output
        return orchestrator.from_obj(output, obj)

    @classmethod
    def _type_check(
        cls, target_cls: Parameter, orchestrator: "Orchestrator", obj: Dict[Any, Any]
    ) -> Optional[KeyValueError]:
        """Type check ``obj`` against all potential types

        Args:
            target_cls (Parameter): state and list of potential types ``obj``
                could be
            orchestrator (Orchestrator): container of all types, typically
                used to recurse nested types
            obj (Dict[Any, Any]): arguments for one of the listed types

        Returns:
            Optional[KeyValueError]: if ``obj`` can't be coerced into any of the type,
                a ``KeyValueError`` is returned containing the reasons why ``obj``
                cannot be coerced into any of the listed types, otherwise ``None``
        """
        output = cls.get_parameter(
            target_cls=target_cls, orchestrator=orchestrator, obj=obj
        )
        if isinstance(output, KeyValueError):
            return output
        return None
