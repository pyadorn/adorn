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

import pytest
from adorn.data.parameter import Parameter
from adorn.exception.type_check_error import (
    ExtraLiteralError,
    KeyValueDiffError,
    KeyValueError,
    MalformedDependencyError,
    MalformedLiteralError,
    MissingDependencyError,
    MissingLiteralError,
    ParamError,
    TooDeepLiteralError,
    UnaryLiteralError,
    WrongTypeError,
)
from adorn.params import Params
from adorn.unit.parameter_value import Dependent, DependentFromObj, DependentUnion

from tests.conftest import ORCHESTRATOR
from tests.example import gym


@pytest.mark.parametrize(
    "target_cls,literal_dict,dependent_from_obj,max_depth,output",
    [
        (
            Parameter(None, None, {"a": {"b": 0, "c": 1}, "d": 2, "e": 3}, ""),
            {"ab": "a.b", "ac": "a.c", "e": "e"},
            False,
            None,
            {"ab": 0, "ac": 1, "e": 3},
        ),  # well formed DependentTypeCheck._type_check
        (
            Parameter(None, None, {"a": {"b": 0}, "d": 2}, ""),
            {"ab": "a.b", "ac": "a.c", "e": "e"},
            False,
            None,
            {"ab": 0},
        ),  # malformed DependentTypeCheck._type_check
        (
            Parameter(None, None, {"a": "garbage", "d": 2, "e": 3}, ""),
            {"ab": "a.b", "ac": "a.c", "e": "e"},
            True,
            1,
            {"ab": "garbage", "ac": "garbage", "e": 3},
        ),  # well formed DependentFromObj._type_check
        (
            Parameter(None, None, {"d": 2}, ""),
            {"ab": "a.b", "ac": "a.c", "e": "e"},
            True,
            1,
            dict(),
        ),  # malformed DependentFromObj._type_check
        (
            Parameter(
                None,
                None,
                {"a": gym.Beef(feed=gym.FeedType.Corn, weight=1.1), "d": 2, "e": 3},
                "",
            ),
            {"ab": "a.feed", "ac": "a.weight", "e": "e"},
            True,
            None,
            {"ab": gym.FeedType.Corn, "ac": 1.1, "e": 3},
        ),  # well formed Dependent._from_params
        (
            Parameter(
                None,
                None,
                {"a": gym.Beef(feed=gym.FeedType.Corn, weight=1.1), "d": 2},
                "",
            ),
            {"ab": "a.feed", "ac": "a.weight", "adne": "a.dne", "e": "e"},
            True,
            None,
            {"ab": gym.FeedType.Corn, "ac": 1.1},
        ),  # well formed Dependent._from_params
    ],
)
def test_get_args(target_cls, literal_dict, dependent_from_obj, max_depth, output):
    assert (
        Dependent.get_args(
            target_cls=target_cls,
            literal_dict=literal_dict,
            dependent_from_obj=dependent_from_obj,
            max_depth=max_depth,
        )
        == output
    )


@pytest.mark.parametrize(
    "target_cls,output",
    [
        (
            Parameter(
                DependentFromObj[gym.MO, Literal[{"dd": "dlc.data_dim"}]],
                gym.BLIM,
                {"dlc": "garbage"},
                "mo",
            ),
            None,
        ),
        (
            Parameter(int, gym.BLIM, {"dlc": "garbage"}, "mo"),
            MalformedDependencyError(
                Parameter(int, gym.BLIM, {"dlc": "garbage"}, "mo")
            ),
        ),  # no args
        (
            Parameter(
                DependentFromObj[gym.MO, None], gym.BLIM, {"dlc": "garbage"}, "mo"
            ),
            MissingLiteralError(
                Parameter(
                    DependentFromObj[gym.MO, None], gym.BLIM, {"dlc": "garbage"}, "mo"
                )
            ),
        ),  # second arg isn't literal
        (
            Parameter(
                DependentFromObj[gym.MO, Literal[1, None]],
                gym.BLIM,
                {"dlc": "garbage"},
                "mo",
            ),
            UnaryLiteralError(
                Parameter(
                    DependentFromObj[gym.MO, Literal[1, None]],
                    gym.BLIM,
                    {"dlc": "garbage"},
                    "mo",
                )
            ),
        ),  # too many arg for literal
        (
            Parameter(
                DependentFromObj[gym.MO, Literal[1]], gym.BLIM, {"dlc": "garbage"}, "mo"
            ),
            MalformedLiteralError(
                Parameter(
                    DependentFromObj[gym.MO, Literal[1]],
                    gym.BLIM,
                    {"dlc": "garbage"},
                    "mo",
                ),
                Dict[str, str],
                WrongTypeError(Dict[str, str], 1),
            ),
        ),  # too many arg for literal
    ],
)
def test_check_args(target_cls, output):
    assert (
        Dependent.check_args(target_cls=target_cls, orchestrator=ORCHESTRATOR) == output
    )


@pytest.mark.parametrize(
    "target_cls,obj,dependent_from_obj,output",
    [
        (
            Parameter(
                DependentFromObj[gym.DMO, Literal[{"dd": "dlc.data_dim"}]],
                gym.BLIM,
                {"dlc": "garbage"},
                "mo",
            ),
            Params({"type": "dmo"}),
            True,
            None,
        ),  # well formed DependentFromObj
        (
            Parameter(
                DependentFromObj[
                    gym.DMO, Literal[{"dne_in_constructor": "dlc.data_dim"}]
                ],
                gym.BLIM,
                {"dlc": "garbage"},
                "mo",
            ),
            Params({"type": "dmo"}),
            True,
            ExtraLiteralError(
                Parameter(
                    DependentFromObj[
                        gym.DMO, Literal[{"dne_in_constructor": "dlc.data_dim"}]
                    ],
                    gym.BLIM,
                    {"dlc": "garbage"},
                    "mo",
                ),
                ["dne_in_constructor"],
            ),
        ),  # malformed DependentFromObj
        (
            Parameter(
                DependentFromObj[gym.DMO, Literal[{"dd": "dlc.data_dim.extra"}]],
                gym.BLIM,
                {"dlc": "garbage"},
                "mo",
            ),
            Params({"type": "dmo"}),
            True,
            TooDeepLiteralError(
                Parameter(
                    DependentFromObj[gym.DMO, Literal[{"dd": "dlc.data_dim.extra"}]],
                    gym.BLIM,
                    {"dlc": "garbage"},
                    "mo",
                ),
                ["dlc.data_dim.extra"],
            ),
        ),  # malformed DependentFromObj
        (
            Parameter(
                DependentFromObj[gym.DMO, Literal[{"dd": "dlc.data_dim"}]],
                gym.BLIM,
                {"dlcc": "garbage"},
                "mo",
            ),
            Params({"type": "dmo"}),
            True,
            MissingDependencyError(
                Parameter(
                    DependentFromObj[gym.DMO, Literal[{"dd": "dlc.data_dim"}]],
                    gym.BLIM,
                    {"dlcc": "garbage"},
                    "mo",
                ),
                {"dd": "dlc.data_dim"},
            ),
        ),  # malformed DependentFromObj
    ],
)
def test_check_literal_dict(target_cls, obj, dependent_from_obj, output):
    assert (
        Dependent.check_literal_dict(
            target_cls=target_cls, obj=obj, dependent_from_obj=dependent_from_obj
        )
        == output
    )


@pytest.mark.parametrize(
    "target_cls,obj,dependent_from_obj,output",
    [
        (
            Parameter(
                DependentFromObj[gym.DMO, Literal[{"dd": "dlc.data_dim"}]],
                gym.BLIM,
                {"dlc": "garbage"},
                "mo",
            ),
            Params({"type": "dmo"}),
            True,
            None,
        ),
        (
            Parameter(
                DependentFromObj[gym.DMO, Literal[{"dd": "dlc.data_dim"}, 1]],
                gym.BLIM,
                {"dlc": "garbage"},
                "mo",
            ),
            Params({"type": "dmo"}),
            True,
            UnaryLiteralError(
                Parameter(
                    DependentFromObj[gym.DMO, Literal[{"dd": "dlc.data_dim"}, 1]],
                    gym.BLIM,
                    {"dlc": "garbage"},
                    "mo",
                )
            ),
        ),  # malformed DependentFromObj, check_args
        (
            Parameter(
                DependentFromObj[
                    gym.DMO, Literal[{"dne_in_constructor": "dlc.data_dim"}]
                ],
                gym.BLIM,
                {"dlc": "garbage"},
                "mo",
            ),
            Params({"type": "dmo"}),
            True,
            ExtraLiteralError(
                Parameter(
                    DependentFromObj[
                        gym.DMO, Literal[{"dne_in_constructor": "dlc.data_dim"}]
                    ],
                    gym.BLIM,
                    {"dlc": "garbage"},
                    "mo",
                ),
                ["dne_in_constructor"],
            ),
        ),  # malformed DependentFromObj, check_literal_dict
        (
            Parameter(
                DependentFromObj[gym.DMO, Literal[{"dd": "dlc.data_dim"}]],
                gym.BLIM,
                {"dlc": "garbage"},
                "mo",
            ),
            1,
            True,
            ParamError(gym.DMO, 1),
        ),  # malformed DependentFromObj, obj wrong type
    ],
)
def test_perfunctory_type_check(target_cls, obj, dependent_from_obj, output):
    assert (
        Dependent.perfunctory_type_check(
            target_cls=target_cls,
            orchestrator=ORCHESTRATOR,
            obj=obj,
            dependent_from_obj=dependent_from_obj,
        )
        == output
    )


def test__from_obj_check_arg_raise():
    target_cls = Parameter(
        DependentFromObj[gym.DMO, Literal[{"dd": "dlc.data_dim"}, 1]],
        gym.BLIM,
        {"dlc": "garbage"},
        "mo",
    )
    with pytest.raises(UnaryLiteralError):
        Dependent._from_obj(
            target_cls=target_cls,
            orchestrator=ORCHESTRATOR,
            obj=Params({"type": "dmo"}),
        )


def test__from_obj_literal_dict_raise():
    target_cls = Parameter(
        DependentFromObj[gym.DMO, Literal[{"dd": "dlc.data_dim"}]],
        gym.BLIM,
        {"dlcc": "garbage"},
        "mo",
    )
    with pytest.raises(MissingDependencyError):
        Dependent._from_obj(
            target_cls=target_cls,
            orchestrator=ORCHESTRATOR,
            obj=Params({"type": "dmo"}),
        )


@pytest.mark.parametrize(
    "target_cls,obj,output",
    [
        (
            Parameter(
                DependentUnion[
                    DependentFromObj[gym.DMO, Literal[{"dd": "dlc.data_dim"}]], gym.MO
                ],
                gym.BLIM,
                {"dlc": "garbage"},
                "mo",
            ),
            Params({"type": "dmo"}),
            Parameter(
                DependentFromObj[gym.DMO, Literal[{"dd": "dlc.data_dim"}]],
                gym.BLIM,
                {"dlc": "garbage"},
                "mo",
            ),
        ),
        (
            Parameter(
                DependentUnion[
                    DependentFromObj[gym.MO, Literal[{"dd": "dlc.data_dim"}]], gym.MO
                ],
                gym.BLIM,
                {"dlc": "garbage"},
                "mo",
            ),
            Params({"type": "mmo", "l_ambig": 1.0}),
            Parameter(
                gym.MO,
                gym.BLIM,
                {"dlc": "garbage"},
                "mo",
            ),
        ),
        (
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
                        DependentFromObj[gym.MO, Literal[{"dd": "dlc.data_dim"}]],
                        gym.MO,
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
                                DependentFromObj[
                                    gym.MO, Literal[{"dd": "dlc.data_dim"}]
                                ],
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
    ],
)
def test_get_parameter(target_cls, obj, output):
    assert (
        DependentUnion.get_parameter(
            target_cls=target_cls, orchestrator=ORCHESTRATOR, obj=obj
        )
        == output
    )


def test__from_obj_key_value_raise():
    target_cls = Parameter(
        DependentUnion[
            DependentFromObj[gym.MO, Literal[{"dd": "dlc.data_dim"}]], gym.MO
        ],
        gym.BLIM,
        {"dlc": "garbage"},
        "mo",
    )
    with pytest.raises(KeyValueError):
        DependentUnion._from_obj(
            target_cls=target_cls,
            orchestrator=ORCHESTRATOR,
            obj=Params({"type": "mmo"}),
        )
