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
from sys import version_info
from typing import Dict

if (version_info.major > 3) or (version_info.major == 3 and version_info.minor >= 8):
    from typing import Literal
else:
    from typing_extensions import Literal

from adorn.data.parameter import Parameter
from adorn.unit.parameter_value import DependentFromObj

from tests.example import gym


def test_parameter():
    parameter = Parameter(Dict[str, int], float, {"a": 1}, "blah")
    assert parameter.origin == dict
    assert parameter.args == (str, int)


def test_parameter_no_origin_args():
    parameter = Parameter(int, float, {"a": 1}, "blahs")
    assert parameter.origin is None
    assert parameter.args is None


def test___eq__():
    assert Parameter(
        DependentFromObj[gym.DMO, Literal[{"dne_in_constructor": "dlc.data_dim"}]],
        gym.BLIM,
        {"dlc": "garbage"},
        "mo",
    ) == Parameter(
        DependentFromObj[gym.DMO, Literal[{"dne_in_constructor": "dlc.data_dim"}]],
        gym.BLIM,
        {"dlc": "garbage"},
        "mo",
    )


def test_normal___eq__():
    assert Parameter(gym.Child0, gym.BLIM, {"dlc": "garbage"}, "mo") == Parameter(
        gym.Child0, gym.BLIM, {"dlc": "garbage"}, "mo"
    )


def test_normal_not___eq__():
    assert Parameter(gym.Child0, gym.BLIM, {"dlc": "garbage"}, "mo") != Parameter(
        gym.Child1, gym.BLIM, {"dlc": "garbage"}, "mo"
    )


def test_not___eq__():
    # missing m, data_di
    assert Parameter(
        DependentFromObj[gym.DMO, Literal[{"dne_in_constructor": "dlc.data_di"}]],
        gym.BLIM,
        {"dlc": "garbage"},
        "mo",
    ) != Parameter(
        DependentFromObj[gym.DMO, Literal[{"dne_in_constructor": "dlc.data_dim"}]],
        gym.BLIM,
        {"dlc": "garbage"},
        "mo",
    )
