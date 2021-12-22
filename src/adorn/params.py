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
"""Params: a glorified dictionary"""
import copy
import json
import logging
import zlib
from collections import OrderedDict
from collections.abc import MutableMapping
from os import PathLike
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from adorn.exception.configuration_error import ConfigurationError

logger = logging.getLogger(__name__)


def infer_and_cast(value: Any) -> Any:  # noqa:C901
    """In some cases we'll be feeding params dicts to functions we don't own

    For example, PyTorch optimizers. In that case we can't use `pop_int`
    or similar to force casts (which means you can't specify `int` parameters
    using environment variables). This function takes something that looks JSON-like
    and recursively casts things that look like (bool, int, float) to
    (bool, int, float).
    """
    if isinstance(value, (int, float, bool)):
        # Already one of our desired types, so leave as is.
        return value
    elif isinstance(value, list):
        # Recursively call on each list element.
        return [infer_and_cast(item) for item in value]
    elif isinstance(value, dict):
        # Recursively call on each dict value.
        return {key: infer_and_cast(item) for key, item in value.items()}
    elif isinstance(value, str):
        # If it looks like a bool, make it a bool.
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        else:
            # See if it could be an int.
            try:
                return int(value)
            except ValueError:
                pass
            # See if it could be a float.
            try:
                return float(value)
            except ValueError:
                # Just return it as a string.
                return value
    else:
        raise ValueError(f"cannot infer type of {value}")


def unflatten(flat_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Given a "flattened" dict with compound keys, e.g.

    ``{"a.b": 0}`` after unflatten, ``{"a": {"b": 0}}``
    """
    unflat: Dict[str, Any] = {}

    for compound_key, value in flat_dict.items():
        curr_dict = unflat
        parts = compound_key.split(".")
        for key in parts[:-1]:
            curr_value = curr_dict.get(key)
            if key not in curr_dict:
                curr_dict[key] = {}
                curr_dict = curr_dict[key]
            elif isinstance(curr_value, dict):
                curr_dict = curr_value
            else:
                raise ConfigurationError("flattened dictionary is invalid")
        if not isinstance(curr_dict, dict) or parts[-1] in curr_dict:
            raise ConfigurationError("flattened dictionary is invalid")
        curr_dict[parts[-1]] = value

    return unflat


def _is_dict_free(obj: Any) -> bool:
    """Returns False if obj is a dict, otherwise list with an element that _has_dict."""
    if isinstance(obj, dict):
        return False
    elif isinstance(obj, list):
        return all(_is_dict_free(item) for item in obj)
    else:
        return True


class Params(MutableMapping):
    """Represents a parameter dictionary with a history.

    Contains other functionality around parameter passing and validation for Adorn.
    There are currently two benefits of a `Params` object over a plain dictionary for
    parameter passing:

    1. We handle a few kinds of parameter validation, including making sure that
       parameters representing discrete choices actually have acceptable values,
       and making sure no extra parameters are passed.
    2. We log all parameter reads, including default values.  This gives a more
       complete specification of the actual parameters used than is given in a JSON
       file, because those may not specify what default values were used, whereas
       this will log them.
    """

    # This allows us to check for the presence of "None" as a default argument,
    # which we require because we make a distinction between passing a value of "None"
    # and passing no value to the default parameter of "pop".
    DEFAULT = object()

    def __init__(self, params: Dict[str, Any], history: str = "") -> None:
        self.params = _replace_none(params)
        self.history = history

    def pop(self, key: str, default: Any = DEFAULT, keep_as_dict: bool = False) -> Any:
        """Performs the functionality associated with dict.pop(key).

        Along with checking for returned dictionaries, replacing them
        with Param objects with an updated history (unless keep_as_dict is True, in
        which case we leave them as dictionaries). If `key` is not present in the
        dictionary, and no default was specified, we raise a `ConfigurationError`,
        instead of the typical `KeyError`.
        """  # noqa:D402
        if default is self.DEFAULT:
            try:
                value = self.params.pop(key)
            except KeyError:
                msg = f'key "{key}" is required'
                if self.history:
                    msg += f' at location "{self.history}"'
                raise ConfigurationError(msg) from KeyError
        else:
            value = self.params.pop(key, default)

        if keep_as_dict or _is_dict_free(value):
            logger.info(f"{self.history}{key} = {value}")
            return value
        else:
            return self._check_is_dict(key, value)

    def pop_int(self, key: str, default: Any = DEFAULT) -> Optional[int]:
        """Performs a pop and coerces to an int."""
        value = self.pop(key, default)
        if value is None:
            return None
        else:
            return int(value)

    def pop_float(self, key: str, default: Any = DEFAULT) -> Optional[float]:
        """Performs a pop and coerces to a float."""
        value = self.pop(key, default)
        if value is None:
            return None
        else:
            return float(value)

    def pop_bool(self, key: str, default: Any = DEFAULT) -> Optional[bool]:
        """Performs a pop and coerces to a bool."""
        value = self.pop(key, default)
        if value is None:
            return None
        elif isinstance(value, bool):
            return value
        elif value == "true":
            return True
        elif value == "false":
            return False
        else:
            raise ValueError(f"Cannot convert variable to bool: {value}")

    def get(self, key: str, default: Any = DEFAULT) -> Any:
        """Performs the functionality associated with dict.get(key).

        Also checks for returned dicts and returns a Params object in
        their place with an updated history.
        """  # noqa:D402
        default = None if default is self.DEFAULT else default
        value = self.params.get(key, default)
        return self._check_is_dict(key, value)

    def pop_choice(
        self,
        key: str,
        choices: List[Any],
        default_to_first_choice: bool = False,
        allow_class_names: bool = True,
    ) -> Any:
        """Gets the value of `key` in the `params` dictionary,

        Ensuring that the value is one of the given choices. Note that
        this `pops` the key from params, modifying the dictionary,
        consistent with how parameters are processed in this codebase.

        Args:
            key (str): Key to get the value from in the param dictionary
            choices (List[Any]): A list of valid options for values corresponding to `key`.
                For example, if you're specifying the type of encoder to use for some part
                of your model, the choices might be the list of encoder classes we know
                about and can instantiate.  If the value we find in the param dictionary
                is not in `choices`, we raise a `ConfigurationError`, because
                the user specified an invalid value in their parameter file.
            default_to_first_choice (bool): If this is `True`, we allow the `key` to not be
                present in the parameter dictionary.  If the key is not present, we will
                use the return as the value the first choice in the `choices` list.
                If this is `False`, we raise a `ConfigurationError`, because
                specifying the `key` is required (e.g., you `have` to specify
                your model class when running an experiment, but you can
                feel free to usedefault settings for encoders if you want).
            allow_class_names (bool): If this is `True`, then we allow unknown
                choices that look like fully-qualified class names.
                This is to allow e.g. specifying a model type
                as my_library.my_model.MyModel and importing it on the fly. Our check for
                "looks like" is extremely lenient and consists of checking that the value
                contains a '.'.

        Returns:
            Any: value which was one of the listed ``choices``

        Raises:
            ConfigurationError: requested a key that DNE
        """  # noqa: B950
        default = choices[0] if default_to_first_choice else self.DEFAULT
        value = self.pop(key, default)
        ok_because_class_name = allow_class_names and "." in value
        if value not in choices and not ok_because_class_name:
            key_str = self.history + key
            message = (
                f"{value} not in acceptable choices for {key_str}: {choices}. "
                "You should either use the --include-package flag to make "
                "sure the correct module is loaded, or use a fully qualified "
                "class name in your config file like "
                """{"model": "my_module.models.MyModel"} """
                "to have it imported automatically."
            )
            raise ConfigurationError(message)
        return value

    def as_dict(
        self, quiet: bool = False, infer_type_and_cast: bool = False
    ) -> Dict[str, Any]:
        """Sometimes we need to just represent the parameters as a dict.

        For instance when we pass them to PyTorch code.

        Args:
            quiet (bool): Whether to log the parameters before
                returning them as a dict.
            infer_type_and_cast (bool): If True, we infer types and cast
                (e.g. things that look like floats to floats).

        Returns:
            Dict[str, Any]: dict containing the content of ``Params``
        """
        if infer_type_and_cast:
            params_as_dict = infer_and_cast(self.params)
        else:
            params_as_dict = self.params

        if quiet:
            return params_as_dict

        def log_recursively(parameters, history):
            for key, value in parameters.items():
                if isinstance(value, dict):
                    new_local_history = history + key + "."
                    log_recursively(value, new_local_history)
                else:
                    logger.info(f"{history}{key} = {value}")

        log_recursively(self.params, self.history)
        return params_as_dict

    def as_flat_dict(self) -> Dict[str, Any]:
        """Returns the parameters of a flat dictionary from keys to values.

        Nested structure is collapsed with periods.
        """
        flat_params = {}

        def recurse(parameters, path):
            for key, value in parameters.items():
                newpath = path + [key]
                if isinstance(value, dict):
                    recurse(value, newpath)
                else:
                    flat_params[".".join(newpath)] = value

        recurse(self.params, [])
        return flat_params

    def duplicate(self) -> "Params":
        """Uses `copy.deepcopy()` to create a duplicate (but fully distinct)

        copy of these Params.
        """  # noqa:D402
        return copy.deepcopy(self)

    def assert_empty(self, class_name: str) -> None:
        """Raises a `ConfigurationError` if `self.params` is not empty.

        We take `class_name` as an argument so that the error message
        gives some idea of where an error happened, if there was one.
        `class_name` should be the name of the `calling` class,
        the one that got extra parameters (if there are any).
        """
        if self.params:
            raise ConfigurationError(
                "Extra parameters passed to {}: {}".format(class_name, self.params)
            )

    def __getitem__(self, key) -> Any:
        if key in self.params:
            return self._check_is_dict(key, self.params[key])
        else:
            raise KeyError

    def __setitem__(self, key, value) -> None:
        self.params[key] = value

    def __delitem__(self, key) -> None:
        del self.params[key]

    def __iter__(self):
        return iter(self.params)

    def __len__(self) -> int:
        return len(self.params)

    def _check_is_dict(self, new_history, value) -> Union["Params", List["Params"]]:
        if isinstance(value, dict):
            new_history = self.history + new_history + "."
            return Params(value, history=new_history)
        if isinstance(value, list):
            value = [
                self._check_is_dict(f"{new_history}.{i}", v)
                for i, v in enumerate(value)
            ]
        return value

    @classmethod
    def from_file(
        cls,
        params_file: Union[str, PathLike],
    ) -> "Params":
        """Load a `Params` object from a configuration file.

        Args:
            params_file (str): The path to the configuration file to load.

        Returns:
            Params: content of the file wrapped in a ``Params``
        """
        params_file = str(params_file)
        with open(params_file) as file_handle:
            file_dict = json.loads(file_handle.read())
        return cls(file_dict)

    def to_file(self, params_file: str) -> None:
        """Writes params object to disk as a json"""
        with open(params_file, "w") as handle:
            json.dump(self.as_ordered_dict(), handle, indent=4)

    def as_ordered_dict(self) -> OrderedDict:
        """Returns Ordered Dict of Params from list of partial order preferences."""
        params_dict = self.as_dict(quiet=True)

        def order_dict(dictionary):
            # Recursively orders dictionary according to scoring order_func
            result = OrderedDict()
            for key, val in sorted(dictionary.items(), key=lambda item: item[0]):
                result[key] = order_dict(val) if isinstance(val, dict) else val
            return result

        return order_dict(params_dict)

    def get_hash(self) -> str:
        """Returns a hash code representing the current state of this `Params` object.

        We don't want to implement `__hash__` because that has deeper python
        implications (and this is a mutable object), but this will give you a
        representation of the current state. We use `zlib.adler32` instead of Python's
        builtin `hash` because the random seed for the latter is reset on each new
        program invocation, as discussed here:
        https://stackoverflow.com/questions/27954892/deterministic-hashing-in-python-3.
        """
        dumped = json.dumps(self.params, sort_keys=True)
        hashed = zlib.adler32(dumped.encode())
        return str(hashed)

    def __str__(self) -> str:
        return f"{self.history}Params({self.params})"

    def left_merge(self, rhs: Union["Params", Dict[str, Any]]) -> Dict[str, Any]:
        """Inject values from a new config into the current config

        Args:
            rhs (Union[Params, Dict[str, Any]]): configuration, where its values
                will be injected into the current config

        Returns:
            Dict[str, Any]: flattened version of the original config that includes
                values from the passed config, ``rhs``
        """
        self_flat_dict = self.as_flat_dict()
        rhs_flat_dict = (
            rhs.as_flat_dict()
            if isinstance(rhs, Params)
            else Params(rhs).as_flat_dict()
        )
        for k, v in rhs_flat_dict.items():
            self_flat_dict[k] = v
        return self_flat_dict


def _replace_none(params: Any) -> Any:
    if params == "None":
        return None
    elif isinstance(params, dict):
        for key, value in params.items():
            params[key] = _replace_none(value)
        return params
    elif isinstance(params, list):
        return [_replace_none(value) for value in params]
    return params
