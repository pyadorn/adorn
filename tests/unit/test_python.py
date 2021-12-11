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

from adorn.exception.configuration_error import ConfigurationError
from adorn.exception.type_check_error import WrongTypeError
from adorn.unit.python import BuiltIn
from adorn.unit.python import Int
from adorn.unit.python import Python


@pytest.mark.parametrize("i", [0, 1, 2, -1, -2])
def test_int_addition_checks(i):
    assert Int.additional_checks(None, i) is None


@pytest.mark.parametrize("i", [True, False])
def test_int_addition_checks_wrong(i):
    assert Int.additional_checks(None, i) == WrongTypeError(int, i)


def test_additional_checks():
    assert BuiltIn.additional_checks(None, 0) is None


def test_cant_use_same_name_twice():
    with pytest.raises(ConfigurationError):
        Python.register("int")(Int)
