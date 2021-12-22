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
from os import path as op
from shutil import rmtree
from tempfile import mkdtemp

import pytest

from adorn.orchestrator.base import Base
from adorn.params import Params
from adorn.unit.constructor_value import ConstructorValue
from adorn.unit.parameter_value import ParameterValue
from adorn.unit.python import Python
from adorn.unit.search.grid import BaseGrid
from adorn.unit.search.grid import BaseGridSearch
from adorn.unit.search.grid import FileGridSearch
from adorn.unit.search.grid import GridElement
from adorn.unit.search.grid import GridList
from adorn.unit.search.grid import GridNestedList
from adorn.unit.search.grid import GridOrchestrator
from adorn.unit.search.grid import GridSearch
from adorn.unit.search.grid import Group
from adorn.unit.search.grid import GroupBy
from adorn.unit.search.grid import IDGroup
from adorn.unit.search.grid import IDOrganize
from adorn.unit.search.grid import ListGridSearch
from adorn.unit.search.grid import Organize
from adorn.unit.search.grid import SortOrganize
from adorn.unit.value import Value


STR_TO_LIST = [("a", ["a"]), (["a", "b", "c"], ["a", "b", "c"])]


TUPLE_TO_DICT = [
    (({"a": 0}, {"b": 1}), {k: en for en, k in enumerate(["a", "b"])}),
    (
        ({"a": 0, "b": 1}, {"c": 2}, {"d": 3, "e": 4}),
        {k: en for en, k in enumerate(["a", "b", "c", "d", "e"])},
    ),
    (({"a": 0, "b": 1},), {"a": 0, "b": 1}),
]

ORCHESTRATOR = Base(
    [
        Value(),
        ParameterValue(),
        ConstructorValue(),
        Python(),
        GridElement(),
        GridSearch(),
        Organize(),
        Group(),
        GridOrchestrator(),
    ]
)

SEARCH_ELEMENT_PARAM_LIST = [
    (
        GridElement,
        BaseGrid,
        Params({"type": "base_grid", "keys": ["a", "b"], "values": [0, 1]}),
        2,
    ),
    (GridElement, BaseGrid, Params({"type": "id_grid", "keys": "a", "value": 0}), 1),
    (
        GridSearch,
        BaseGridSearch,
        Params(
            {
                "type": "base_grid_search",
                "search_space": [{"type": "id_grid", "keys": "a", "value": 0}],
            }
        ),
        1,
    ),
    (
        GridSearch,
        BaseGridSearch,
        Params(
            {
                "type": "base_grid_search",
                "search_space": [
                    {"type": "id_grid", "keys": "a", "value": 0},
                    {
                        "type": "base_grid_search",
                        "search_space": [
                            {"type": "base_grid", "keys": ["a", "b"], "values": [0, 1]}
                        ],
                    },
                ],
            }
        ),
        2,
    ),
    (
        GridSearch,
        ListGridSearch,
        Params(
            {
                "type": "list_grid_search",
                "search_space": [
                    {
                        "type": "base_grid_search",
                        "search_space": [
                            {"type": "id_grid", "keys": "a", "value": 0},
                            {
                                "type": "base_grid_search",
                                "search_space": [
                                    {
                                        "type": "base_grid",
                                        "keys": ["a", "b"],
                                        "values": [0, 1],
                                    }
                                ],
                            },
                        ],
                    }
                ],
            }
        ),
        2,
    ),
    (
        GridSearch,
        ListGridSearch,
        Params(
            {
                "type": "list_grid_search",
                "search_space": [
                    {
                        "type": "base_grid_search",
                        "search_space": [
                            {"type": "id_grid", "keys": "a", "value": 0},
                            {
                                "type": "base_grid_search",
                                "search_space": [
                                    {
                                        "type": "base_grid",
                                        "keys": ["a", "b"],
                                        "values": [0, 1],
                                    }
                                ],
                            },
                        ],
                    },
                    {"type": "file_grid_search", "filenames": ["a", "b", "c"]},
                ],
            }
        ),
        5,
    ),
    (
        GridSearch,
        FileGridSearch,
        Params({"type": "file_grid_search", "filenames": ["a", "b", "c"]}),
        3,
    ),
]

CALL_LIST = [
    (GridElement, Params({"type": "id_grid", "keys": "a", "value": 1}), [{"a": 1}]),
    (
        GridElement,
        Params({"type": "id_grid", "keys": ["a", "b"], "value": 1}),
        [{"a": 1, "b": 1}],
    ),
    (
        GridElement,
        Params({"type": "base_grid", "keys": "a", "values": [1, 2]}),
        [{"a": i} for i in [1, 2]],
    ),
    (
        GridElement,
        Params({"type": "base_grid", "keys": ["a", "b"], "values": [1, 2]}),
        [{"a": i, "b": i} for i in [1, 2]],
    ),
    (
        GridSearch,
        Params(
            {
                "type": "base_grid_search",
                "search_space": [
                    {"type": "base_grid", "keys": ["a", "b"], "values": [1, 2]}
                ],
            }
        ),
        [{"a": i, "b": i} for i in [1, 2]],
    ),
    (
        GridSearch,
        Params(
            {
                "type": "base_grid_search",
                "search_space": [
                    {"type": "base_grid", "keys": ["a", "b"], "values": [1, 2]},
                    {"type": "id_grid", "keys": "c", "value": 3},
                ],
            }
        ),
        [{"a": i, "b": i, "c": 3} for i in [1, 2]],
    ),
    (
        GridSearch,
        Params(
            {
                "type": "base_grid_search",
                "search_space": [
                    {"type": "base_grid", "keys": ["a", "b"], "values": [1, 2]},
                    {"type": "id_grid", "keys": "c", "value": 3},
                    {
                        "type": "base_grid_search",
                        "search_space": [
                            {"type": "base_grid", "keys": ["d", "e"], "values": [4, 5]}
                        ],
                    },
                ],
            }
        ),
        [
            {"a": 1, "b": 1, "c": 3, "d": 4, "e": 4},
            {"a": 1, "b": 1, "c": 3, "d": 5, "e": 5},
            {"a": 2, "b": 2, "c": 3, "d": 4, "e": 4},
            {"a": 2, "b": 2, "c": 3, "d": 5, "e": 5},
        ],
    ),
    (
        GridSearch,
        Params(
            {
                "type": "list_grid_search",
                "search_space": [
                    {
                        "type": "base_grid_search",
                        "search_space": [
                            {"type": "base_grid", "keys": ["a", "b"], "values": [1, 2]},
                            {"type": "id_grid", "keys": "c", "value": 3},
                        ],
                    }
                ],
            }
        ),
        [{"a": i, "b": i, "c": 3} for i in [1, 2]],
    ),
    (
        GridSearch,
        Params(
            {
                "type": "list_grid_search",
                "search_space": [
                    {
                        "type": "base_grid_search",
                        "search_space": [
                            {"type": "base_grid", "keys": ["a", "b"], "values": [1, 2]},
                            {"type": "id_grid", "keys": "c", "value": 3},
                        ],
                    },
                    {
                        "type": "base_grid_search",
                        "search_space": [
                            {"type": "base_grid", "keys": ["a", "b"], "values": [1, 2]}
                        ],
                    },
                ],
            }
        ),
        [{"a": i, "b": i, "c": 3} for i in [1, 2]] + [{"a": i, "b": i} for i in [1, 2]],
    ),
]


GRID_ORCH_PARAMS = [
    (Organize, IDOrganize, Params({"type": "id_organize"})),
    (Organize, SortOrganize, Params({"type": "sort_organize", "keys": "a"})),
    (Group, IDGroup, Params({"type": "id_group"})),
    (Group, GroupBy, Params({"type": "group_by", "keys": ["a", "b"]})),
    (
        GridOrchestrator,
        GridList,
        Params(
            {
                "type": "grid_orch_list",
                "grid_search": {
                    "type": "base_grid_search",
                    "search_space": [
                        {"type": "base_grid", "keys": ["a", "b"], "values": [1, 2]},
                        {"type": "id_grid", "keys": "c", "value": 3},
                        {
                            "type": "base_grid_search",
                            "search_space": [
                                {
                                    "type": "base_grid",
                                    "keys": ["d", "e"],
                                    "values": [4, 5],
                                }
                            ],
                        },
                    ],
                },
            }
        ),
    ),
    (
        GridOrchestrator,
        GridNestedList,
        Params(
            {
                "type": "grid_orch_nested_list",
                "grid_search": {
                    "type": "base_grid_search",
                    "search_space": [
                        {"type": "base_grid", "keys": ["a", "b"], "values": [1, 2]},
                        {"type": "id_grid", "keys": "c", "value": 3},
                        {
                            "type": "base_grid_search",
                            "search_space": [
                                {
                                    "type": "base_grid",
                                    "keys": ["d", "e"],
                                    "values": [4, 5],
                                }
                            ],
                        },
                    ],
                },
            }
        ),
    ),
]


GRID_ORCH_INPUT_CALL_LIST = [
    (
        Organize,
        Params({"type": "id_organize"}),
        [{"a.b": 2}, {"a.b": -1}, {"a.b": 3}],
        [{"a.b": 2}, {"a.b": -1}, {"a.b": 3}],
    ),
    (
        Organize,
        Params({"type": "sort_organize", "keys": "a.b"}),
        [{"a.b": 2}, {"a.b": -1}, {"a.b": 3}],
        [{"a.b": -1}, {"a.b": 2}, {"a.b": 3}],
    ),
    (
        Organize,
        Params({"type": "sort_organize", "keys": ["a.b", "c"]}),
        [
            {"a.b": 2, "c": 0},
            {"a.b": -1, "c": 2},
            {"a.b": -1, "c": 0},
            {"a.b": 3, "c": 3},
        ],
        [
            {"a.b": -1, "c": 0},
            {"a.b": -1, "c": 2},
            {"a.b": 2, "c": 0},
            {"a.b": 3, "c": 3},
        ],
    ),
    (
        Group,
        Params({"type": "group_by", "keys": ["a.b"]}),
        [
            {"a.b": 2, "c": 0},
            {"a.b": -1, "c": 2},
            {"a.b": -1, "c": 0},
            {"a.b": 3, "c": 3},
        ],
        [
            [{"a.b": -1, "c": 2}, {"a.b": -1, "c": 0}],
            [{"a.b": 2, "c": 0}],
            [{"a.b": 3, "c": 3}],
        ],
    ),
]


GRID_ORCH_CALL_LIST = [
    (
        GridOrchestrator,
        Params(
            {
                "type": "grid_orch_list",
                "grid_search": {
                    "type": "base_grid_search",
                    "search_space": [
                        {"type": "base_grid", "keys": ["a", "b"], "values": [1, 2]},
                        {"type": "id_grid", "keys": "c", "value": 3},
                        {
                            "type": "base_grid_search",
                            "search_space": [
                                {
                                    "type": "base_grid",
                                    "keys": ["d", "e"],
                                    "values": [4, 5],
                                }
                            ],
                        },
                    ],
                },
            }
        ),
        [
            {"a": 1, "b": 1, "c": 3, "d": 4, "e": 4},
            {"a": 1, "b": 1, "c": 3, "d": 5, "e": 5},
            {"a": 2, "b": 2, "c": 3, "d": 4, "e": 4},
            {"a": 2, "b": 2, "c": 3, "d": 5, "e": 5},
        ],
    ),
    (
        GridOrchestrator,
        Params(
            {
                "type": "grid_orch_list",
                "grid_search": {
                    "type": "base_grid_search",
                    "search_space": [
                        {"type": "base_grid", "keys": ["a", "b"], "values": [1, 2]},
                        {"type": "id_grid", "keys": "c", "value": 3},
                        {
                            "type": "base_grid_search",
                            "search_space": [
                                {
                                    "type": "base_grid",
                                    "keys": ["d", "e"],
                                    "values": [4, 5],
                                }
                            ],
                        },
                    ],
                },
                "organize": {"type": "sort_organize", "keys": ["d", "e"]},
            }
        ),
        [
            {"a": 1, "b": 1, "c": 3, "d": 4, "e": 4},
            {"a": 2, "b": 2, "c": 3, "d": 4, "e": 4},
            {"a": 1, "b": 1, "c": 3, "d": 5, "e": 5},
            {"a": 2, "b": 2, "c": 3, "d": 5, "e": 5},
        ],
    ),
    (
        GridOrchestrator,
        Params(
            {
                "type": "grid_orch_nested_list",
                "grid_search": {
                    "type": "base_grid_search",
                    "search_space": [
                        {"type": "base_grid", "keys": ["a", "b"], "values": [1, 2]},
                        {"type": "id_grid", "keys": "c", "value": 3},
                        {
                            "type": "base_grid_search",
                            "search_space": [
                                {
                                    "type": "base_grid",
                                    "keys": ["d", "e"],
                                    "values": [4, 5],
                                }
                            ],
                        },
                    ],
                },
            }
        ),
        [
            [{"a": 1, "b": 1, "c": 3, "d": 4, "e": 4}],
            [{"a": 1, "b": 1, "c": 3, "d": 5, "e": 5}],
            [{"a": 2, "b": 2, "c": 3, "d": 4, "e": 4}],
            [{"a": 2, "b": 2, "c": 3, "d": 5, "e": 5}],
        ],
    ),
    (
        GridOrchestrator,
        Params(
            {
                "type": "grid_orch_nested_list",
                "grid_search": {
                    "type": "base_grid_search",
                    "search_space": [
                        {"type": "base_grid", "keys": ["a", "b"], "values": [1, 2]},
                        {"type": "id_grid", "keys": "c", "value": 3},
                        {
                            "type": "base_grid_search",
                            "search_space": [
                                {
                                    "type": "base_grid",
                                    "keys": ["d", "e"],
                                    "values": [4, 5],
                                }
                            ],
                        },
                    ],
                },
                "group": {"type": "group_by", "keys": ["d", "e"]},
            }
        ),
        [
            [
                {"a": 1, "b": 1, "c": 3, "d": 4, "e": 4},
                {"a": 2, "b": 2, "c": 3, "d": 4, "e": 4},
            ],
            [
                {"a": 1, "b": 1, "c": 3, "d": 5, "e": 5},
                {"a": 2, "b": 2, "c": 3, "d": 5, "e": 5},
            ],
        ],
    ),
]


@pytest.fixture(params=STR_TO_LIST)
def str_to_list(request):
    return request.param


@pytest.fixture(params=TUPLE_TO_DICT)
def tuple_to_dict(request):
    return request.param


@pytest.fixture
def orchestrator():
    return ORCHESTRATOR


@pytest.fixture(params=SEARCH_ELEMENT_PARAM_LIST + GRID_ORCH_PARAMS)
def from_obj_params(request):
    return request.param


@pytest.fixture(params=SEARCH_ELEMENT_PARAM_LIST)
def len_params(request):
    return request.param


@pytest.fixture(params=CALL_LIST)
def call(request):
    return request.param


@pytest.fixture(params=GRID_ORCH_INPUT_CALL_LIST)
def grid_orch_input_call(request):
    return request.param


@pytest.fixture(params=GRID_ORCH_CALL_LIST)
def grid_orch_call(request):
    return request.param


@pytest.fixture
def file_grid_search_call():
    directory = mkdtemp()
    filenames = []
    output = []
    for en, i in enumerate(["a", "b", "c"]):
        dct = {i: en}
        filename = op.join(directory, f"{i}.json")
        Params(dct).to_file(filename)
        filenames.append(filename)
        output.append(dct)
    yield Params({"type": "file_grid_search", "filenames": filenames}), output
    rmtree(directory)


def test_str_to_list(str_to_list):
    input, output = str_to_list
    assert GridElement.str_to_list(input) == output


def test_tuple_to_dict(tuple_to_dict):
    input, output = tuple_to_dict
    assert GridSearch.tuple_to_dict(input) == output


def test_from_obj(orchestrator, from_obj_params):
    target_cls, instance_cls, params, *_ = from_obj_params
    assert isinstance(orchestrator.from_obj(target_cls, params), instance_cls)


def test_len(orchestrator, len_params):
    target_cls, _, params, length = len_params
    obj = orchestrator.from_obj(target_cls, params)
    assert len(obj) == length


def test___call__(orchestrator, call):
    target_cls, params, output = call
    obj = orchestrator.from_obj(target_cls, params)
    assert obj() == output


def test_file_grid_search___call__(orchestrator, file_grid_search_call):
    params, output = file_grid_search_call
    obj = orchestrator.from_obj(GridSearch, params)
    assert obj() == output


def test_grid_orch_input___call__(orchestrator, grid_orch_input_call):
    target_cls, params, input, output = grid_orch_input_call
    obj = orchestrator.from_obj(target_cls, params)
    assert obj(input) == output


def test_grid_orch___call__(orchestrator, grid_orch_call):
    target_cls, params, output = grid_orch_call
    obj = orchestrator.from_obj(target_cls, params)
    assert obj() == output
