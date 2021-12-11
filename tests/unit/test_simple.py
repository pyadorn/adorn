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
from adorn.orchestrator.orchestrator import Orchestrator
from adorn.unit.simple import Simple


def test__contains():
    assert not Simple._contains(int, Orchestrator)


def test__type_check():
    assert Simple._type_check(int, Orchestrator, 1) is None


def test__from_obj():
    assert Simple._from_obj(int, Orchestrator, 1) is None
