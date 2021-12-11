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
from typing import List
from typing import Optional

from tests.example import gym
from tests.example.dne import _B

from adorn.data.constructor import Constructor
from adorn.exception.type_check_error import KeyValueDiffError
from adorn.exception.type_check_error import KeyValueError
from adorn.exception.type_check_error import ParameterOrderError
from adorn.exception.type_check_error import WrongTypeError
from adorn.params import Params
from adorn.unit.constructor_value import BaseConstructorValue
from adorn.unit.constructor_value import ConstructorValue


CONSTRUCTOR_VALUE_TYPES_MISMATCH = [
    (BaseConstructorValue, gym.Apple),
    (BaseConstructorValue, gym.Child0),
    (BaseConstructorValue, _B),
    (BaseConstructorValue, int),
]
CONSTRUCTOR_VALUE_TYPE_CHECK = [
    (
        BaseConstructorValue,
        Constructor(gym.Child0),
        Params({"type": "0", "zero": ["a"], "a": 1, "gp": "yes"}),
    ),
    (
        BaseConstructorValue,
        Constructor(gym.Child1),
        Params({"type": "1", "one": {0: [True]}, "a": 1, "gp": "yes"}),
    ),
    (BaseConstructorValue, Constructor(gym.Apple), Params({"type": "apple"})),
    (BaseConstructorValue, Constructor(gym.Avocado), Params({})),
]
CONSTRUCTOR_VALUE_TYPE_CHECK_WRONG = [
    (
        BaseConstructorValue,
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
        BaseConstructorValue,
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
    (
        BaseConstructorValue,
        Constructor(gym.Child0),
        Params({"type": "0", "zero": [1], "a": 1.1, "gp": "yes"}),
        KeyValueError(
            gym.Child0,
            {
                "zero": KeyValueError(List[str], {"0": WrongTypeError(str, 1)}, [1]),
                "a": WrongTypeError(int, 1.1),
            },
            Params({"type": "0", "zero": [1], "a": 1.1, "gp": "yes"}),
        ),
    ),
    (
        BaseConstructorValue,
        Constructor(gym.BadChild0),
        Params({"type": "bad_0", "gp": "a"}),
        ParameterOrderError(Constructor(gym.BadChild0), {"gp"}, {"b"}),
    ),
]
CONSTRUCTOR_VALUE_FROM_OBJ = [
    (
        BaseConstructorValue,
        Constructor(gym.Child0),
        Params({"type": "0", "zero": ["a"], "a": "1", "gp": "yes"}),
        gym.Child0(zero=["a"], a=1, gp="yes"),
    ),
    (
        BaseConstructorValue,
        Constructor(gym.Apple),
        Params({"type": "apple"}),
        gym.Apple(),
    ),
    (
        BaseConstructorValue,
        Constructor(gym.Child1),
        Params({"type": "1", "one": {"0": [1]}, "a": 1, "gp": "yes"}),
        gym.Child1(one={0: {True}}, a=1, gp="yes"),
    ),
]


CONSTRUCTOR_VALUE = ConstructorValue()

TYPES_MISMATCH = [(CONSTRUCTOR_VALUE, *i) for i in (CONSTRUCTOR_VALUE_TYPES_MISMATCH)]
TYPE_CHECK = [(CONSTRUCTOR_VALUE, *i) for i in (CONSTRUCTOR_VALUE_TYPE_CHECK)]
TYPE_CHECK_WRONG = [
    (CONSTRUCTOR_VALUE, *i) for i in (CONSTRUCTOR_VALUE_TYPE_CHECK_WRONG)
]
FROM_OBJ = [(CONSTRUCTOR_VALUE, *i) for i in (CONSTRUCTOR_VALUE_FROM_OBJ)]
