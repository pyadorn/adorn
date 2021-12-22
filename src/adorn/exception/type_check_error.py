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
"""Exceptions specifying why a request was malformed"""
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Type
from typing import TYPE_CHECKING
from typing import Union

if TYPE_CHECKING:  # pragma: no cover
    from adorn.data.parameter import Parameter
    from adorn.params import Params
    from adorn.unit.anum import Anum
    from adorn.unit.unit import Unit


DictOrList = Union[
    Dict[Union[int, str], "TypeCheckError"],
    List[Tuple[Dict[Union[int, str], "TypeCheckError"]]],
]


class TypeCheckError(Exception):
    """Generic ``Exception`` that contains the state the produced the error.

    Args:
        target_cls (Type): the requested type to perform an action against
        msg (List[str]): explanation about the exception
        child (Optional[TypeCheckError]): an excpetion produced by a downstream
            process
        obj (Optional[Any]): the caller provided object, that was innvolved in
            causing the error
    """

    def __init__(
        self,
        target_cls: Type,
        msg: List[str],
        child: Optional["TypeCheckError"] = None,
        obj: Optional[Any] = None,
    ) -> None:
        super().__init__()
        self.target_cls = target_cls
        self.msg = msg
        self.child = child
        self.obj = obj

    def to_str(self, seed: str = "") -> str:
        """Create a sting with the reason/explanation of the error.

        Args:
            seed (str): spacing used to compose error statements in a cute way

        Returns:
            str: information about the error
        """
        prefix = "\n" + seed if seed else ""
        line_break = "\n" + seed
        outer_msg = prefix + line_break.join(self.msg)
        if self.child is None:
            return outer_msg
        return outer_msg + self.child.to_str(seed + "\t")

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return self.to_str()

    def __eq__(self, other) -> bool:
        if type(self) != type(other):
            return False
        return all(
            [
                self.target_cls == other.target_cls,
                self.msg == other.msg,
                self.child == other.child,
                self.obj == other.obj,
            ]
        )


class WrongTypeError(TypeCheckError):
    """Error when provided an ``obj`` of the wrong type

    Args:
        target_cls (type): the requested type to perform an action against
        obj (Any): caller provided object, that is not of type
            ``target_cls``
    """

    def __init__(self, target_cls: type, obj: Any) -> "TypeCheckError":
        target_cls_name = (
            target_cls.__name__ if hasattr(target_cls, "__name__") else target_cls
        )
        msg = [
            f"Expected an object of type {target_cls_name},\n ",
            "but received an object of type ",
            f"{type(obj).__name__}\nwith a value of:",
            f"\n\t{obj}",
        ]
        super().__init__(target_cls=target_cls, msg=msg, child=None, obj=obj)


class ParamError(TypeCheckError):
    """Error when an obj of not type :class:`~adorn.params.Params` is passed

    Args:
        target_cls (type): the requested type to perform an action against
        obj (Any): caller provided object, that is not of type
            ``Params``
    """

    def __init__(self, target_cls: type, obj: Any) -> "TypeCheckError":
        target_cls_name = (
            target_cls.__name__ if hasattr(target_cls, "__name__") else target_cls
        )
        msg = [
            f"For {target_cls_name}, expected a Params object",
            f"but received an object of type {type(obj).__name__}",
        ]
        super().__init__(target_cls=target_cls, msg=msg, child=None, obj=obj)


class UnRepresentedTypeError(TypeCheckError):
    """Error when a :class:`~adorn.unit.unit.Unit` does not cotain a given type.

    Args:
        target_cls (type): The requested type that can't be expressed by the ``Unit``
        unit (Unit): a collection of types that can't express ``target_cls``
        obj (Any): the caller created object that was supposed to map to ``target_cls``
    """

    def __init__(self, target_cls: type, unit: "Unit", obj: Any) -> "TypeCheckError":
        target_cls_name = (
            target_cls.__name__ if hasattr(target_cls, "__name__") else target_cls
        )
        msg = [
            (
                f"Requested type: {target_cls_name} with an object of type:"
                f"{type(obj).__name__}"
            ),
            "with a value of:",
            f"{obj}",
            f"didn't match any subtype of {type(unit).__name__}",
        ]
        super().__init__(target_cls=target_cls, msg=msg, child=None, obj=obj)


class KeyValueError(TypeCheckError):
    """Error when dependencies of the given ``target_cls`` produce an error.

    Args:
        target_cls (type): the requested type, whose dependencies produced error(s)
        key_values (DictOrList): a collection of the name of the dependency and
            error the dependency produced
        obj (Union[List[Any], Dict[str, Any]]): caller specified values for the
            dependencies
    """

    def __init__(
        self,
        target_cls: type,
        key_values: DictOrList,
        obj: Union[List[Any], Dict[str, Any]],
    ) -> None:
        msg = self.get_msg(target_cls, key_values)
        self.key_values = key_values
        super().__init__(target_cls, msg, child=None, obj=obj)

    @staticmethod
    def get_msg(
        target_cls: type,
        key_values: DictOrList,
    ) -> List[str]:
        """Generate the msg containing why the dependencies produced an error.

        Args:
            target_cls (type): the requested type, whose dependencies produced
                error(s)
            key_values (DictOrList): a collection of the name of the dependency
                and error the dependency produced

        Returns:
            List[str]: message containing the reasons why the dependencies produced
                errors
        """
        result_list = []
        collection = key_values.items() if isinstance(key_values, dict) else key_values
        for k, v in collection:
            msg = "\t-" + f"{k}: " + v.to_str("\t\t")
            result_list.append(msg)
        return [
            f"Failed to construct {target_cls} because of the following values:"
        ] + result_list


class HashableError(TypeCheckError):
    """Error when a Unit's subtype is not hashable.

    This is typically caused when a type is wrapped in a ``Set``, but the
    wrapped type is not hashable.

    Args:
        target_cls (Type): The requested type, that isn't hashable
        unit (Unit): the collection of types that contained ``target_cls``
        obj (Optional[Any]): the caller created object that maps
            to the unhashable type
    """

    def __init__(self, target_cls: Type, unit: "Unit", obj: Optional[Any]) -> None:
        target_origin = getattr(target_cls, "__origin__", None)
        target_arg = getattr(target_cls, "__args__", [None])[0]
        ta = target_arg or target_origin or target_cls
        msg = [
            f"Failed to construct {target_cls}, because {ta}",
            "is not hashable.  You may need to alter the hashable attr of",
            f"{unit.__name__} or use a type that is hashable",
        ]
        super().__init__(target_cls, msg, child=None, obj=obj)


class TupleArgLenError(TypeCheckError):
    """Exception when the number of args specified in the Tuple does not match the object's length.

    Args:
        target_cls (Type): the tuple type
        obj (Optional[Any]): the caller created object that has a length
            different than that specified by ``target_cls``
    """  # noqa: B950

    def __init__(self, target_cls: Type, obj: Optional[Any]) -> None:
        target_args = getattr(target_cls, "__args__", [None])
        msg = [
            f"Failed to create a {target_cls} because {len(target_args)} args were",
            f"expected but only {len(obj)} were received.",
            f"obj had a value of {obj}",
        ]
        super().__init__(target_cls, msg, child=None, obj=obj)


class KeyValueDiffError(TypeCheckError):
    """:class:`~adorn.params.Params` object had missing and/or additional information

    Args:
        target_cls (type): the type that the ``obj`` was intended to create
        parameter_kv (Optional[Dict[str, type]]): missing information from the ``obj``
        obj_kv (Optional[Dict[str, type]]): additional information in the ``obj``
        obj (Params): the ``Params`` object that has missing and/or additional
            information
    """

    def __init__(
        self,
        target_cls: type,
        parameter_kv: Optional[Dict[str, type]],
        obj_kv: Optional[Dict[str, type]],
        obj: "Params",
    ) -> None:
        msg = [
            f"{target_cls} was missing arguments, indicated with a `-`",
            "and/or passed additional arguments indicated with a `+`",
        ]
        if parameter_kv:
            missing = [
                f"\t- {k}: {getattr(v, '__name__', v)}" for k, v in parameter_kv.items()
            ]
            msg.extend(missing)

        if obj_kv:
            added = [f"\t+ {k}: {getattr(v, '__name__', v)}" for k, v in obj_kv.items()]
            msg.extend(added)
        self.parameter_kv = parameter_kv
        self.obj_kv = obj_kv
        super().__init__(target_cls, msg, child=None, obj=obj)


class ComplexTypeMismatchError(TypeCheckError):
    """The `type` specified doesn't match any of the options for the ``target_cls``

    Args:
        target_cls (Type): the requested type
        possibilities (Dict[str, type]): the different subclasses that can be
            requested for ``target_cls``
        obj (Params): ``Params`` with a value for ``type`` that doesn't map to
            any of the subclasses of ``target_cls``
    """

    def __init__(
        self, target_cls: Type, possibilities: Dict[str, type], obj: "Params"
    ) -> None:
        msg = [
            f"For {target_cls}, a Params object specified a `type`",
            f"of {obj.get('type')}, which is not an acceptable option",
            f"for {target_cls}.  The potential values for `type` and",
            "their corresponding type are:",
            *[f"\t- {k}: {v.__name__}" for k, v in possibilities.items()],
        ]
        self.possiblilites = possibilities
        super().__init__(target_cls, msg, child=None, obj=obj)


class ParameterOrderError(TypeCheckError):
    """The ``parameter_order`` attr contained too many and/or too few parameters

    Args:
        target_cls (type): the type with a malformed ``parameter_order`` attr
        too_few (Set[str]): parameters not in ``parameter_order``
        too_many (Set[str]): additional parameters in ``parameter_order`` that aren't
            in the constructor
    """

    def __init__(
        self,
        target_cls: type,
        too_few: Set[str],
        too_many: Set[str],
    ) -> None:
        msg = [
            f"{target_cls} parameter_order attribute, was missing parameters,",
            "indicated with a `-` and/or passed additional arguments",
            "indicated with a `+`",
        ]
        if too_few:
            missing = [f"\t- {k}" for k in too_few]
            msg.extend(missing)

        if too_many:
            added = [f"\t+ {k}" for k in too_many]
            msg.extend(added)

        self.too_few = too_few
        self.too_many = too_many
        super().__init__(target_cls, msg, child=None, obj=None)


class MalformedDependencyError(TypeCheckError):
    """:class:`~adorn.unit.parameter_value.Dependent` type was not provided all the necessary information.

    Args:
        target_cls (Type): The type with malformed dependency information
    """  # noqa: B950

    def __init__(self, target_cls: Type) -> None:
        msg = [
            f"{target_cls.cls} type was not provided all the necessary",
            "information at the type level.  Ensure that all necessary",
            "information was passed to the type.",
        ]
        super().__init__(target_cls, msg, child=None, obj=None)


class MissingLiteralError(TypeCheckError):
    """:class:`~adorn.unit.parameter_value.Dependent` type's first argument was not a ``typing.Literal``.

    Args:
        target_cls (Type): Type with a dependency that didn't have a ``typing.Literal``
    """  # noqa: B950

    def __init__(self, target_cls: Type) -> None:
        msg = [
            f"{target_cls.cls} requires it's last argument to be wrapped",
            "in a ``typing.Literal``",
        ]
        super().__init__(target_cls, msg, child=None, obj=None)


class UnaryLiteralError(TypeCheckError):
    """``typing.Literal`` that was passed more than one arg

    Args:
        target_cls (Type): Type with a dependency that had a ``typing.Literal``
            with more than one arg
    """

    def __init__(self, target_cls: Type) -> None:
        msg = [
            f"{target_cls.cls} requires it's last argument to be wrapped",
            "in a ``typing.Literal`` which is passed a single argument.",
        ]
        super().__init__(target_cls, msg, child=None, obj=None)


class MalformedLiteralError(TypeCheckError):
    """``typing.Literal`` argument wasn't of the correct type

    Args:
        target_cls (Type): the type which contained the problem ``typing.Literal``
        literal_type (Type): the required type of the ``typing.Literal``
            argument
        child (TypeCheckError): the error produced by the ``typing.Literal``
            argument
    """

    def __init__(
        self, target_cls: Type, literal_type: Type, child: TypeCheckError
    ) -> None:
        msg = [
            f"{target_cls.cls} requires it's last argument to be wrapped",
            f"in a ``typing.Literal`` which is of type {literal_type}",
        ]
        self.literal_type = literal_type
        super().__init__(target_cls, msg, child=child, obj=None)


class ExtraLiteralError(TypeCheckError):
    """``typing.Literal`` contains additional keys not specified in the constructor.

    Args:
        target_cls (Type): the type which contains the problem ``typing.Literal``
        extras (List[str]): the additional arguments specified in the
            ``typing.Literal`` argument
    """

    def __init__(self, target_cls: Type, extras: List[str]) -> None:
        msg = [
            f"{target_cls.cls}'s' ``typing.Literal`` arg contains additional keys",
            "that were not in the constructor",
            *[f"\t- {k}" for k in extras],
        ]
        self.extras = extras
        super().__init__(target_cls, msg, child=None, obj=None)


class TooDeepLiteralError(TypeCheckError):
    """``typing.Literal`` specified a dependency that goes beyond one layer deep

    An example would be `"a.b.c"`.

    Args:
        target_cls (Type): the type which contains the problem ``typing.Literal``
        bad_literal (List[str]): the dependency requests that went too deep
    """

    def __init__(self, target_cls: Type, bad_literal: List[str]) -> None:
        msg = [
            f"{target_cls.cls}'s' ``typing.Literal`` arg is not allowed to have",
            "dependencies that go beyond one layer deep, one period.",
            "The following dependencies were more than one layer deep:",
            *[f"\t- {k}" for k in bad_literal],
        ]
        self.bad_literal = bad_literal
        super().__init__(target_cls, msg, child=None, obj=None)


class MissingDependencyError(TypeCheckError):
    """``typing.Literal`` requested a dependency that doesn't exist in local state

    Args:
        target_cls (Type): the type which contains the problem ``typing.Literal``
        missing_dependency (Dict[str, str]): the dependency requests that didn't
            exist in the local state
    """

    def __init__(self, target_cls: Type, missing_dependency: Dict[str, str]) -> None:
        msg = [
            f"{target_cls.cls}'s' ``typing.Literal`` requested",
            "dependencies that were not in the local state.",
            "The following dependency requests were not in the local state:",
            *[f"\t- {k}: {v}" for k, v in missing_dependency.items()],
        ]
        self.missing_dependency = missing_dependency
        super().__init__(target_cls, msg, child=None, obj=None)


class AnumWrongTypeError(WrongTypeError):
    """Error when provided an ``obj`` of the wrong type for a :class:`~adorn.unit.anum.Anum`

    Args:
        target_cls (Anum): the requested wrapped enumeration
        obj (Any): caller provided object, that is not of type
            ``target_cls``
    """  # noqa: B950

    def __init__(self, target_cls: "Anum", obj: Any) -> "TypeCheckError":
        super().__init__(str, obj)
        self.target_cls = target_cls
        self.msg[0] = f"For the Anum, {self.target_cls}, " + self.msg[0]


class AnumMemberError(TypeCheckError):
    """The str specified doesn't match any of the members of ``target_cls``

    Args:
        target_cls (Anum): the requested wrapped enumeration
        obj (str): requested member that does not exist
    """

    def __init__(self, target_cls: "Anum", obj: str) -> None:
        self.members = target_cls.__members__
        msg = [
            f"For {target_cls}, a str specified a member,",
            f"{obj}, which is not an acceptable option",
            f"for {target_cls}.  The valid members",
            f"of {target_cls} are:",
            *[f"\t- {k}" for k in self.members.keys()],
        ]
        super().__init__(target_cls, msg, child=None, obj=obj)


class UserDictError(TypeCheckError):
    """Report an error during the from_obj step of :class:`~adorn.alter.dict_alter.UserDictAlter`

    Args:
        alter_type (Type): the type of ``Alter`` being performed
        target_cls (Parameter): the parameter the alter was trying to convert
            the ``obj`` into
        obj (Any): the alter request that produced an exception
        exception (Exception): the ``Exception`` produced from trying to convert ``obj``
            into the requested data.

    """  # noqa: B950

    def __init__(
        self, alter_type: Type, target_cls: "Parameter", obj: Any, exception: Exception
    ) -> None:
        self.alter_type = alter_type
        self.exception = exception
        msg = [
            f"An Alter of type {alter_type} was requested for",
            f"a parameter named {target_cls.parameter_name} of type {target_cls.cls}",
            "but an exception was caused when converting the obj:",
            f"{obj}",
            f"to type {target_cls.cls}.  The exception was:",
            f"{self.exception}",
        ]
        super().__init__(target_cls, msg, child=None, obj=obj)

    def __eq__(self, other) -> bool:
        if type(self) != type(other):
            return False
        return all(
            [
                self.target_cls == other.target_cls,
                self.msg[:-1] == other.msg[:-1],
                self.child == other.child,
                self.obj == other.obj,
                isinstance(self.exception, type(other.exception)),
            ]
        )
