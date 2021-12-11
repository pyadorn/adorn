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
from typing import Dict
from typing import Iterable
from typing import List
from typing import Set
from typing import Tuple
from typing import Union

from tests.example.dne import _A
from tests.example.dne import _B
from tests.example.dne import _C

from adorn.exception.type_check_error import HashableError
from adorn.exception.type_check_error import KeyValueError
from adorn.exception.type_check_error import TupleArgLenError
from adorn.exception.type_check_error import UnRepresentedTypeError
from adorn.exception.type_check_error import WrongTypeError
from adorn.orchestrator.base import Base
from adorn.unit.python import Bool
from adorn.unit.python import Float
from adorn.unit.python import Int
from adorn.unit.python import Python
from adorn.unit.python import Ret
from adorn.unit.python import Rict
from adorn.unit.python import Rnion
from adorn.unit.python import Rterable
from adorn.unit.python import Ruple
from adorn.unit.python import Str

BUILTIN_TYPES = [
    (Int, int),
    (Int, int),
    (Str, str),
    (Str, Str),
    (Bool, bool),
    (Bool, bool),
    (Float, float),
    (Float, Float),
]

BUILTIN_TYPES_MISMATCH = [
    (Int, bool),
    (Int, float),
    (Str, int),
    (Float, int),
    (Float, bool),
    (Float, str),
    (Bool, int),
    (Bool, float),
]

BUILTIN_TYPE_CHECK = list(
    chain(
        *[
            [(Int, int, i) for i in [-100, -1, 0, 1, 100]],
            [(Bool, bool, i) for i in [True, False]],
            [(Str, str, i) for i in ["", "c", "ada dafa"]],
            [(Float, float, i) for i in [-100.0, -0.0, 1.241]],
        ]
    )
)

BUILTIN_TYPE_CHECK_WRONG = list(
    chain(
        *[
            [
                (Int, int, i, WrongTypeError(int, i))
                for i in ["0", "1", True, False, 1.1]
            ],
            [(Bool, bool, i, WrongTypeError(bool, i)) for i in [0, 1, "1", "0"]],
            [(Str, str, i, WrongTypeError(str, i)) for i in [0, 1, 1.1, True]],
            [(Float, float, i, WrongTypeError(float, i)) for i in [1, True, "1.23543"]],
        ]
    )
)

BUILTIN_FROM_OBJ = list(
    chain(
        *[
            [
                (Int, int, v, tv)
                for v, tv in [
                    (-384, -384),
                    ("0", 0),
                    ("1", 1),
                    (True, 1),
                    (False, 0),
                    (1.1, 1),
                ]
            ],
            [
                (Bool, bool, v, tv)
                for v, tv in [(False, False), (True, True), (0, False), (1, True)]
            ],
            [
                (Str, str, v, tv)
                for v, tv in [
                    ("abA", "abA"),
                    (0, "0"),
                    (1, "1"),
                    (1.1, "1.1"),
                    (True, "True"),
                ]
            ],
            [
                (Float, float, v, tv)
                for v, tv in [(-3.235, -3.235), (1, 1.0), (False, 0.0), ("1.2", 1.2)]
            ],
        ]
    )
)

# PYTHON WRAPPER

WRAPPER_TYPES = list(
    chain(
        *[
            [
                (Rterable, i)
                for i in [List[int], Iterable[str], Iterable[float], List[bool]]
            ],
            [(Ret, i) for i in [Set[int], Set[float], Set[str]]],
            [
                (Ruple, i)
                for i in [Tuple[int, List[Set[str]]], Tuple[str, Set[int], List[float]]]
            ],
            [
                (Rnion, i)
                for i in [Union[Set[str], List[Tuple[float, bool]]], Union[float, str]]
            ],
            [(Rict, i) for i in [Dict[str, List[float]], Dict[int, Set[bool]]]],
        ]
    )
)

WRAPPER_TYPES_MISMATCH = list(
    chain(
        *[
            [(Rterable, i) for i in [List[_A], List[_B], Set[int], Dict[str, str]]],
            [(Ret, i) for i in [Set[_A], Set[_B], List[str], Dict[int, float]]],
            [
                (Ruple, i)
                for i in [Tuple[int, float, _A], List[str], Set[int], Dict[str, float]]
            ],
            [
                (Rnion, i)
                for i in [Union[str, _A], Tuple[int, str], List[Union[float, int]]]
            ],
            [
                (Rict, i)
                for i in [
                    Union[str, Dict[str, int]],
                    Tuple[str, int],
                    Dict[str, _A],
                    Dict[_A, str],
                    Dict[_A, _A],
                ]
            ],
        ]
    )
)

WRAPPER_TYPE_CHECK = [
    (Rterable, List[int], [-1, 0, 1]),
    (Rterable, List[str], ["ab"]),
    (Rterable, List[float], []),
    (Ret, Set[int], set()),
    (Ret, Set[float], {1.1, -23.0}),
    (Ret, Set[bool], {True, False}),
    (Ruple, Tuple[int, float, str], (-1, 1.1, "")),
    (Ruple, Tuple[List[Set[bool]], str], ([{True}, {False}], "yes")),
    (Rnion, Union[float, str], 1.1),
    (Rnion, Union[float, str], "a"),
    (Rnion, Union[List[int], List[Union[str, int]]], [1, "1", "2", 2]),
    (Rict, Dict[int, Set[str]], {0: {"", "a"}, 1: {"bcd", "efg"}}),
    (Rict, Dict[str, List[Tuple[bool, float]]], {"a": [(False, 1.1)]}),
    (Rict, Dict[int, str], dict()),
]

WRAPPER_TYPE_CHECK_WRONG = [
    (
        Rterable,
        List[int],
        [1, 2, "2"],
        KeyValueError(List[int], {2: WrongTypeError(int, "2")}, [1, 2, "2"]),
    ),
    (
        Rterable,
        List[str],
        [0, "a", True],
        KeyValueError(
            List[str],
            {0: WrongTypeError(str, 0), 2: WrongTypeError(str, True)},
            [0, "a", True],
        ),
    ),
    (Rterable, List[float], {0}, WrongTypeError(List[float], {0})),
    (
        Rterable,
        List[Set[bool]],
        [{True}, {"no"}],
        KeyValueError(
            List[Set[bool]],
            {1: KeyValueError(Set[bool], {0: WrongTypeError(bool, "no")}, {"no"})},
            [{True}, {"no"}],
        ),
    ),
    (
        Ret,
        Set[int],
        {-1, "2"},
        KeyValueError(
            Set[int],
            {0: WrongTypeError(int, "2")},
            {-1, "2"},
        ),
    ),
    (Ret, float, [1.1, 1.2], WrongTypeError(float, [1.1, 1.2])),
    (Ret, Set[List[float]], set(), HashableError(Set[List[float]], Rterable, set())),
    (Ruple, Tuple[int, float], {1: 1.1}, WrongTypeError(Tuple[int, float], {1: 1.1})),
    (
        Ruple,
        Tuple[List[Set[bool]], str],
        ([{True}, {"no"}], "yes"),
        KeyValueError(
            Tuple[List[Set[bool]], str],
            {
                0: KeyValueError(
                    List[Set[bool]],
                    {
                        1: KeyValueError(
                            Set[bool], {0: WrongTypeError(bool, "no")}, {"no"}
                        )
                    },
                    [{True}, {"no"}],
                )
            },
            ([{True}, {"no"}], "yes"),
        ),
    ),
    (Ruple, Tuple[int, int], (1,), TupleArgLenError(Tuple[int, int], (1,))),
    (
        Rnion,
        Union[int, float],
        "1",
        KeyValueError(
            Union[int, float],
            {int: WrongTypeError(int, "1"), float: WrongTypeError(float, "1")},
            "1",
        ),
    ),
    (
        Rnion,
        Union[Set[List[int]], float],
        [[1.1]],
        KeyValueError(
            Union[Set[List[int]], float],
            {
                Set[List[int]]: HashableError(Set[List[int]], Rterable, [[1.1]]),
                float: WrongTypeError(float, [[1.1]]),
            },
            [[1.1]],
        ),
    ),
    (
        Rict,
        Dict[List[str], int],
        dict(),
        HashableError(Dict[List[str], int], Rterable, dict()),
    ),
    (Rict, Dict[int, str], (0, "a"), WrongTypeError(Dict[int, str], (0, "a"))),
    (
        Rict,
        Dict[str, int],
        {0: "1", "a": "b", 1: 2, "c": 3},
        KeyValueError(
            Dict[str, int],
            {
                f"key_{str}_0": WrongTypeError(str, 0),
                f"key_{str}_1": WrongTypeError(str, 1),
                f"value_{int}_0": WrongTypeError(int, "1"),
                f"value_{int}_1": WrongTypeError(int, "b"),
            },
            {0: "1", "a": "b", 1: 2, "c": 3},
        ),
    ),
]

WRAPPER_FROM_OBJ = [
    (Rterable, List[int], ["0", 100, -100, True], [0, 100, -100, True]),
    (Rterable, Iterable[str], ["abc", 0], ["abc", "0"]),
    (Rterable, List[float], [-1.1, 2], [-1.1, 2.0]),
    (Ret, Set[str], [], set()),
    (Ret, Set[int], [-1, -2, 2], {-1, -2, 2}),
    (Ret, Set[bool], {True, False}, {True, False}),
    (Ruple, Tuple[int, float, str], ["-1", 1.1, ""], (-1, 1.1, "")),
    (
        Ruple,
        Tuple[List[Set[bool]], str],
        [[[True], [False]], "yes"],
        ([{True}, {False}], "yes"),
    ),
    (Ruple, Tuple[int, int], (1, "2"), (1, 2)),
    (Rnion, Union[float, str], 1.1, 1.1),
    (Rnion, Union[float, str], "1.1", "1.1"),
    (
        Rnion,
        Union[List[int], List[Union[str, int]]],
        [1, "1", "2", 2],
        [1, "1", "2", 2],
    ),
    (Rnion, Union[bool, float], 1, KeyValueError),
    (
        Rict,
        Dict[int, float],
        {"1": "1.1", "2": 2.2, 3: "3.3", 4: 4.4},
        {1: 1.1, 2: 2.2, 3: 3.3, 4: 4.4},
    ),
    (Rict, Dict[str, List[Tuple[bool, bool]]], {1: [[0, 1]]}, {"1": [(False, True)]}),
    (Rict, Dict[str, int], dict(), dict()),
]

BASE_TYPE_DNE_LIST = list(
    chain(
        *[
            [(_B, i) for i in ["a", 100, True, 1.1]],
            [(_C, i) for i in ["asdads dadf", -100, False, -3.14]],
            [(None, None)],
        ]
    )
)

BASE_TYPE = Python()


TYPES = [(BASE_TYPE, *i) for i in (BUILTIN_TYPES + WRAPPER_TYPES)]
TYPES_MISMATCH = [
    (BASE_TYPE, *i) for i in (BUILTIN_TYPES_MISMATCH + WRAPPER_TYPES_MISMATCH)
]
TYPE_CHECK = [(BASE_TYPE, *i) for i in (BUILTIN_TYPE_CHECK + WRAPPER_TYPE_CHECK)]
TYPE_CHECK_WRONG = [
    (BASE_TYPE, *i) for i in (BUILTIN_TYPE_CHECK_WRONG + WRAPPER_TYPE_CHECK_WRONG)
]
FROM_OBJ = [(BASE_TYPE, *i) for i in (BUILTIN_FROM_OBJ + WRAPPER_FROM_OBJ)]
TYPE_CHECK_WRONG_SPECIAL = [
    (
        BASE_TYPE,
        Ret,
        Set[_A],
        set(),
        UnRepresentedTypeError(Set[_A], unit=Base([]), obj=set()),
    )
]

DNE_LIST = [(BASE_TYPE, *i) for i in BASE_TYPE_DNE_LIST]
