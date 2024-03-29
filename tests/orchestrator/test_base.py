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


def test_contains(contains):
    (orchestrator, _, _, typ) = contains
    assert orchestrator.contains(typ)


def test_contains_false(orchestrator_dne):
    (orchestrator, typ, _) = orchestrator_dne
    assert not orchestrator.contains(typ)


def test_get(contains):
    (orchestrator, unit, _, typ) = contains
    assert type(orchestrator.get(typ)) == type(unit)


def test_get_none(orchestrator_dne):
    (orchestrator, typ, _) = orchestrator_dne
    with pytest.raises(TypeCheckError):
        _ = orchestrator.get(typ)


def test_type_check(type_check_all):
    (orchestrator, _, _, target_cls, v) = type_check_all
    assert orchestrator.type_check(target_cls, v) is None


def test_type_check_wrong(type_check_wrong_all):
    (orchestrator, _, _, target_cls, v, tv) = type_check_wrong_all
    assert isinstance(orchestrator.type_check(target_cls, v), type(tv))


def test_type_check_type_check_error(orchestrator_dne):
    (orchestrator, typ, obj) = orchestrator_dne
    with pytest.raises(TypeCheckError):
        _ = orchestrator.type_check(typ, obj)


def test_from_obj(from_obj_all):
    (orchestrator, _, _, target_cls, v, tv) = from_obj_all
    if isclass(tv) and issubclass(tv, TypeCheckError):
        with pytest.raises(tv):
            orchestrator.from_obj(target_cls, v)
    else:
        assert orchestrator.from_obj(target_cls, v) == tv


def test_from_obj_type_check_error(orchestrator_dne):
    (orchestrator, typ, obj) = orchestrator_dne
    with pytest.raises(TypeCheckError):
        _ = orchestrator.from_obj(typ, obj)


def test_a_get(a_orchestrator, a_get):
    cls, obj, output = a_get
    assert a_orchestrator.a_get(cls, obj) == output


def test_a_type_check(a_orchestrator, a_wellformed):
    cls, obj, _ = a_wellformed
    assert a_orchestrator.type_check(cls, obj) is None


def test_a_from_obj(a_orchestrator, a_wellformed):
    cls, obj, output_dict = a_wellformed
    output = a_orchestrator.from_obj(cls, obj)
    assert isinstance(output, cls)
    assert all(getattr(output, k) == v for k, v in output_dict.items())


def test_a_type_check_bad(a_orchestrator, a_malformed):
    cls, obj, output, a = a_malformed
    o = a_orchestrator.type_check(cls, obj)
    kv = o.key_values["reps"]
    assert kv == a
    assert type(o) == type(output)  # noqa: E721
    assert o.target_cls == output.target_cls
    assert list(o.key_values.keys()) == list(output.key_values.keys())


def test_a_from_obj_bad(a_orchestrator, a_malformed):
    cls, obj, _, output = a_malformed
    with pytest.raises(type(output)):
        a_orchestrator.from_obj(cls, obj)
