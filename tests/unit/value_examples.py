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
from typing import Any
from typing import List
from typing import Set

from tests.example.dne import _B
from tests.example.dne import _C

from adorn.exception.type_check_error import WrongTypeError
from adorn.unit.value import Nny
from adorn.unit.value import Rone
from adorn.unit.value import Value

RONE_TYPES = [(Rone, None), (Rone, type(None)), (Nny, Any)]

RONE_TYPES_MISMATCH = list(chain(*[[(Rone, i) for i in [0, 0.0, "", False, True]]]))

RONE_TYPE_CHECK = [
    (Rone, None, None),
    (Rone, type(None), None),
    (Nny, Any, 1),
    (Nny, Any, "works"),
    (Nny, Any, None),
]

RONE_TYPE_CHECK_WRONG = [
    (Rone, None, 0, WrongTypeError(type(None), 0)),
    (Rone, type(None), "", WrongTypeError(type(None), "")),
    (Rone, None, [], WrongTypeError(type(None), [])),
]

RONE_FROM_OBJ = [
    (Rone, None, 0, None),
    (Rone, type(None), "", None),
    (Rone, None, None, None),
    (Nny, Any, 1, 1),
    (Nny, Any, None, None),
    (Nny, Any, "works", "works"),
]

VALUE_DNE_LIST = list(
    chain(
        *[
            [(_B, i) for i in ["a", 100, True, 1.1]],
            [(_C, i) for i in ["asdads dadf", -100, False, -3.14]],
            [(int, 1), (List[str], ["a", "b", "c"]), (Set[bool], {True})],
        ]
    )
)


VALUE = Value()


TYPES = [(VALUE, *i) for i in (RONE_TYPES)]
TYPES_MISMATCH = [(VALUE, *i) for i in (RONE_TYPES_MISMATCH)]
TYPE_CHECK = [(VALUE, *i) for i in (RONE_TYPE_CHECK)]
TYPE_CHECK_WRONG = [(VALUE, *i) for i in (RONE_TYPE_CHECK_WRONG)]
FROM_OBJ = [(VALUE, *i) for i in (RONE_FROM_OBJ)]
DNE_LIST = [(VALUE, *i) for i in VALUE_DNE_LIST]
