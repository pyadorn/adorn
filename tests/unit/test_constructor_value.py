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
import inspect
from typing import List, Optional

import pytest
from adorn.data.constructor import Constructor
from adorn.exception.type_check_error import (
    KeyValueDiffError,
    KeyValueError,
    ParameterOrderError,
    WrongTypeError,
)
from adorn.orchestrator.base import Base
from adorn.orchestrator.orchestrator import Orchestrator
from adorn.params import Params
from adorn.unit.constructor_value import BaseConstructorValue, ConstructorValue
from adorn.unit.parameter_value import ParameterValue
from adorn.unit.python import Python
from adorn.unit.value import Value

from tests.example import gym


def test_get_none():
    cv = ConstructorValue()
    assert cv.get(int, Orchestrator) is None


@pytest.mark.parametrize(
    "target_cls,obj,target",
    [
        (Constructor(gym.Avocado), Params({}), None),
        (
            Constructor(gym.Child0),
            Params({"type": "0", "zero": ["a"], "a": 1, "gp": "yes"}),
            None,
        ),
        (
            Constructor(gym.Child0),
            Params({"type": "0", "zero": ["a"], "a": 1}),
            {"gp": str},
        ),
        (
            Constructor(gym.Child2),
            Params({}),
            {
                "food": Optional[gym.Food],
                "fruit": gym.Fruit,
                "meat": gym.Meat,
                "gp": str,
            },
        ),
    ],
)
def test_get_kv_parameter(target_cls, obj, target):
    assert (
        ConstructorValue.get_kv(
            target_cls.parameters,
            lambda i: i.annotation,
            obj,
            {"self"},
            lambda i: i.default != inspect._empty,
        )
        == target
    )


@pytest.mark.parametrize(
    "target_cls,target",
    [
        (Constructor(gym.Child0), None),
        (Constructor(gym.Child2), None),
        (
            Constructor(gym.BadChild0),
            ParameterOrderError(Constructor(gym.BadChild0), {"gp"}, {"b"}),
        ),
    ],
)
def test_check_parameter_order(target_cls, target):
    assert ConstructorValue.check_parameter_order(target_cls=target_cls) == target


@pytest.mark.parametrize(
    "target_cls,obj,target",
    [
        (Constructor(gym.Avocado), Params({}), None),
        (
            Constructor(gym.Child0),
            Params({"type": "0", "zero": ["a"], "a": 1, "gp": "yes"}),
            None,
        ),
        (Constructor(gym.Avocado), Params({"extra": 1}), {"extra": int}),
        (
            Constructor(gym.Child0),
            Params({"type": "0", "zero": ["a"], "a": 1, "gp": "yes", "x": "abc"}),
            {"x": str},
        ),
    ],
)
def test_get_kv_obj(target_cls, obj, target):
    assert ConstructorValue.get_kv(obj, type, target_cls.parameters, {"type"}) == target


@pytest.mark.parametrize(
    "target_cls,obj,target",
    [
        (Constructor(gym.Avocado), Params({}), None),
        (
            Constructor(gym.Child0),
            Params({"type": "0", "zero": ["a"], "a": 1, "gp": "yes"}),
            None,
        ),
        (
            Constructor(gym.Child0),
            Params({"type": "0", "zero": ["a"], "a": 1, "gp": "yes", "x": "abc"}),
            KeyValueDiffError(
                gym.Child0,
                None,
                {"x": str},
                Params({"type": "0", "zero": ["a"], "a": 1, "gp": "yes", "x": "abc"}),
            ),
        ),
        (
            Constructor(gym.Child0),
            Params({"type": "0", "zero": ["a"], "a": 1}),
            KeyValueDiffError(
                gym.Child0,
                {"gp": str},
                None,
                Params({"type": "0", "zero": ["a"], "a": 1}),
            ),
        ),
        (
            Constructor(gym.Child2),
            Params({"type": "2", "x": "abc"}),
            KeyValueDiffError(
                gym.Child2,
                {
                    "gp": str,
                    "food": Optional[gym.Food],
                    "fruit": gym.Fruit,
                    "meat": gym.Meat,
                },
                {"x": str},
                Params({"type": "2", "x": "abc"}),
            ),
        ),
    ],
)
def test_parameter_consistency(target_cls, obj, target):
    assert ConstructorValue.parameter_consistency(target_cls, obj) == target


@pytest.mark.parametrize(
    "target_cls,obj,target",
    [
        (Constructor(gym.Avocado), Params({}), None),
        (
            Constructor(gym.Child0),
            Params({"type": "0", "zero": ["a"], "a": 1, "gp": "yes"}),
            None,
        ),
        (
            Constructor(gym.Child0),
            Params({"type": "0", "zero": ["a"], "a": 1.1, "gp": "yes"}),
            KeyValueError(
                gym.Child0,
                {"a": WrongTypeError(int, 1.1)},
                Params({"type": "0", "zero": ["a"], "a": 1.1, "gp": "yes"}),
            ),
        ),
        (
            Constructor(gym.Child0),
            Params({"type": "0", "zero": [1], "a": 1.1, "gp": "yes"}),
            KeyValueError(
                gym.Child0,
                {
                    "zero": KeyValueError(
                        List[str], {"0": WrongTypeError(str, 1)}, [1]
                    ),
                    "a": WrongTypeError(int, 1.1),
                },
                Params({"type": "0", "zero": [1], "a": 1.1, "gp": "yes"}),
            ),
        ),
    ],
)
def test_dict_type_check(target_cls, obj, target):
    orchestrator = Base([ParameterValue(), Value(), Python(), gym.Gym()])
    result = ConstructorValue.dict_type_check(
        target_cls=target_cls, orchestrator=orchestrator, obj=obj
    )
    assert result == target


def test_type_check_wrong_type():
    cv = ConstructorValue()
    assert cv.type_check(int, None, 1) == WrongTypeError(Constructor, int)


def test_from_obj_raise():
    orchestrator = Base([ParameterValue(), Value(), Python(), gym.Gym()])
    with pytest.raises(ParameterOrderError):
        BaseConstructorValue._from_obj(
            Constructor(gym.BadChild0),
            orchestrator=orchestrator,
            obj=Params({"type": "bad_0", "gp": "a"}),
        )
