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
import dataclasses

import pytest
from tests.conftest import ORCHESTRATOR
from tests.example import gym

from adorn.exception.type_check_error import AnumMemberError
from adorn.exception.type_check_error import KeyValueError
from adorn.exception.type_check_error import ParamError
from adorn.exception.type_check_error import UnRepresentedTypeError
from adorn.params import Params


@dataclasses.dataclass
class UnregisteredDataClass:
    """dataclass that isn't in the registry"""

    nope: bool = True


DATA_CLASS = gym.GymData()
CONTAIN_GET_LIST = [
    (gym.Workout, True),
    (None, False),
    (gym.Food, False),
    (UnregisteredDataClass, False),
]

WELLFORMED_LIST = [
    (
        gym.Workout,
        Params({"lift": "Squat", "reps": 1, "weight": 405.0}),
        gym.Workout(gym.Lift.Squat, 1, 405.0),
    ),
    (
        gym.Workout,
        Params({"lift": "Deadlift", "reps": 1, "weight": 495.0, "maxed": True}),
        gym.Workout(gym.Lift.Deadlift, 1, 495.0, True),
    ),
]


MALFORMED_LIST = [
    (
        UnregisteredDataClass,
        Params({}),
        UnRepresentedTypeError(UnregisteredDataClass, DATA_CLASS, Params({})),
    ),
    (
        gym.Workout,
        {"lift": "Squat", "reps": 1, "weight": 405.0},
        ParamError(gym.Workout, {"lift": "Squat", "reps": 1, "weight": 405.0}),
    ),
    (
        gym.Workout,
        Params({"lift": "squat", "reps": 1, "weight": 405.0}),
        KeyValueError(
            gym.Workout,
            {
                "lift": AnumMemberError(gym.Lift, "squat"),
            },
            Params({"lift": "squat", "reps": 1, "weight": 405.0}),
        ),
    ),
]


@pytest.fixture
def orchestrator():
    return ORCHESTRATOR


@pytest.fixture(params=CONTAIN_GET_LIST)
def contain_get(request):
    return request.param


@pytest.fixture(params=WELLFORMED_LIST)
def wellformed(request):
    return request.param


@pytest.fixture(params=MALFORMED_LIST)
def malformed(request):
    return request.param


@pytest.fixture()
def dataclass():
    return DATA_CLASS


def test_get(contain_get, dataclass):
    (target_cls, contains) = contain_get
    output = dataclass.get(target_cls, None)
    statement = (output == target_cls) if contains else (output is None)
    assert statement


def test_contains(contain_get, dataclass):
    (target_cls, contains) = contain_get
    output = dataclass.contains(target_cls, None)
    assert output == contains


def test_type_check_error(malformed, dataclass, orchestrator):
    target_cls, obj, error = malformed
    assert dataclass.type_check(target_cls, orchestrator, obj) == error


def test_type_check(wellformed, dataclass, orchestrator):
    target_cls, obj, *_ = wellformed
    assert dataclass.type_check(target_cls, orchestrator, obj) is None


def test_from_obj(wellformed, dataclass, orchestrator):
    target_cls, obj, target = wellformed
    assert dataclass.from_obj(target_cls, orchestrator, obj) == target
