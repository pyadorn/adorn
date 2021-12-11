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
"""Subclass of :class:`~adorn.unit.complex.Complex` to specify alternate construction of a class"""  # noqa: B950
from typing import Any
from typing import Optional
from typing import Type
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from adorn.orchestrator.orchestrator import Orchestrator

from adorn.data.constructor import Constructor
from adorn.exception.type_check_error import TypeCheckError
from adorn.params import Params
from adorn.unit.complex import Complex


class Template(Complex):
    """Subclass of :class:`~adorn.unit.complex.Complex` to specify alternate construction of a class

    This construct allows for you to specify a different way of constructing
    an instance of :class:`~adorn.unit.complex.Complex`, without having
    to add an additional method to the given class of
    :class:`~adorn.unit.complex.Complex`.  This is especially useful
    for creating configurable constructs, that reduces parameters,
    while still covering most use cases.

    .. note

        The constructor for this class will be passed values from the configuration that
        haven't been instantiated.
    """  # noqa: B950

    @property
    def params(self) -> Params:
        """Configuration for the object being shadowed"""
        return self._params.duplicate()

    @property
    def _params(self) -> Params:  # pragma: no cover
        """Specifies a configuration for a class

        Raises:
            NotImplementedError: subclasses must override this method
        """
        raise NotImplementedError

    @classmethod
    def _type_check(
        cls, target_cls: Type, orchestrator: "Orchestrator", obj: Any
    ) -> Optional[TypeCheckError]:
        """Check the arguments for the ``Template``

        Args:
            target_cls (Type): the target Type, the given ``Template`` will
                generate
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): an instance, that will be checked to see if it
                can instantiate the ``Template``

        Returns:
            Optional[TypeCheckError]: Errors that would prevent you from instantiating
                the ``Template`` or the underlying ``target_cls`` that
                the ``Template`` generates an instance of, otherwise ``None``
        """  # noqa: B950
        return orchestrator.type_check(Constructor(cls), obj)

    @classmethod
    def _from_obj(cls, target_cls: Type, orchestrator: "Orchestrator", obj: Any) -> Any:
        """Instantiate the ``Template``, then use :attr:`~adorn.unit.template.Template.params` to instantiate an instance of ``target_cls``

        Args:
            target_cls (Type): the target Type, the given ``Template`` will
                generate
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): an instance, that will instantiate an
                instance of ``Template``

        Returns:
            Any: an instance of ``target_cls``
        """  # noqa: B950, RST304
        return orchestrator.from_obj(
            target_cls, cls(**{k: v for k, v in obj.items() if k != "type"}).params
        )
