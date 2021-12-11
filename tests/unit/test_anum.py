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
from enum import auto
from enum import Enum

import pytest
from tests.example import gym

from adorn.exception.type_check_error import AnumMemberError
from adorn.exception.type_check_error import AnumWrongTypeError
from adorn.exception.type_check_error import UnRepresentedTypeError


class UnregistereEnum(Enum):
    """Enum that isn't in the registry"""

    A = auto()


ANUM = gym.Gymnum()
CONTAIN_GET_LIST = [
    (gym.FeedType, True),
    (None, False),
    (gym.Food, False),
    (UnregistereEnum, False),
]

WELLFORMED_LIST = [
    (gym.FeedType, "Grass", gym.FeedType.Grass),
    (gym.FeedType, "Unknown", gym.FeedType.Unknown),
    (gym.FeedType, "Corn", gym.FeedType.Corn),
]


MALFORMED_LIST = [
    (UnregistereEnum, "A", UnRepresentedTypeError(UnregistereEnum, ANUM, "A")),
    (gym.FeedType, 1, AnumWrongTypeError(gym.FeedType, 1)),
    (gym.FeedType, "Gass", AnumMemberError(gym.FeedType, "Gass")),
]


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
def anum():
    return ANUM


def test_get(contain_get, anum):
    (target_cls, contains) = contain_get
    output = anum.get(target_cls, None)
    statement = (output == target_cls) if contains else (output is None)
    assert statement


def test_contains(contain_get, anum):
    (target_cls, contains) = contain_get
    output = anum.contains(target_cls, None)
    assert output == contains


def test_type_check_error(malformed, anum):
    target_cls, obj, error = malformed
    assert anum.type_check(target_cls, None, obj) == error


def test_type_check(wellformed, anum):
    target_cls, obj, *_ = wellformed
    assert anum.type_check(target_cls, None, obj) is None


def test_from_obj(wellformed, anum):
    target_cls, obj, target = wellformed
    assert anum.from_obj(target_cls, None, obj) == target
