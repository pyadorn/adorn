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
import json
import re
from collections import OrderedDict
from typing import Optional
from typing import Union

import pytest
import yaml

from adorn.exception.configuration_error import ConfigurationError
from adorn.params import _is_dict_free
from adorn.params import infer_and_cast
from adorn.params import Params
from adorn.params import unflatten


LEFT_MERGE = [
    (
        Params({"a": 0, "b": {"c": 1, "d": 2, "e": {"f": 3, "g": 4}}}),
        dict(),
        {"a": 0, "b.c": 1, "b.d": 2, "b.e.f": 3, "b.e.g": 4},
    ),
    (
        Params({"a": 0, "b": {"c": 1, "d": 2, "e": {"f": 3, "g": 4}}}),
        Params({}),
        {"a": 0, "b.c": 1, "b.d": 2, "b.e.f": 3, "b.e.g": 4},
    ),
    (
        Params({"a": 0, "b": {"c": 1, "d": 2, "e": {"f": 3, "g": 4}}}),
        {"a": 5, "b.d": 6, "b.e.f": 7},
        {"a": 5, "b.c": 1, "b.d": 6, "b.e.f": 7, "b.e.g": 4},
    ),
    (
        Params({"a": 0, "b": {"c": 1, "d": 2, "e": {"f": 3, "g": 4}}}),
        Params({"a": 5, "b.d": 6, "b.e.f": 7}),
        {"a": 5, "b.c": 1, "b.d": 6, "b.e.f": 7, "b.e.g": 4},
    ),
    (
        Params({"a": 0, "b": {"c": 1, "d": 2, "e": {"f": 3, "g": 4}}}),
        {"a": 5, "b": {"d": 6, "e": {"f": 7, "h": 8}, "i": 9}, "j": 10},
        {
            "a": 5,
            "b.c": 1,
            "b.d": 6,
            "b.e.f": 7,
            "b.e.g": 4,
            "b.e.h": 8,
            "b.i": 9,
            "j": 10,
        },
    ),
    (
        Params({"a": 0, "b": {"c": 1, "d": 2, "e": {"f": 3, "g": 4}}}),
        Params({"a": 5, "b": {"d": 6, "e": {"f": 7, "h": 8}, "i": 9}, "j": 10}),
        {
            "a": 5,
            "b.c": 1,
            "b.d": 6,
            "b.e.f": 7,
            "b.e.g": 4,
            "b.e.h": 8,
            "b.i": 9,
            "j": 10,
        },
    ),
]


@pytest.fixture(params=LEFT_MERGE)
def left_merge(request):
    return request.param


def test_left_merge(left_merge):
    params, rhs, output = left_merge
    assert params.left_merge(rhs) == output


def test_load_from_file(tmpdir):
    dct = {"a": 0, "b": 1, "c": {"d": 2}}
    file_content = tmpdir.mkdir("sub").join("temp.json")
    file_content.write(json.dumps(dct))
    params = Params.from_file(file_content)

    assert "a" in params
    assert "b" in params

    model_params = params.pop("c")
    assert model_params.pop("d") == 2


def test_replace_none():
    params = Params({"a": "None", "b": [1.0, "None", 2], "c": {"d": "None"}})
    assert params["a"] is None
    assert params["b"][1] is None
    assert params["c"]["d"] is None


def test_unflatten():
    flattened = {"a.b.c": 1, "a.b.d": 0, "a.e.f.g.h": 2, "b": 3}
    unflattened = unflatten(flattened)
    assert unflattened == {
        "a": {"b": {"c": 1, "d": 0}, "e": {"f": {"g": {"h": 2}}}},
        "b": 3,
    }

    # should do nothing to a non-flat dictionary
    assert unflatten(unflattened) == unflattened


def test_unflatten_configuration_error_cur_dict():
    with pytest.raises(ConfigurationError):
        unflatten({"a.b": 1, "a": {"b": 2}})


def test_unflatten_configuration_error_cur_value():
    with pytest.raises(ConfigurationError):
        unflatten({"a.b": 1, "a.b.c": []})


def test_as_flat_dict():
    params = Params({"a": 10, "b": {"c": 20, "d": "stuff"}}).as_flat_dict()
    assert params == {"a": 10, "b.c": 20, "b.d": "stuff"}


def test_regexes_with_backslashes(tmp_path):
    bad_regex = tmp_path / "bad_regex.json"
    good_regex = tmp_path / "good_regex.json"

    with open(bad_regex, "w") as f:
        f.write(r'{"myRegex": "a\.b"}')

    with open(good_regex, "w") as f:
        f.write(r'{"myRegex": "a\\.b"}')

    with pytest.raises(json.decoder.JSONDecodeError):
        Params.from_file(bad_regex)

    params = Params.from_file(good_regex)
    regex = params["myRegex"]

    assert re.match(regex, "a.b")
    assert not re.match(regex, "a-b")

    # Check roundtripping
    good_regex2 = tmp_path / "good_regex2.json"
    with open(good_regex2, "w") as f:
        f.write(json.dumps(params.as_dict()))
    params2 = Params.from_file(good_regex2)

    assert params.as_dict() == params2.as_dict()


def test_as_ordered_dict():
    params = Params(
        {
            "keyC": "valC",
            "keyB": "valB",
            "keyA": "valA",
            "keyE": "valE",
            "keyD": {"keyDB": "valDB", "keyDA": "valDA"},
        }
    )
    ordered_params_dict = params.as_ordered_dict()
    expected_ordered_params_dict = OrderedDict(
        {
            "keyA": "valA",
            "keyB": "valB",
            "keyC": "valC",
            "keyD": {"keyDA": "valDA", "keyDB": "valDB"},
            "keyE": "valE",
        }
    )
    assert json.dumps(ordered_params_dict) == json.dumps(expected_ordered_params_dict)


def test_to_file(tmp_path):
    # Test to_file works with or without preference orders
    params_dict = {"keyA": "valA", "keyB": "valB"}
    expected_ordered_params_dict = OrderedDict(params_dict)
    params = Params(params_dict)
    file_path = tmp_path / "config.json"
    # check with preference orders
    params.to_file(file_path)
    with open(file_path, "r") as handle:
        ordered_params_dict = OrderedDict(json.load(handle))
    assert json.dumps(expected_ordered_params_dict) == json.dumps(ordered_params_dict)


@pytest.mark.parametrize(
    "params",
    [
        Params({"a": "b", "c": "d"}),
        Params({"a": {"b": "c"}, "d": Params({"e": "f"})}),
        Params({"a": {"b": "c"}, "d": Params({"e": Params({"f": "g"})})}),
        Params({"a": {"b": "c"}, "d": [Params({"e": Params({"f": "g"})})]}),
    ],
)
def test_to_file_from_file(tmp_path, params):
    file_path = tmp_path / "config.json"
    params.to_file(file_path)
    assert Params.from_file(file_path) == params


def test_from_file_yaml(tmp_path):
    file_path = tmp_path / "config.yaml"
    dct = dict(a=0, b=1, c=2)
    with open(file_path, "w") as fh:
        fh.write(yaml.dump(dct))
    p = Params.from_file(file_path)
    assert dct == p.as_dict()


def test_from_file_toml(tmp_path):
    file_path = tmp_path / "config.toml"
    toml_str = """
    [[players]]
    name = "Lehtinen"
    number = 26

    [[players]]
    name = "Numminen"
    number = 27
    """
    with open(file_path, "w") as fh:
        fh.write(toml_str)
    p = Params.from_file(file_path)
    assert p.as_dict() == {
        "players": [
            {"name": "Lehtinen", "number": 26},
            {"name": "Numminen", "number": 27},
        ]
    }


def test__is_dict_free_list():
    assert _is_dict_free([1, 2, 3, [3, 4, 5]])


def test_infer_and_cast():
    lots_of_strings = {
        "a": ["10", "1.3", "true"],
        "b": {"x": 10, "y": "20.1", "z": "other things"},
        "c": "just a string",
        "d": "false",
    }

    casted = {
        "a": [10, 1.3, True],
        "b": {"x": 10, "y": 20.1, "z": "other things"},
        "c": "just a string",
        "d": False,
    }

    assert infer_and_cast(lots_of_strings) == casted

    contains_bad_data = {"x": 10, "y": int}
    with pytest.raises(ValueError, match="cannot infer type"):
        infer_and_cast(contains_bad_data)

    params = Params(lots_of_strings)
    assert params.as_dict() == lots_of_strings
    assert params.as_dict(infer_type_and_cast=True) == casted


def test_pop_exception():
    params = Params({"a": 1})
    with pytest.raises(ConfigurationError) as e:  # noqa: B908
        params.pop("b")
        assert e == 'key "b" is required'


def test_pop_exception_history():
    params = Params({"a": 1}, history="blah")
    with pytest.raises(ConfigurationError) as e:  # noqa: B908
        params.pop("b")
        assert "blah" in e


@pytest.mark.parametrize(
    "method_name,params,target",
    [
        ("pop_int", Params({"a": "1"}), 1),
        ("pop_int", Params({"a": None}), None),
        ("pop_float", Params({"a": "1.1"}), 1.1),
        ("pop_float", Params({"a": None}), None),
        ("pop_bool", Params({"a": None}), None),
        ("pop_bool", Params({"a": True}), True),
        ("pop_bool", Params({"a": "true"}), True),
        ("pop_bool", Params({"a": "false"}), False),
    ],
)
def test_pop_type(
    method_name: str, params: Params, target: Optional[Union[int, float, bool]]
):
    assert getattr(params, method_name)("a") == target


def test_pop_bool_value_error():
    with pytest.raises(ValueError):
        Params({"a": 1}).pop_bool("a")


def test_assert_empty_error():
    with pytest.raises(ConfigurationError):
        Params({"a": 1}).assert_empty("who_cares")


def test_assert_empty():
    assert Params(dict()).assert_empty("yes") is None


def test___delitem__():
    dct = {"b": 2}
    params = Params({"a": 1, **dct})
    params.__delitem__("a")
    assert params == Params(dct)


def test___len__():
    n = 10
    params = Params({i: i for i in range(n)})
    assert len(params) == n


def test_get_hash():
    p0 = Params({"a": 1})
    p1 = Params({"a": 1})
    p2 = Params({"a": 2})
    assert p0.get_hash() == p1.get_hash()
    assert p0.get_hash() != p2.get_hash()


def test_pop_choice():
    choices = ["my_model", "other_model"]
    params = Params({"model": "my_model"})
    assert params.pop_choice("model", choices) == "my_model"

    params = Params({"model": "non_existent_model"})
    with pytest.raises(ConfigurationError):
        params.pop_choice("model", choices)

    params = Params({"model": "module.submodule.ModelName"})
    assert params.pop_choice("model", "choices") == "module.submodule.ModelName"

    params = Params({"model": "module.submodule.ModelName"})
    with pytest.raises(ConfigurationError):
        params.pop_choice("model", choices, allow_class_names=False)
