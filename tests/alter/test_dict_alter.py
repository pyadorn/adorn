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
from os import environ

import pytest
from tests.conftest import ORCHESTRATOR

from adorn.alter.dict_alter import EnvDictAlter
from adorn.alter.dict_alter import UserDictAlter
from adorn.data.parameter import Parameter
from adorn.exception.type_check_error import UserDictError
from adorn.params import Params


CONTAINS = [
    (
        UserDictAlter(dict(a=None)),
        (
            Parameter(int, None, dict(), ""),
            None,
            Params({"type": "user_dict", "key": "a"}),
        ),
        True,
    ),
    (
        UserDictAlter(dict()),
        (
            Parameter(int, None, dict(), ""),
            None,
            Params({"type": "user_dict", "key": "a"}),
        ),
        False,
    ),
    (
        UserDictAlter(dict()),
        (Parameter(int, None, dict(), ""), None, Params({"type": "blah", "key": "a"})),
        False,
    ),
    (
        UserDictAlter(dict()),
        (Parameter(int, None, dict(), ""), None, {"type": "user_dict"}),
        False,
    ),
    (
        UserDictAlter(dict()),
        (None, None, Params({"type": "user_dict", "key": "a"})),
        False,
    ),
]

ALTER_OBJ = [
    (
        UserDictAlter({"USER": "abc", "PASSWORD": "120"}),
        {
            "target_cls": Parameter(str, None, dict(), ""),
            "obj": {"type": "user_dict", "key": "USER"},
        },
        "abc",
    ),
    (
        UserDictAlter({"USER": "abc", "PASSWORD": "120"}),
        {
            "target_cls": Parameter(int, None, dict(), ""),
            "obj": {"type": "user_dict", "key": "PASSWORD"},
        },
        120,
    ),
    (
        UserDictAlter({"USER": "abc", "PASSWORD": "120", "FLT": "3.4"}),
        {
            "target_cls": Parameter(float, None, dict(), ""),
            "obj": {"type": "user_dict", "key": "FLT"},
        },
        3.4,
    ),
    (
        UserDictAlter({"USER": "abc", "PASSWORD": "120", "FLT": "a"}),
        {
            "target_cls": Parameter(float, None, dict(), "b"),
            "obj": {"type": "user_dict", "key": "FLT"},
        },
        UserDictError(
            UserDictAlter,
            Parameter(float, None, dict(), "b"),
            {"type": "user_dict", "key": "FLT"},
            ValueError(),
        ),
    ),
]


@pytest.fixture
def orchestrator():
    return ORCHESTRATOR


@pytest.fixture(params=CONTAINS)
def contains(request):
    return request.param


@pytest.fixture(params=ALTER_OBJ)
def alter_obj(request):
    return request.param


def test_env_dict_alter_type_value():
    assert EnvDictAlter().type_value == "ENV"


def test_user_dict_alter_type_value():
    assert UserDictAlter(dict()).type_value == "user_dict"


def test_env_dict_environ():
    assert EnvDictAlter().user_dict == environ


def test_a_contains(contains):
    da, args, output = contains
    assert da.a_contains(*args) == output


def test_a_get(contains):
    da, args, output = contains
    get_output = da.a_get(*args)
    if output:
        assert isinstance(get_output, UserDictAlter)
    else:
        assert get_output is None


def test_alter_obj(alter_obj, orchestrator):
    alter, inputs, output = alter_obj
    inputs["orchestrator"] = orchestrator
    assert alter.alter_obj(**inputs) == output
