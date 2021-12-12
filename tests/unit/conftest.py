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
from typing import Optional

from tests.example import gym
from tests.example.dne import _B

from adorn.data.constructor import Constructor
from adorn.exception.type_check_error import AnumMemberError
from adorn.exception.type_check_error import ComplexTypeMismatchError
from adorn.exception.type_check_error import KeyValueDiffError
from adorn.exception.type_check_error import KeyValueError
from adorn.exception.type_check_error import ParamError
from adorn.exception.type_check_error import WrongTypeError
from adorn.params import Params

COMPLEX_TYPES = [
    (gym.GrandParent, gym.GrandParent),
    (gym.ParentA, gym.ParentA),
    (gym.ParentB, gym.ParentB),
    (gym.Food, gym.Food),
    (gym.Fruit, gym.Fruit),
    (gym.Meat, gym.Meat),
    (gym.Child0, gym.Child0),
    (gym.Child1, gym.Child1),
    (gym.Child2, gym.Child2),
    (gym.Apple, gym.Apple),
    (gym.Pork, gym.Pork),
]
COMPLEX_TYPES_MISMATCH = [
    (gym.Gym, _B),
    (gym.Gym, int),
    (gym.Gym, Constructor(gym.Apple)),
    (gym.Gym, Constructor(gym.Child0)),
    (gym.Gym, Dict[str, gym.Meat]),
    (gym.Gym, gym.IntentionallyUnregistered),
    (gym.Gym, Constructor(gym.Child0)),
]
COMPLEX_TYPE_CHECK = [
    (
        gym.Gym,
        gym.Child0,
        Params({"type": "0", "zero": ["a"], "a": 1, "gp": "yes"}),
    ),
    (
        gym.GrandParent,
        gym.Child0,
        Params({"type": "0", "zero": ["a"], "a": 1, "gp": "yes"}),
    ),
    (
        gym.ParentA,
        gym.Child0,
        Params({"type": "0", "zero": ["a"], "a": 1, "gp": "yes"}),
    ),
    (
        gym.Child0,
        gym.Child0,
        Params({"type": "0", "zero": ["a"], "a": 1, "gp": "yes"}),
    ),
    (
        gym.Gym,
        gym.Child1,
        Params({"type": "1", "one": {0: [True]}, "a": 1, "gp": "yes"}),
    ),
    (gym.Gym, gym.Apple, Params({"type": "apple"})),
    (gym.Food, gym.Apple, Params({"type": "apple"})),
    (gym.Fruit, gym.Apple, Params({"type": "apple"})),
    (gym.Apple, gym.Apple, Params({"type": "apple"})),
    (gym.Gym, gym.Avocado, Params({"type": "avocado"})),
]

COMPLEX_TYPE_CHECK_NO_UNDER = [
    (gym.Gym, gym.GrandParent, Params({"type": "beef_2", "weight": 10})),
    (gym.Gym, gym.ParentB, Params({"type": "beef_2", "weight": 10})),
    (gym.Gym, gym.Child2, Params({"type": "beef_2", "weight": 10})),
    (
        gym.Gym,
        gym.Child2,
        Params(
            {
                "type": "2",
                "food": None,
                "fruit": {"type": "apple"},
                "meat": {"type": "pork", "weight": 1.0},
                "gp": "works",
                "workout": {"lift": "Squat", "reps": 1, "weight": 405.0},
            }
        ),
    ),
    (gym.Meat, gym.Meat, Params({"type": "beef", "feed": "Grass", "weight": 12.0})),
]

AMBIG_TYPE_CHECK_NO_UNDER = [
    (
        gym.LIM,
        gym.BLIM,
        Params(
            {
                "type": "lim",
                "dlc": {
                    "type": "dlc",
                    "dct": {
                        "a": {
                            "type": "bdl",
                            "s": {"type": "is"},
                            "d": {
                                "type": "id",
                                "filename": "a",
                                "k": ["b"],
                                "dd": {"c": 1},
                            },
                            "sh": True,
                        }
                    },
                },
                "mo": {"type": "dmo"},
                "sme": {"type": "bsme", "lst": []},
                "lrs": {"type": "lrs", "per": 10},
                "op": {"type": "op", "l_ambig": 1.1},
            }
        ),
    ),
    (
        gym.LIM,
        gym.BLIM,
        Params(
            {
                "type": "lim",
                "dlc": {
                    "type": "dlc",
                    "dct": {
                        "a": {
                            "type": "bdl",
                            "s": {"type": "is"},
                            "d": {
                                "type": "id",
                                "filename": "a",
                                "k": ["b"],
                                "dd": {"c": 1},
                            },
                            "sh": True,
                        }
                    },
                },
                "mo": {"type": "mmo", "l_ambig": 2.2},
                "sme": {"type": "bsme", "lst": []},
                "lrs": None,
                "op": None,
            }
        ),
    ),
]


COMPLEX_TYPE_CHECK_WRONG = [
    (
        gym.Child2,
        gym.Child2,
        Params({"type": "2", "x": "abc"}),
        KeyValueDiffError(
            gym.Child2,
            {
                "gp": str,
                "food": Optional[gym.Food],
                "fruit": gym.Fruit,
                "meat": gym.Meat,
            },
            {"x": str},
            Params({"type": "2", "x": "abc"}),
        ),
    ),
    (
        gym.Gym,
        gym.Child0,
        Params({"type": "0", "zero": [1], "a": 1.1, "gp": "yes"}),
        KeyValueError(
            gym.Child0,
            {
                "zero": KeyValueError(List[str], {"0": WrongTypeError(str, 1)}, [1]),
                "a": WrongTypeError(int, 1.1),
            },
            Params({"type": "0", "zero": [1], "a": 1.1, "gp": "yes"}),
        ),
    ),
    (
        gym.GrandParent,
        gym.Child0,
        Params({"type": "0", "zero": [1], "a": 1.1, "gp": "yes"}),
        KeyValueError(
            gym.Child0,
            {
                "zero": KeyValueError(List[str], {"0": WrongTypeError(str, 1)}, [1]),
                "a": WrongTypeError(int, 1.1),
            },
            Params({"type": "0", "zero": [1], "a": 1.1, "gp": "yes"}),
        ),
    ),
    (
        gym.ParentA,
        gym.Child0,
        Params({"type": "0", "zero": [1], "a": 1.1, "gp": "yes"}),
        KeyValueError(
            gym.Child0,
            {
                "zero": KeyValueError(List[str], {"0": WrongTypeError(str, 1)}, [1]),
                "a": WrongTypeError(int, 1.1),
            },
            Params({"type": "0", "zero": [1], "a": 1.1, "gp": "yes"}),
        ),
    ),
    (
        gym.Child0,
        gym.Child0,
        Params({"type": "0", "zero": [1], "a": 1.1, "gp": "yes"}),
        KeyValueError(
            gym.Child0,
            {
                "zero": KeyValueError(List[str], {"0": WrongTypeError(str, 1)}, [1]),
                "a": WrongTypeError(int, 1.1),
            },
            Params({"type": "0", "zero": [1], "a": 1.1, "gp": "yes"}),
        ),
    ),
]


COMPLEX_TYPE_CHECK_WRONG_NO_UNDER = [
    (
        gym.Gym,
        gym.Food,
        gym.Apple(),
        ParamError(target_cls=gym.Food, obj=gym.Apple()),
    ),
    (
        gym.Food,
        gym.Apple,
        Params({}),
        ComplexTypeMismatchError(
            gym.Food, gym.Food.get_instantiate_children(), Params({})
        ),
    ),
    (
        gym.Food,
        gym.Food,
        Params({"type": "dne"}),
        ComplexTypeMismatchError(
            gym.Food, gym.Food.get_instantiate_children(), Params({"type": "dne"})
        ),
    ),
    (
        gym.Gym,
        gym.Child2,
        Params({"type": "beef_2", "weight": 10.0}),
        KeyValueError(
            gym.BeefChild2,
            {
                "weight": WrongTypeError(int, 10.0),
            },
            Params({"type": "beef_2", "weight": 10.0}),
        ),
    ),
    (
        gym.Gym,
        gym.Beef,
        Params({"type": "beef", "feed": "Gass", "weight": 10.0}),
        KeyValueError(
            gym.BeefChild2,
            {
                "feed": AnumMemberError(gym.FeedType, "Gass"),
            },
            Params({"type": "beef", "feed": "Gass", "weight": 10.0}),
        ),
    ),
]


COMPLEX_FROM_OBJ = [
    (gym.Gym, gym.Apple, Params({"type": "apple"}), gym.Apple()),
    (gym.Food, gym.Apple, Params({"type": "apple"}), gym.Apple()),
    (gym.Fruit, gym.Apple, Params({"type": "apple"}), gym.Apple()),
    (gym.Apple, gym.Apple, Params({"type": "apple"}), gym.Apple()),
    (gym.Apple, gym.Apple, gym.Apple(), gym.Apple()),
    (
        gym.Gym,
        gym.Child1,
        Params({"type": "1", "one": {"0": [1]}, "a": 1, "gp": "yes"}),
        gym.Child1(one={0: {True}}, a=1, gp="yes"),
    ),
    (
        gym.GrandParent,
        gym.Child1,
        Params({"type": "1", "one": {"0": [1]}, "a": 1, "gp": "yes"}),
        gym.Child1(one={0: {True}}, a=1, gp="yes"),
    ),
    (
        gym.ParentA,
        gym.Child1,
        Params({"type": "1", "one": {"0": [1]}, "a": 1, "gp": "yes"}),
        gym.Child1(one={0: {True}}, a=1, gp="yes"),
    ),
    (
        gym.Child1,
        gym.Child1,
        Params({"type": "1", "one": {"0": [1]}, "a": 1, "gp": "yes"}),
        gym.Child1(one={0: {True}}, a=1, gp="yes"),
    ),
]

COMPLEX_FROM_OBJ_NO_UNDER = [
    (
        gym.Gym,
        gym.GrandParent,
        Params({"type": "beef_2", "weight": 10}),
        gym.Child2(
            food=None, fruit=gym.Apple(), meat=gym.Beef(weight=10.0), gp="doesnt_matter"
        ),
    ),
    (
        gym.Gym,
        gym.ParentB,
        Params({"type": "beef_2", "weight": 10}),
        gym.Child2(
            food=None, fruit=gym.Apple(), meat=gym.Beef(weight=10.0), gp="doesnt_matter"
        ),
    ),
    (
        gym.Gym,
        gym.Child2,
        Params({"type": "beef_2", "weight": 10}),
        gym.Child2(
            food=None, fruit=gym.Apple(), meat=gym.Beef(weight=10.0), gp="doesnt_matter"
        ),
    ),
    (
        gym.Meat,
        gym.Meat,
        Params({"type": "beef", "feed": "Grass", "weight": 12.0}),
        gym.Beef(feed=gym.FeedType.Grass, weight=12.0),
    ),
    (
        gym.Gym,
        gym.Child2,
        Params(
            {
                "type": "2",
                "food": None,
                "fruit": {"type": "apple"},
                "meat": {"type": "pork", "weight": 1.0},
                "gp": "works",
                "workout": {"lift": "Squat", "reps": 1, "weight": 405.0},
            }
        ),
        gym.Child2(
            food=None,
            fruit=gym.Apple(),
            meat=gym.Pork(1.0),
            gp="works",
            workout=gym.Workout(gym.Lift.Squat, reps=1, weight=405.0),
        ),
    ),
]

AMBIG_FROM_OBJ_NO_UNDER = [
    (
        gym.LIM,
        gym.BLIM,
        Params(
            {
                "type": "lim",
                "dlc": {
                    "type": "dlc",
                    "dct": {
                        "a": {
                            "type": "bdl",
                            "s": {"type": "is"},
                            "d": {
                                "type": "id",
                                "filename": "a",
                                "k": ["b"],
                                "dd": {"c": 1},
                            },
                            "sh": True,
                        }
                    },
                },
                "mo": {"type": "dmo"},
                "sme": {"type": "bsme", "lst": []},
                "lrs": {"type": "lrs", "per": 10},
                "op": {"type": "op", "l_ambig": 1.1},
            }
        ),
        gym.BLIM(
            mo=gym.FDMO({"c": 1}),
            dlc=gym.DictDLC(
                {
                    "a": gym.BDL(
                        gym.BIS(gym.BID("a", ["b"], {"c": 1})),
                        gym.BID("a", ["b"], {"c": 1}),
                        True,
                    )
                }
            ),
            op=gym.BOP(gym.FDMO({"c": 1}), 1.1),
            sme=gym.BSME([], {"c": 1}),
            lrs=gym.BLRS(gym.BOP(gym.FDMO({"c": 1}), 1.1), 10),
        ),
    ),
    (
        gym.LIM,
        gym.BLIM,
        Params(
            {
                "type": "lim",
                "dlc": {
                    "type": "dlc",
                    "dct": {
                        "a": {
                            "type": "bdl",
                            "s": {"type": "is"},
                            "d": {
                                "type": "id",
                                "filename": "a",
                                "k": ["b"],
                                "dd": {"c": 1},
                            },
                            "sh": True,
                        }
                    },
                },
                "mo": {"type": "mmo", "l_ambig": 2.2},
                "sme": {"type": "bsme", "lst": []},
                "lrs": None,
                "op": None,
            }
        ),
        gym.BLIM(
            mo=gym.LMMO(l_ambig=2.2),
            dlc=gym.DictDLC(
                {
                    "a": gym.BDL(
                        gym.BIS(gym.BID("a", ["b"], {"c": 1})),
                        gym.BID("a", ["b"], {"c": 1}),
                        True,
                    )
                }
            ),
            op=None,
            sme=gym.BSME([], {"c": 1}),
            lrs=None,
        ),
    ),
]

COMPLEX = gym.Gym()
AMBIG = gym.Ambig()

TYPES = [(COMPLEX, *i) for i in (COMPLEX_TYPES)]
TYPES_MISMATCH = [(COMPLEX, *i) for i in (COMPLEX_TYPES_MISMATCH)]
TYPE_CHECK = [(COMPLEX, *i) for i in (COMPLEX_TYPE_CHECK)]
TYPE_CHECK_WRONG = [(COMPLEX, *i) for i in (COMPLEX_TYPE_CHECK_WRONG)]
FROM_OBJ = [(COMPLEX, *i) for i in (COMPLEX_FROM_OBJ)]


TYPE_CHECK_NO_UNDER = [(COMPLEX, *i) for i in (COMPLEX_TYPE_CHECK_NO_UNDER)] + [
    (AMBIG, *i) for i in (AMBIG_TYPE_CHECK_NO_UNDER)
]
TYPE_CHECK_WRONG_NO_UNDER = [(COMPLEX, *i) for i in (COMPLEX_TYPE_CHECK_WRONG_NO_UNDER)]
FROM_OBJ_NO_UNDER = [(COMPLEX, *i) for i in (COMPLEX_FROM_OBJ_NO_UNDER)] + [
    (AMBIG, *i) for i in (AMBIG_FROM_OBJ_NO_UNDER)
]
