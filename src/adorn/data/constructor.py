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
"""A container of information relevant for constructing an object."""
import inspect
from dataclasses import dataclass
from typing import Callable
from typing import Dict
from typing import Type
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from adorn.unit.complex import _T, _UnitT


@dataclass
class Constructor:
    """Container holding the class and relevant metadata to construct an object.

    Args:
        subclass (_UnitT): The ``type`` to generate construction metadata for
    """

    subclass: "_UnitT"

    def __post_init__(self):
        self.constructor_type = getattr(self.subclass, "constructor_type", None)
        if hasattr(self.subclass, "by_name"):
            self.constructor = self.subclass.by_name()
            constructor = (
                self.constructor
                if self.constructor.constructor_name is None
                else getattr(self.constructor, self.constructor.constructor_name)
            )
        else:
            self.constructor = self.subclass
            constructor = self.constructor
        self.parameters = self.infer_params(self.subclass, constructor)
        self.parameter_order = getattr(self.subclass, "parameter_order", None)

    def infer_params(
        self, target_class: Type["_T"], constructor: Callable[..., "_T"]
    ) -> Dict[str, inspect.Parameter]:
        """Generate a dict containing all the parameters needed to instantiate ``subclass``.

        This method is recursive and will convert ``**kwargs``, specified in the constructor,
        to the relevant parameters of its parent class(es), given the parent(s)
        subclass :class:`~adorn.unit.complex.Complex`

        Args:
            target_class (Type["_T"]): The class you are interegating the constructor of.
                This argument is used to explode the ``**kwargs``
            constructor (Callable[..., "_T"]): The method, whose parameters will be added
                to a dictionary

        Returns:
            Dict[str, inspect.Parameter]: constructor parameters as a dict
                keys are the parameter names and values are the parameter metadata
        """  # noqa:B950
        # circular imports
        from adorn.unit.complex import Complex

        signature = inspect.signature(constructor)
        parameters = dict(signature.parameters)

        parameters.pop("self", None)

        has_kwargs = False
        var_positional_key = None
        for param in parameters.values():
            if param.kind == param.VAR_KEYWORD:
                has_kwargs = True
            elif param.kind == param.VAR_POSITIONAL:
                var_positional_key = param.name

        if var_positional_key:
            del parameters[var_positional_key]

        if not has_kwargs:
            return parameters
        # probably only want to do this when the associated type is inspect._empty
        parameters.pop("kwargs")
        # "mro" is "method resolution order".  The first one is the current class,
        # the next is the first superclass, and so on.  We take the first
        # superclass we find that inherits from Complex.
        super_class = None
        # we could probably use the Complex's parent method
        # to help filter the mro output
        for super_class_candidate in target_class.mro()[1:]:
            if issubclass(super_class_candidate, Complex):
                super_class = super_class_candidate
                break
        if super_class:
            super_parameters = self.infer_params(super_class, super_class.by_name())
        else:
            super_parameters = {}

        return {
            **super_parameters,
            **parameters,
        }  # Subclass parameters overwrite superclass ones
