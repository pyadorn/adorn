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
from inspect import isclass

import pytest
from adorn.exception.type_check_error import TypeCheckError

from tests.example import gym


def test__contains(contains):
    (orchestrator, _, target_cls, typ) = contains
    assert target_cls._contains(typ, orchestrator)


def test__contains_false(contains_mismatch):
    orchestrator, _, target_cls, typ = contains_mismatch
    assert not target_cls._contains(typ, orchestrator)


def test__type_check(type_check):
    (orchestrator, _, cls, target_cls, v) = type_check
    nu_cls = target_cls if issubclass(cls, gym.Gym) else cls
    assert nu_cls._type_check(target_cls, orchestrator, v) is None


def test__type_check_wrong(type_check_wrong):
    (orchestrator, _, cls, target_cls, v, tv) = type_check_wrong
    nu_cls = target_cls if issubclass(cls, gym.Gym) else cls
    assert nu_cls._type_check(target_cls, orchestrator, v) == tv


def test__from_obj(from_obj):
    (orchestrator, _, cls, target_cls, v, tv) = from_obj
    nu_cls = target_cls if issubclass(cls, gym.Gym) else cls
    if isclass(tv) and issubclass(tv, TypeCheckError):
        with pytest.raises(tv):
            nu_cls._from_obj(target_cls, orchestrator, v)
    else:
        assert nu_cls._from_obj(target_cls, orchestrator, v) == tv


def test__type_check_wrong_special(type_check_wrong_special):
    (orchestrator, _, cls, target_cls, v, tv) = type_check_wrong_special
    assert cls._type_check(target_cls, orchestrator, v) == tv
