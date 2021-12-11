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
from sys import version_info
from typing import Dict
from typing import List
from typing import Tuple

if (version_info.major > 3) or (version_info.major == 3 and version_info.minor >= 8):
    from typing import Literal
else:
    from typing_extensions import Literal

import pytest
from tests.example import gym

from adorn.data.parameter import Parameter
from adorn.exception.type_check_error import ComplexTypeMismatchError
from adorn.exception.type_check_error import ExtraLiteralError
from adorn.exception.type_check_error import HashableError
from adorn.exception.type_check_error import KeyValueDiffError
from adorn.exception.type_check_error import KeyValueError
from adorn.exception.type_check_error import MalformedDependencyError
from adorn.exception.type_check_error import MalformedLiteralError
from adorn.exception.type_check_error import MissingDependencyError
from adorn.exception.type_check_error import MissingLiteralError
from adorn.exception.type_check_error import ParamError
from adorn.exception.type_check_error import ParameterOrderError
from adorn.exception.type_check_error import TooDeepLiteralError
from adorn.exception.type_check_error import TupleArgLenError
from adorn.exception.type_check_error import TypeCheckError
from adorn.exception.type_check_error import UnaryLiteralError
from adorn.exception.type_check_error import UnRepresentedTypeError
from adorn.exception.type_check_error import WrongTypeError
from adorn.params import Params
from adorn.unit.python import BuiltIn, Python
from adorn.unit.parameter_value import DependentTypeCheck


def test_to_str():
    tc = TypeCheckError(int, ["Failed", "to", "make", "int"])
    assert tc.to_str() == "Failed\nto\nmake\nint"
    for i in ["\t", "\t\t", "\t\t\t"]:
        assert tc.to_str(i) == f"\n{i}Failed\n{i}to\n{i}make\n{i}int"


def test_to_str_child():
    tc_str = TypeCheckError(str, ["a", "b"])
    tc_int = TypeCheckError(int, ["c", "d", "\te"], tc_str)
    tc_bool = TypeCheckError(bool, ["f", "g"], tc_int)

    assert tc_bool.to_str() == "f\ng\n\tc\n\td\n\t\te\n\t\ta\n\t\tb"
    for i in ["\t", "\t\t", "\t\t\t"]:
        assert (
            tc_bool.to_str(i)
            == f"\n{i}f\n{i}g\n\t{i}c\n\t{i}d\n\t\t{i}e\n\t\t{i}a\n\t\t{i}b"
        )


def test___repr__():
    tc_str = TypeCheckError(str, ["a", "b"])
    tc_int = TypeCheckError(int, ["c", "d", "\te"], tc_str)
    tc_bool = TypeCheckError(bool, ["f", "g"], tc_int)
    assert repr(tc_bool) == "f\ng\n\tc\n\td\n\t\te\n\t\ta\n\t\tb"
    assert str(tc_bool) == "f\ng\n\tc\n\td\n\t\te\n\t\ta\n\t\tb"

    assert repr(tc_int) == "c\nd\n\te\n\ta\n\tb"
    assert str(tc_int) == "c\nd\n\te\n\ta\n\tb"

    assert repr(tc_str) == "a\nb"
    assert str(tc_str) == "a\nb"


def test___eq__():
    tc_str = TypeCheckError(str, ["a", "b"])
    tc_str_prime = TypeCheckError(str, ["a", "b"])
    tc_str_child = TypeCheckError(str, ["a", "b"], child=tc_str)
    tc_str_msg = TypeCheckError(str, ["a"])
    tc_int = TypeCheckError(int, ["c", "d", "\te"], tc_str)
    assert tc_str == tc_str
    assert tc_str == tc_str_prime
    assert tc_str != tc_str_child
    assert tc_str != tc_str_msg
    assert tc_str_child != tc_str_msg
    assert tc_str != tc_int


def test_raise():
    for i in [
        TypeCheckError(str, ["s"]),
        WrongTypeError(str, 0),
        UnRepresentedTypeError(int, Python, None),
    ]:
        with pytest.raises(type(i)):
            raise i


def test_wrong_type_error():
    wte = WrongTypeError(str, 100)
    assert wte.target_cls == str
    assert wte.obj == 100
    assert wte.child is None
    assert wte.msg == [
        "Expected an object of type str,\n ",
        "but received an object of type ",
        "int\nwith a value of:",
        "\n\t100",
    ]


def test_unrepresented_type_error():
    ute = UnRepresentedTypeError(int, Python(), "abc")
    assert ute.target_cls == int
    assert ute.obj == "abc"
    assert ute.child is None
    assert ute.msg == [
        ("Requested type: int with an object of type:" "str"),
        "with a value of:",
        "abc",
        "didn't match any subtype of Python",
    ]


def test_key_value_error():
    tc_str = TypeCheckError(str, ["a", "b"])
    tc_bool = TypeCheckError(bool, ["f", "g"])
    obj = [tc_str, tc_bool]
    key_values = dict(enumerate(obj))
    kve = KeyValueError(List[int], key_values=key_values, obj=["str", True, 1])
    assert kve.msg == [
        "Failed to construct typing.List[int] because of the following values:",
        "\t-0: \n\t\ta\n\t\tb",
        "\t-1: \n\t\tf\n\t\tg",
    ]


def test_hashable_error():
    he = HashableError(int, BuiltIn, 0)
    assert he.obj == 0
    assert he.target_cls == int
    assert he.child is None
    assert he.msg == [
        "Failed to construct <class 'int'>, because <class 'int'>",
        "is not hashable.  You may need to alter the hashable attr of",
        "BuiltIn or use a type that is hashable",
    ]


def test_tuple_arg_len_error():
    tale = TupleArgLenError(Tuple[int, str], (1,))
    assert tale.obj == (1,)
    assert tale.target_cls == Tuple[int, str]
    assert tale.child is None
    assert tale.msg == [
        f"Failed to create a {Tuple[int, str]} because 2 args were",
        "expected but only 1 were received.",
        f"obj had a value of {(1,)}",
    ]


def test_param_error():
    pe = ParamError(int, "abc")
    assert pe.target_cls == int
    assert pe.child is None
    assert pe.obj == "abc"
    assert pe.msg == [
        "For int, expected a Params object",
        "but received an object of type str",
    ]


def test_key_value_difference_error():
    kvde = KeyValueDiffError(int, {"type": str, "name": bool}, {"a": float}, 20)
    assert kvde.target_cls == int
    assert kvde.child is None
    assert kvde.obj == 20
    assert kvde.msg == [
        f"{int} was missing arguments, indicated with a `-`",
        "and/or passed additional arguments indicated with a `+`",
        "\t- type: str",
        "\t- name: bool",
        "\t+ a: float",
    ]


def test_complex_type_mismatch_error():
    ctme = ComplexTypeMismatchError(str, {"a": int, "b": bool}, Params({}))
    assert ctme.target_cls == str
    assert ctme.child is None
    assert ctme.obj == Params({})
    assert ctme.msg == [
        f"For {str}, a Params object specified a `type`",
        f"of {None}, which is not an acceptable option",
        f"for {str}.  The potential values for `type` and",
        "their corresponding type are:",
        "\t- a: int",
        "\t- b: bool",
    ]


def test_parameter_order():
    poe = ParameterOrderError(int, {"a", "b"}, {"0"})
    assert poe.target_cls == int
    assert poe.obj is None
    assert poe.child is None
    assert len(poe.msg) == 6
    assert poe.msg[:3] == [
        f"{int} parameter_order attribute, was missing parameters,",
        "indicated with a `-` and/or passed additional arguments",
        "indicated with a `+`",
    ]
    assert all(i in poe.msg[3:] for i in ["\t- a", "\t- b", "\t+ 0"])


def test_malformed_dependency_error():
    dtc = DependentTypeCheck[gym.Pork, Literal[{"weight": "a.w"}]]
    parameter = Parameter(dtc, gym.Child2, {"a": {"w": 1.0}}, "meat")
    output = MalformedDependencyError(parameter)
    assert isinstance(output, MalformedDependencyError)
    assert output.obj is None
    assert output.child is None
    assert output.target_cls == parameter
    assert output.msg == [
        f"{dtc} type was not provided all the necessary",
        "information at the type level.  Ensure that all necessary",
        "information was passed to the type.",
    ]


def test_missing_literal_error():
    dtc = DependentTypeCheck[gym.Pork, None]
    parameter = Parameter(dtc, gym.Child2, {"a": {"w": 1.0}}, "meat")
    output = MissingLiteralError(parameter)
    assert isinstance(output, MissingLiteralError)
    assert output.obj is None
    assert output.child is None
    assert output.target_cls == parameter
    assert output.msg == [
        f"{dtc} requires it's last argument to be wrapped",
        "in a ``typing.Literal``",
    ]


def test_unary_literal_error():
    dtc = DependentTypeCheck[gym.Pork, Literal[{"weight": "a.w"}, True]]
    parameter = Parameter(dtc, gym.Child2, {"a": {"w": 1.0}}, "meat")
    output = UnaryLiteralError(parameter)
    assert isinstance(output, UnaryLiteralError)
    assert output.obj is None
    assert output.child is None
    assert output.target_cls == parameter
    assert output.msg == [
        f"{dtc} requires it's last argument to be wrapped",
        "in a ``typing.Literal`` which is passed a single argument.",
    ]


def test_malformed_literal_error():
    dtc = DependentTypeCheck[gym.Pork, Literal[True]]
    dct_type = Dict[str, str]
    wte = WrongTypeError(dct_type, True)

    parameter = Parameter(dtc, gym.Child2, {"a": {"w": 1.0}}, "meat")
    output = MalformedLiteralError(parameter, dct_type, wte)
    assert isinstance(output, MalformedLiteralError)
    assert output.obj is None
    assert output.child == wte
    assert output.target_cls == parameter
    assert output.msg == [
        f"{dtc} requires it's last argument to be wrapped",
        f"in a ``typing.Literal`` which is of type {dct_type}",
    ]


def test_extra_literal_error():
    dtc = DependentTypeCheck[gym.Pork, Literal[{"weight": "a.w", "a": "a"}]]
    parameter = Parameter(dtc, gym.Child2, {"a": {"w": 1.0}}, "meat")
    output = ExtraLiteralError(parameter, ["a"])
    assert output.obj is None
    assert output.child is None
    assert output.target_cls == parameter
    assert output.msg == [
        f"{dtc}'s' ``typing.Literal`` arg contains additional keys",
        "that were not in the constructor",
        "\t- a",
    ]


def test_too_deep_literal_error():
    dtc = DependentTypeCheck[gym.Pork, Literal[{"weight": "a.w.b"}]]
    parameter = Parameter(dtc, gym.Child2, {"a": {"w": 1.0}}, "meat")
    output = TooDeepLiteralError(parameter, ["a.w.b"])
    assert output.obj is None
    assert output.child is None
    assert output.target_cls == parameter
    assert output.msg == [
        f"{dtc}'s' ``typing.Literal`` arg is not allowed to have",
        "dependencies that go beyond one layer deep, one period.",
        "The following dependencies were more than one layer deep:",
        "\t- a.w.b",
    ]


def test_missing_dependency_error():
    dtc = DependentTypeCheck[gym.Pork, Literal[{"weight": "a.c"}]]
    parameter = Parameter(dtc, gym.Child2, {"a": {"w": 1.0}}, "meat")
    output = MissingDependencyError(parameter, {"weight": "a.c"})
    assert output.obj is None
    assert output.child is None
    assert output.target_cls == parameter
    assert output.msg == [
        f"{dtc}'s' ``typing.Literal`` requested",
        "dependencies that were not in the local state.",
        "The following dependency requests were not in the local state:",
        "\t- weight: a.c",
    ]
