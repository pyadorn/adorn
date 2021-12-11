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
from itertools import chain

import pytest
from tests.example import gym
from tests.example.dne import _B
from tests.example.dne import _C
from tests.unit import conftest as unit
from tests.unit import constructor_value_examples
from tests.unit import parameter_value_examples
from tests.unit import python_examples
from tests.unit import value_examples

from adorn.orchestrator.base import Base
from adorn.unit.constructor_value import ConstructorValue
from adorn.unit.parameter_value import ParameterValue
from adorn.unit.python import Python
from adorn.unit.value import Value

ORCHESTRATOR = Base(
    [Value(), ParameterValue(), ConstructorValue(), Python(), gym.Gym(), gym.Ambig()]
)

TYPES = [
    (ORCHESTRATOR, *i)
    for i in (
        value_examples.TYPES
        + python_examples.TYPES
        + parameter_value_examples.TYPES
        + unit.TYPES
    )
]
TYPES_MISMATCH = [
    (ORCHESTRATOR, *i)
    for i in (
        value_examples.TYPES_MISMATCH
        + python_examples.TYPES_MISMATCH
        + parameter_value_examples.TYPES_MISMATCH
        + constructor_value_examples.TYPES_MISMATCH
        + unit.TYPES_MISMATCH
    )
]
TYPE_CHECK = [
    (ORCHESTRATOR, *i)
    for i in (
        value_examples.TYPE_CHECK
        + python_examples.TYPE_CHECK
        + parameter_value_examples.TYPE_CHECK
        + constructor_value_examples.TYPE_CHECK
        + unit.TYPE_CHECK
    )
]
TYPE_CHECK_WRONG = [
    (ORCHESTRATOR, *i)
    for i in (
        value_examples.TYPE_CHECK_WRONG
        + python_examples.TYPE_CHECK_WRONG
        + parameter_value_examples.TYPE_CHECK_WRONG
        + constructor_value_examples.TYPE_CHECK_WRONG
        + unit.TYPE_CHECK_WRONG
    )
]
FROM_OBJ = [
    (ORCHESTRATOR, *i)
    for i in (
        value_examples.FROM_OBJ
        + python_examples.FROM_OBJ
        + parameter_value_examples.FROM_OBJ
        + constructor_value_examples.FROM_OBJ
        + unit.FROM_OBJ
    )
]
TYPE_CHECK_WRONG_SPECIAL = [
    (ORCHESTRATOR, *i) for i in (python_examples.TYPE_CHECK_WRONG_SPECIAL)
]
DNE_LIST = [
    (ORCHESTRATOR, *i) for i in (python_examples.DNE_LIST + python_examples.DNE_LIST)
]

ORCHESTRATOR_DNE_LIST = [
    (ORCHESTRATOR, *i)
    for i in list(
        chain(
            *[
                [(_B, i) for i in ["a", 100, True, 1.1]],
                [(_C, i) for i in ["asdads dadf", -100, False, -3.14]],
            ]
        )
    )
]


@pytest.fixture(
    params=TYPES,
)
def contains(request):
    return request.param


@pytest.fixture(
    params=TYPES_MISMATCH,
)
def contains_mismatch(request):
    return request.param


@pytest.fixture(
    params=TYPE_CHECK,
)
def type_check(request):
    return request.param


@pytest.fixture(
    params=TYPE_CHECK + [(ORCHESTRATOR, *i) for i in unit.TYPE_CHECK_NO_UNDER]
)
def type_check_all(request):
    return request.param


@pytest.fixture(
    params=TYPE_CHECK_WRONG,
)
def type_check_wrong(request):
    return request.param


@pytest.fixture(
    params=TYPE_CHECK_WRONG
    + [(ORCHESTRATOR, *i) for i in unit.TYPE_CHECK_WRONG_NO_UNDER]
)
def type_check_wrong_all(request):
    return request.param


@pytest.fixture(
    params=TYPE_CHECK_WRONG_SPECIAL,
)
def type_check_wrong_special(request):
    return request.param


@pytest.fixture(params=FROM_OBJ)
def from_obj(request):
    return request.param


@pytest.fixture(params=FROM_OBJ + [(ORCHESTRATOR, *i) for i in unit.FROM_OBJ_NO_UNDER])
def from_obj_all(request):
    return request.param


@pytest.fixture(params=DNE_LIST)
def unit_dne(request):
    return request.param


@pytest.fixture(params=ORCHESTRATOR_DNE_LIST)
def orchestrator_dne(request):
    return request.param
