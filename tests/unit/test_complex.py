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
from typing import Dict
from typing import List

import pytest
from tests.conftest import ORCHESTRATOR
from tests.example import gym
from tests.example.dne import _B

from adorn.exception.configuration_error import ConfigurationError
from adorn.exception.type_check_error import ComplexTypeMismatchError
from adorn.exception.type_check_error import ParamError
from adorn.exception.type_check_error import UnRepresentedTypeError
from adorn.orchestrator.base import Base
from adorn.params import Params


@pytest.mark.parametrize(
    "input,target",
    [
        (
            gym.GrandParent,
            {
                "0": gym.Child0,
                "1": gym.Child1,
                "2": gym.Child2,
                "beef_2": gym.BeefChild2,
                "bad_0": gym.BadChild0,
            },
        ),
        (gym.ParentA, {"0": gym.Child0, "1": gym.Child1}),
        (gym.ParentB, {"2": gym.Child2, "beef_2": gym.BeefChild2}),
        (gym.Child0, {"0": gym.Child0}),
        (gym.Meat, {"beef": gym.Beef, "pork": gym.Pork}),
        (gym.Beef, {"beef": gym.Beef}),
        (
            gym.Depth,
            {"da1": gym.DA1, "da2": gym.DA2, "da0a": gym.DA0A, "da1a": gym.DA1A},
        ),
        (gym.DA, {"da1": gym.DA1, "da2": gym.DA2, "da0a": gym.DA0A, "da1a": gym.DA1A}),
        (gym.DA1, {"da1": gym.DA1, "da1a": gym.DA1A}),
    ],
)
def test_get_instantiate_children(input, target):
    assert input.get_instantiate_children() == target


@pytest.mark.parametrize(
    "input,target",
    [
        (gym.GrandParent, None),
        (gym.ParentA, [gym.GrandParent]),
        (gym.Child0, gym.ParentA),
        (gym.Food, None),
        (gym.Meat, [gym.Food]),
    ],
)
def test_get_direct_parent(input, target):
    assert input.get_direct_parent() == target


@pytest.mark.parametrize(
    "input,target",
    [
        (gym.GrandParent, [gym.ParentA, gym.ParentB, gym.BadParent]),
        (gym.ParentA, []),
        (gym.Food, [gym.Meat, gym.Fruit]),
        (gym.Fruit, []),
        (gym.Depth, [gym.DA]),
        (gym.DA, [gym.DA0, gym.DA1]),
    ],
)
def test_get_intermediate_children(input, target):
    assert input.get_intermediate_children() == target


@pytest.mark.parametrize(
    "input,target",
    [
        (gym.Child0, "0"),
        (gym.Child1, "1"),
        (gym.Child2, "2"),
        (gym.Beef, "beef"),
        (gym.Pork, "pork"),
        (gym.Apple, "apple"),
        (gym.Avocado, "avocado"),
    ],
)
def test_name(input, target):
    assert input.name() == target


@pytest.mark.parametrize(
    "input", [gym.Food, gym.Fruit, gym.Meat, gym.GrandParent, gym.ParentA, gym.ParentB]
)
def test_name_exception(input):
    with pytest.raises(Exception):
        input.name()


@pytest.mark.parametrize(
    "input,name,target",
    [
        (gym.GrandParent, "0", gym.Child0),
        (gym.ParentA, "0", gym.Child0),
        (gym.Child0, "0", gym.Child0),
        (gym.Child0, None, gym.Child0),
        (gym.GrandParent, "2", gym.Child2),
        (gym.ParentB, "2", gym.Child2),
        (gym.Child2, "2", gym.Child2),
        (gym.Child2, None, gym.Child2),
        (gym.Food, "apple", gym.Apple),
        (gym.Fruit, "apple", gym.Apple),
        (gym.Apple, "apple", gym.Apple),
        (gym.Apple, None, gym.Apple),
    ],
)
def test_resolve_class_name(input, name, target):
    assert input.resolve_class_name(name) == target


@pytest.mark.parametrize(
    "input,target",
    [
        (
            gym.GrandParent,
            [gym.BadChild0, gym.Child2, gym.BeefChild2, gym.Child0, gym.Child1],
        ),
        (gym.ParentA, [gym.Child0, gym.Child1]),
        (gym.ParentB, [gym.Child2, gym.BeefChild2]),
        (gym.Child2, [gym.Child2, gym.BeefChild2]),
        (gym.BeefChild2, [gym.BeefChild2]),
        (gym.Child0, [gym.Child0]),
        (gym.Meat, [gym.Beef, gym.Pork]),
        (gym.Beef, [gym.Beef]),
    ],
)
def test_list_available(input, target):
    assert input.list_available() == target


@pytest.mark.parametrize(
    "input,target",
    [
        (gym.GrandParent, True),
        (gym.ParentA, True),
        (gym.ParentB, True),
        (gym.Food, True),
        (gym.Fruit, True),
        (gym.Meat, True),
        (gym.Child0, True),
        (gym.Child1, True),
        (gym.Child2, True),
        (gym.Apple, True),
        (gym.Pork, True),
        (Dict[str, gym.Meat], False),
        (List[gym.GrandParent], False),
        (str, False),
        (int, False),
        (bool, False),
    ],
)
def test_match(input, target):
    gym_instance = gym.Gym()
    assert gym_instance.match(input) == target


@pytest.mark.parametrize(
    "cls,obj,is_from_obj,target",
    [
        (gym.Food, Params({"type": "apple"}), False, None),
        (gym.Food, Params({"type": "apple"}), True, None),
        (
            gym.Food,
            gym.Apple(),
            False,
            ParamError(target_cls=gym.Food, obj=gym.Apple()),
        ),
        (gym.Food, gym.Apple(), True, gym.Apple()),
        (gym.Food, True, True, ParamError(target_cls=gym.Food, obj=True)),
        (
            _B,
            Params({"type": "_b"}),
            False,
            UnRepresentedTypeError(_B, gym.Gym(), Params({"type": "_b"})),
        ),
        (
            _B,
            Params({"type": "_b"}),
            True,
            UnRepresentedTypeError(_B, gym.Gym(), Params({"type": "_b"})),
        ),
        (
            gym.Food,
            Params({}),
            False,
            ComplexTypeMismatchError(
                gym.Food, gym.Food.get_instantiate_children(), Params({})
            ),
        ),
        (
            gym.Food,
            Params({"type": "dne"}),
            True,
            ComplexTypeMismatchError(
                gym.Food, gym.Food.get_instantiate_children(), Params({"type": "dne"})
            ),
        ),
        (gym.GrandParent, Params({"type": "beef_2", "weight": 10}), False, None),
        (gym.ParentB, Params({"type": "beef_2", "weight": 10}), False, None),
        (gym.Child2, Params({"type": "beef_2", "weight": 10}), False, None),
        (gym.BeefChild2, Params({"type": "beef_2", "weight": 10}), True, None),
    ],
)
def test_general_check(cls, obj, is_from_obj, target):
    unit = gym.Gym()
    orchestrator = Base([unit])
    assert (
        unit.general_check(
            cls=cls, orchestrator=orchestrator, obj=obj, is_from_obj=is_from_obj
        )
        == target
    )


def test_cant_use_same_name_twice():
    with pytest.raises(ConfigurationError):
        gym.Fruit.register("apple")(gym.Apple)


def test_get_none():
    gym_inst = gym.Gym()
    assert gym_inst.get(_B, ORCHESTRATOR) is None


@pytest.mark.parametrize(
    "cls,obj,target",
    [
        (gym.Food, True, ParamError),
        (_B, Params({"type": "_b"}), UnRepresentedTypeError),
        (gym.Food, Params({"type": "dne"}), ComplexTypeMismatchError),
    ],
)
def test_from_obj_exception(cls, obj, target):
    gym_inst = gym.Gym()
    with pytest.raises(target):
        gym_inst.from_obj(cls, ORCHESTRATOR, obj)
