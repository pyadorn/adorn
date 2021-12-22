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
"""Base Class for altering a config during type checking or object creation"""
from typing import Any
from typing import Optional
from typing import Type
from typing import TYPE_CHECKING
from typing import Union

from adorn.exception.type_check_error import TypeCheckError

if TYPE_CHECKING:  # pragma: no cover
    from adorn.orchestrator.orchestrator import Orchestrator


class Alter:
    """Base class that enables a config to be altered during type checking or object creation"""  # noqa: B950

    def a_contains(
        self,
        target_cls: Type,
        orchestrator: "Orchestrator",
        obj: Any,
    ) -> bool:  # pragma: no cover
        """Check if the application of an ``Alter`` is required

        Args:
            target_cls (Type): the target Type, the given ``obj`` will be converted
                into or checked against
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): an instance, that will be checked to see if it can be
                converted into the ``target_cls`` or will be converted to an
                instance of ``target_cls``

        Raises:
            NotImplementedError: This method must be overriden by a subclass
        """
        raise NotImplementedError

    def a_get(
        self,
        target_cls: Type,
        orchestrator: "Orchestrator",
        obj: Any,
    ) -> Optional["Alter"]:  # pragma: no cover
        """Capture the ``Alter`` associated with the arguments

        Args:
            target_cls (Type): the target Type, the given ``obj`` will be converted
                into or checked against
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): an instance, that will be checked to see if it can be
                converted into the ``target_cls`` or will be converted to an
                instance of ``target_cls``

        Raises:
            NotImplementedError: This method must be overriden by a subclass
        """
        raise NotImplementedError

    def alter_obj(
        self,
        target_cls: Type,
        orchestrator: "Orchestrator",
        obj: Any,
    ) -> Union[Any, TypeCheckError]:  # pragma: no cover
        """Apply an alteration to an object

        Args:
            target_cls (Type): the target Type, the given ``obj`` will be converted
                into or checked against
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): an instance, that will be checked to see if it can be
                converted into the ``target_cls`` or will be converted to an
                instance of ``target_cls``

        Raises:
            NotImplementedError: This method must be overriden by a subclass
        """
        raise NotImplementedError
