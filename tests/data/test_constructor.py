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
import inspect
from typing import List
from typing import Optional

import pytest
from tests.example import gym

from adorn.data.constructor import Constructor


@pytest.mark.parametrize(
    "input,parameters,constructor_type",
    [
        (gym.Apple, dict(), None),
        (
            gym.Beef,
            {
                "weight": inspect.Parameter(
                    "weight",
                    kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=float,
                ),
                "feed": inspect.Parameter(
                    "feed",
                    kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=gym.FeedType,
                    default=gym.FeedType.Corn,
                ),
            },
            None,
        ),
        (
            gym.Pork,
            {
                "weight": inspect.Parameter(
                    "weight",
                    kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=float,
                )
            },
            None,
        ),
        (
            gym.Child0,
            {
                "zero": inspect.Parameter(
                    "zero",
                    kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=List[str],
                ),
                "a": inspect.Parameter(
                    "a", kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=int
                ),
                "gp": inspect.Parameter(
                    "gp", kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=str
                ),
            },
            None,
        ),
        (
            gym.Child2,
            {
                "food": inspect.Parameter(
                    "food",
                    kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=Optional[gym.Food],
                ),
                "fruit": inspect.Parameter(
                    "fruit",
                    kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=gym.Fruit,
                ),
                "meat": inspect.Parameter(
                    "meat",
                    kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=gym.Meat,
                ),
                "b": inspect.Parameter(
                    "b",
                    default=True,
                    kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=bool,
                ),
                "gp": inspect.Parameter(
                    "gp", kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=str
                ),
                "workout": inspect.Parameter(
                    "workout",
                    default=None,
                    kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=Optional[gym.Workout],
                ),
            },
            None,
        ),
    ],
)
def test_constructor(input, parameters, constructor_type):
    obj = Constructor(input)
    assert obj.subclass == input
    assert obj.parameters == parameters
    assert obj.constructor_type == constructor_type
