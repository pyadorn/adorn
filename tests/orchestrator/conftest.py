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
import pytest
from tests.example import gym

from adorn.alter.dict_alter import UserDictAlter
from adorn.data.constructor import Constructor
from adorn.data.parameter import Parameter
from adorn.exception.type_check_error import KeyValueError
from adorn.exception.type_check_error import UserDictError
from adorn.orchestrator.base import Base
from adorn.params import Params
from adorn.unit.constructor_value import ConstructorValue
from adorn.unit.parameter_value import ParameterValue
from adorn.unit.python import Python
from adorn.unit.value import Value

A_ORCHESTRATOR = Base(
    [
        Value(),
        ParameterValue(),
        ConstructorValue(),
        Python(),
        gym.Gymnum(),
        gym.GymData(),
        gym.Gym(),
        gym.Ambig(),
    ],
    [
        UserDictAlter({"a": 0, "b": 1}),
        UserDictAlter({"c": 2, "d": 3, "e": 1, "f": "a"}),
    ],
)


A_GET = [
    (
        Parameter(int, gym.Workout, dict(), "reps"),
        Params({"type": "user_dict", "key": "a"}),
        A_ORCHESTRATOR.alters[0],
    ),
    (
        Parameter(int, gym.Workout, dict(), "reps"),
        Params({"type": "user_dict", "key": "c"}),
        A_ORCHESTRATOR.alters[1],
    ),
    (
        Parameter(int, gym.Workout, dict(), "reps"),
        {"type": "user_dict", "key": "c"},
        None,
    ),
]

A_WELLFORMED = [
    (
        gym.Workout,
        Params(
            {"lift": "Squat", "weight": 10.0, "reps": {"type": "user_dict", "key": "a"}}
        ),
        {"reps": 0},
    ),
    (
        gym.Workout,
        Params(
            {"lift": "Squat", "weight": 10.0, "reps": {"type": "user_dict", "key": "d"}}
        ),
        {"reps": 3},
    ),
    (
        gym.Workout,
        Params(
            {
                "lift": "Squat",
                "weight": 10.0,
                "reps": {"type": "user_dict", "key": "a"},
                "maxed": {"type": "user_dict", "key": "e"},
            }
        ),
        {"reps": 0, "maxed": True},
    ),
]


REP_ERROR = UserDictError(
    UserDictAlter,
    Parameter(
        int,
        Constructor(gym.Workout),
        Params(
            {"lift": "Squat", "weight": 10.0, "reps": {"type": "user_dict", "key": "f"}}
        ),
        "reps",
    ),
    Params({"type": "user_dict", "key": "f"}, history="reps."),
    ValueError(),
)

A_MALFORMED = [
    (
        gym.Workout,
        Params(
            {"lift": "Squat", "weight": 10.0, "reps": {"type": "user_dict", "key": "f"}}
        ),
        KeyValueError(
            gym.Workout,
            {"reps": REP_ERROR},
            Params(
                {
                    "lift": "Squat",
                    "weight": 10.0,
                    "reps": {"type": "user_dict", "key": "f"},
                }
            ),
        ),
        REP_ERROR,
    ),
]


@pytest.fixture
def a_orchestrator():
    return A_ORCHESTRATOR


@pytest.fixture(params=A_GET)
def a_get(request):
    return request.param


@pytest.fixture(params=A_WELLFORMED)
def a_wellformed(request):
    return request.param


@pytest.fixture(params=A_MALFORMED)
def a_malformed(request):
    return request.param
