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
from typing import Dict, List

if (version_info.major > 3) or (version_info.major == 3 and version_info.minor >= 8):
    from typing import Literal
else:
    from typing_extensions import Literal

from adorn.data.parameter import Parameter
from adorn.exception.type_check_error import (
    ComplexTypeMismatchError,
    ExtraLiteralError,
    KeyValueDiffError,
    KeyValueError,
    ParamError,
    WrongTypeError,
)
from adorn.params import Params
from adorn.unit.parameter_value import (
    DependentFromObj,
    DependentTypeCheck,
    DependentUnion,
    ParameterValue,
)

from tests.example import gym
from tests.example.dne import _B

PARAMETER_VALUE_TYPES = [
    (
        DependentFromObj,
        Parameter(
            DependentFromObj[gym.Apple, Literal[{"a": "a.c"}]],
            gym.Child2,
            {"a": 0},
            "fruit",
        ),
    ),
    (
        DependentTypeCheck,
        Parameter(
            DependentTypeCheck[gym.Apple, Literal[{"a": "a.c"}]],
            gym.Child2,
            {"a": 0},
            "fruit",
        ),
    ),
    (
        DependentUnion,
        Parameter(
            DependentUnion[
                DependentFromObj[gym.DMO, Literal[{"dd": "dlc.dd"}]], gym.MMO
            ],
            gym.BLIM,
            dict(),
            "mo",
        ),
    ),
]

PARAMETER_VALUE_TYPES_MISMATCH = [
    (
        DependentFromObj,
        Parameter(
            DependentFromObj[_B, Literal[{"a": "a.c"}]], gym.Child2, {"a": 0}, "fruit"
        ),
    ),
    (
        DependentTypeCheck,
        Parameter(
            DependentTypeCheck[_B, Literal[{"a": "a.c"}]], gym.Child2, {"a": 0}, "fruit"
        ),
    ),
    (
        DependentFromObj,
        Parameter(
            DependentTypeCheck[gym.Apple, Literal[{"a": "a.c"}]],
            gym.Child2,
            {"a": 0},
            "fruit",
        ),
    ),
    (
        DependentTypeCheck,
        Parameter(
            DependentFromObj[gym.Apple, Literal[{"a": "a.c"}]],
            gym.Child2,
            {"a": 0},
            "fruit",
        ),
    ),
    (DependentTypeCheck, Parameter(gym.Apple, gym.Child2, {"a": 0}, "fruit")),
    (DependentFromObj, Parameter(gym.Apple, gym.Child2, {"a": 0}, "fruit")),
    (
        DependentFromObj,
        Parameter(
            DependentTypeCheck[int, Literal[{"a": "a.c"}]],
            gym.Child2,
            {"a": 0},
            "fruit",
        ),
    ),
    (
        DependentTypeCheck,
        Parameter(
            DependentFromObj[int, Literal[{"a": "a.c"}]], gym.Child2, {"a": 0}, "fruit"
        ),
    ),
    (
        DependentUnion,
        Parameter(
            DependentUnion[DependentTypeCheck[_B, Literal[{"a": "a.c"}]], None],
            gym.Child2,
            {"a": 0},
            "fruit",
        ),
    ),
    (
        DependentUnion,
        Parameter(DependentUnion[List[int], None], gym.Child2, {"a": 0}, "fruit"),
    ),
]

PARAMETER_VALUE_TYPE_CHECK = [
    (
        DependentTypeCheck,
        Parameter(
            DependentTypeCheck[gym.S, Literal[{"d": "d"}]],
            gym.BDL,
            {"sh": True, "d": {"type": "id"}},
            "s",
        ),
        Params(
            {"type": "is", "d": {"type": "id", "filename": "", "k": [], "dd": dict()}}
        ),
    ),
    (
        DependentFromObj,
        Parameter(
            DependentFromObj[gym.MO, Literal[{"dd": "dlc.dd"}]],
            gym.BLIM,
            {"dlc": {"type": "dlc", "etc": "garbage"}},
            "mo",
        ),
        Params({"type": "dmo"}),
    ),
    (
        DependentFromObj,
        Parameter(
            DependentFromObj[gym.SME, Literal[{"dd": "dlc.dd"}]],
            gym.BLIM,
            {"dlc": {"type": "dlc", "etc": "garbage"}},
            "sme",
        ),
        Params({"type": "bsme", "lst": []}),
    ),
    (
        DependentTypeCheck,
        Parameter(
            DependentTypeCheck[gym.OP, Literal[{"dmo": "mo"}]],
            gym.BLIM,
            {"mo": {"type": "dmo"}},
            "op",
        ),
        Params({"type": "op", "l_ambig": 1.1}),
    ),
    (
        DependentTypeCheck,
        Parameter(
            DependentTypeCheck[gym.LRS, Literal[{"op": "op"}]],
            gym.BLIM,
            {"op": {"type": "op", "l_ambig": 1.1}},
            "lrs",
        ),
        Params(
            {
                "type": "lrs",
                "per": 10,
                "op": {
                    "type": "op",
                    "l_ambig": 1.1,
                    "dmo": {"type": "dmo", "dd": {"a": 1}},
                },
            }
        ),
    ),
]

PARAMETER_VALUE_TYPE_CHECK_WRONG = [
    (
        DependentTypeCheck,
        Parameter(
            DependentFromObj[gym.DMO, Literal[{"dd": "dlc.data_dim"}]],
            gym.BLIM,
            {"dlc": "garbage"},
            "mo",
        ),
        1,
        ParamError(gym.DMO, 1),
    ),
    (
        DependentTypeCheck,
        Parameter(
            DependentTypeCheck[gym.OP, Literal[{"dmo": "mo"}]],
            gym.BLIM,
            {"mo": {"type": "mmo"}},
            "op",
        ),
        Params({"type": "op", "l_ambig": 1.1}),
        KeyValueError(
            Parameter(
                DependentTypeCheck[gym.OP, Literal[{"dmo": "mo"}]],
                gym.BLIM,
                {"mo": {"type": "mmo"}},
                "op",
            ),
            {
                "dmo": ComplexTypeMismatchError(
                    gym.DMO, gym.DMO.get_instantiate_children(), {"type": "mmo"}
                )
            },
            Params({"type": "op", "l_ambig": 1.1}),
        ),
    ),
    (
        DependentTypeCheck,
        Parameter(
            DependentTypeCheck[gym.SME, Literal[{"dd": "dlc.dd"}]],
            gym.BLIM,
            {"dlc": {"type": "dlc", "dd": 1}},
            "sme",
        ),
        Params({"type": "bsme", "lst": []}),
        KeyValueError(
            Parameter(
                DependentTypeCheck[gym.SME, Literal[{"dd": "dlc.dd"}]],
                gym.BLIM,
                {"dlc": {"type": "dlc", "dd": 1}},
                "sme",
            ),
            {"dd": WrongTypeError(Dict[str, int], 1)},
            Params({"type": "bsme", "lst": []}),
        ),
    ),
    (
        DependentUnion,
        Parameter(
            DependentUnion[
                DependentFromObj[gym.MO, Literal[{"dd": "dlc.data_dim"}]], gym.MO
            ],
            gym.BLIM,
            {"dlc": "garbage"},
            "mo",
        ),
        Params({"type": "mmo"}),
        KeyValueError(
            Parameter(
                DependentUnion[
                    DependentFromObj[gym.MO, Literal[{"dd": "dlc.data_dim"}]], gym.MO
                ],
                gym.BLIM,
                {"dlc": "garbage"},
                "mo",
            ),
            [
                (
                    Parameter(
                        DependentFromObj[gym.MO, Literal[{"dd": "dlc.data_dim"}]],
                        gym.BLIM,
                        {"dlc": "garbage"},
                        "mo",
                    ),
                    ExtraLiteralError(
                        Parameter(
                            DependentFromObj[gym.MO, Literal[{"dd": "dlc.data_dim"}]],
                            gym.BLIM,
                            {"dlc": "garbage"},
                            "mo",
                        ),
                        ["dd"],
                    ),
                ),
                (
                    Parameter(
                        gym.MO,
                        gym.BLIM,
                        {"dlc": "garbage"},
                        "mo",
                    ),
                    KeyValueDiffError(
                        gym.LMMO, {"l_ambig": float}, None, Params({"type": "mmo"})
                    ),
                ),
            ],
            Params({"type": "mmo"}),
        ),
    ),
]


PARAMETER_VALUE_FROM_OBJ = [
    (
        DependentTypeCheck,
        Parameter(
            DependentTypeCheck[gym.S, Literal[{"d": "d"}]],
            gym.BDL,
            {"sh": True, "d": gym.BID("", [], dict())},
            "s",
        ),
        Params({"type": "is"}),
        gym.BIS(gym.BID("", [], dict())),
    ),
    (
        DependentFromObj,
        Parameter(
            DependentFromObj[gym.MO, Literal[{"dd": "dlc.dd"}]],
            gym.BLIM,
            {
                "dlc": gym.DictDLC(
                    {
                        "a": gym.BDL(
                            gym.BIS(gym.BID("", [], dict())),
                            gym.BID("", [], dict()),
                            True,
                        )
                    }
                )
            },
            "mo",
        ),
        Params({"type": "dmo"}),
        gym.FDMO(dict()),
    ),
    (
        DependentFromObj,
        Parameter(
            DependentFromObj[gym.SME, Literal[{"dd": "dlc.dd"}]],
            gym.BLIM,
            {
                "dlc": gym.DictDLC(
                    {
                        "a": gym.BDL(
                            gym.BIS(gym.BID("", [], dict())),
                            gym.BID("", [], dict()),
                            True,
                        )
                    }
                )
            },
            "sme",
        ),
        Params({"type": "bsme", "lst": []}),
        gym.BSME([], dict()),
    ),
    (
        DependentTypeCheck,
        Parameter(
            DependentTypeCheck[gym.OP, Literal[{"dmo": "mo"}]],
            gym.BLIM,
            {"mo": gym.FDMO(dict())},
            "op",
        ),
        Params({"type": "op", "l_ambig": 1.1}),
        gym.BOP(gym.FDMO(dict()), 1.1),
    ),
    (
        DependentTypeCheck,
        Parameter(
            DependentTypeCheck[gym.LRS, Literal[{"op": "op"}]],
            gym.BLIM,
            {"op": gym.BOP(gym.FDMO(dict()), 1.1)},
            "lrs",
        ),
        Params({"type": "lrs", "per": 10}),
        gym.BLRS(gym.BOP(gym.FDMO(dict()), 1.1), 10),
    ),
]

PARAMETER_VALUE = ParameterValue()

TYPES = [(PARAMETER_VALUE, *i) for i in (PARAMETER_VALUE_TYPES)]
TYPES_MISMATCH = [(PARAMETER_VALUE, *i) for i in (PARAMETER_VALUE_TYPES_MISMATCH)]
TYPE_CHECK = [(PARAMETER_VALUE, *i) for i in (PARAMETER_VALUE_TYPE_CHECK)]
TYPE_CHECK_WRONG = [(PARAMETER_VALUE, *i) for i in (PARAMETER_VALUE_TYPE_CHECK_WRONG)]
FROM_OBJ = [(PARAMETER_VALUE, *i) for i in (PARAMETER_VALUE_FROM_OBJ)]
