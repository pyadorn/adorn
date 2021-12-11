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
from adorn.exception.type_check_error import UnRepresentedTypeError


def test_contains(contains):
    (orchestrator, unit, _, typ) = contains
    assert unit.contains(typ, orchestrator)


def test_contains_false(unit_dne):
    (orchestrator, unit, target_cls, _) = unit_dne
    assert not unit.contains(target_cls, orchestrator)


def test_get(contains):
    (orchestrator, unit, target_cls, typ) = contains
    assert unit.get(typ, orchestrator) == target_cls


def test_get_none(unit_dne):
    (orchestrator, unit, target_cls, _) = unit_dne
    assert unit.get(target_cls, orchestrator) is None


def test_type_check(type_check_all):
    (orchestrator, unit, _, target_cls, v) = type_check_all
    assert unit.type_check(target_cls, orchestrator, v) is None


def test_type_check_wrong(type_check_wrong_all):
    (orchestrator, unit, _, target_cls, v, tv) = type_check_wrong_all
    assert isinstance(
        unit.type_check(target_cls, orchestrator, v),
        type(tv),
    )


def test_type_check_unrepresented(unit_dne):
    (orchestrator, unit, target_cls, obj) = unit_dne
    assert unit.type_check(target_cls, orchestrator, obj) == UnRepresentedTypeError(
        target_cls, unit, obj
    )


def test_from_obj(from_obj_all):
    (orchestrator, unit, _, target_cls, v, tv) = from_obj_all
    if isclass(tv) and issubclass(tv, TypeCheckError):
        with pytest.raises(tv):
            unit.from_obj(target_cls, orchestrator, v)
    else:
        assert unit.from_obj(target_cls, orchestrator, v) == tv


def test_from_obj_unrepresented(unit_dne):
    (orchestrator, unit, target_cls, obj) = unit_dne
    with pytest.raises(UnRepresentedTypeError):
        _ = unit.from_obj(target_cls, orchestrator, obj)
