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
"""State from the constructor for a parameter from the constructor."""
from typing import Any
from typing import Dict
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from adorn.unit.complex import _UnitT


class Parameter:
    """State for a parameter from a given :class:`~adorn.data.constructor.Constructor`

    ``Parameter`` allows for information outside of its ``obj``, to be utilized,
    to perform some action.  Examples of constructs that utilize the information
    contained in ``Parameter`` include:

    - :class:`~adorn.unit.parameter_value.DependentTypeCheck`
    - :class:`~adorn.unit.parameter_value.DependentFromObj`
    - :class:`~adorn.unit.parameter_value.DependentUnion`

    Attributes:
        cls (_UnitT): the type of the underlying parameter
        parent (_UnitT): The type of object whose constructor requires
            an object of type ``cls``
        local_state (Dict[str, Any]): Information about other arguments
            provided to the given constructor
        parameter_name (str): name of the parameter in the constructor
    """

    def __init__(
        self,
        cls: "_UnitT",
        parent: "_UnitT",
        local_state: Dict[str, Any],
        parameter_name: str,
    ):
        self.cls = cls
        self.parent = parent
        self.local_state = local_state
        self.parameter_name = parameter_name
        self.origin = getattr(self.cls, "__origin__", None)
        self.args = getattr(self.cls, "__args__", None)

    def __eq__(self, o: object) -> bool:  # noqa: C901
        # Literal.__eq__ doesn't support dict's so
        # we force the check
        # prevent circular import
        from adorn.unit.parameter_value import Dependent

        if not isinstance(o, Parameter):
            return False

        normal_args = all(
            i
            for i in [
                self.parent == o.parent,
                self.local_state == o.local_state,
                self.parameter_name == o.parameter_name,
            ]
        )
        if not normal_args:
            return False

        eq_cls = False
        if issubclass(getattr(self.cls, "__origin__", int), Dependent):
            eq_cls = str(self.cls) == str(o.cls)
        else:
            eq_cls = self.cls == o.cls
        return eq_cls

    def __str__(self):
        return str(self.cls)
