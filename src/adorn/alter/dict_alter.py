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
"""Apply an alteration to an object based off a ``dict``"""
from os import environ
from typing import Any
from typing import Dict
from typing import Optional
from typing import Type
from typing import TYPE_CHECKING
from typing import Union

from adorn.exception.type_check_error import TypeCheckError
from adorn.exception.type_check_error import UserDictError

if TYPE_CHECKING:  # pragma: no cover
    from adorn.orchestrator.orchestrator import Orchestrator

from adorn.alter.alter import Alter
from adorn.data.parameter import Parameter
from adorn.params import Params


class UserDictAlter(Alter):
    """Inject a value from a user provided ``dict``

    Args:
        user_dict (Dict[str, Any]): dictionary which contains
            values to be injected
    """

    def __init__(self, user_dict: Dict[str, Any]) -> None:
        super().__init__()
        self.user_dict = user_dict

    def a_contains(
        self,
        target_cls: Type,
        orchestrator: "Orchestrator",
        obj: Any,
    ) -> bool:
        """Check if a value in ``user_dict`` has been requested

        Args:
            target_cls (Type): the target Type, the given ``obj`` will be converted
                into or checked against
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): an instance, that will be checked to see if it can be
                converted into the ``target_cls`` or will be converted to an
                instance of ``target_cls``

        Returns:
            bool: if ``True`` then a value in the user dict has been
                requested else ``False``
        """
        return (
            isinstance(target_cls, Parameter)
            and isinstance(obj, Params)
            and obj.get("type") == self.type_value
            and obj.get("key") in self.user_dict
        )

    def a_get(
        self,
        target_cls: Type,
        orchestrator: "Orchestrator",
        obj: Any,
    ) -> Optional[Alter]:
        """Return this ``Alter`` if the associated with the arguments are requesting it

        Args:
            target_cls (Type): the target Type, the given ``obj`` will be converted
                into or checked against
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): an instance, that will be checked to see if it can be
                converted into the ``target_cls`` or will be converted to an
                instance of ``target_cls``

        Returns:
            Optional[Alter]: if the provided arguments are contained by this ``Alter``
                return it, otherwise ``None``
        """
        if self.a_contains(
            target_cls=target_cls,
            orchestrator=orchestrator,
            obj=obj,
        ):
            return self

    def alter_obj(
        self,
        target_cls: Type,
        orchestrator: "Orchestrator",
        obj: Any,
    ) -> Union[Any, TypeCheckError]:
        """Swap ``obj`` with a value in ``user_dict``

        Args:
            target_cls (Type): the target Type, the given ``obj`` will be converted
                into or checked against
            orchestrator (Orchestrator): container of all types, typically used
                to recurse down nested types
            obj (Any): an instance, that will be checked to see if it can be
                converted into the ``target_cls`` or will be converted to an
                instance of ``target_cls``

        Returns:
            Union[Any, TypeCheckError]: a value from ``user_dict`` or a
                ``TypeCheckError`` providing a reason why a value from
                ``user_dict`` couldn't be provided
        """
        user_dict_value = self.user_dict[obj.get("key")]
        try:
            new_obj = orchestrator.from_obj(target_cls.cls, user_dict_value)
        except Exception as e:
            return UserDictError(type(self), target_cls, obj, e)
        return new_obj

    @property
    def type_value(self) -> str:
        """The expected value for the key ``type`` in the given :class:`~adorn.params.Params` object

        Returns:
            str: the value of ``type`` for which this ``Alter`` is appropriate
        """  # noqa: B950
        return "user_dict"


class EnvDictAlter(UserDictAlter):
    """Inject values from the environment"""

    def __init__(self) -> None:
        super().__init__(user_dict=environ)

    @property
    def type_value(self) -> str:
        """The expected value for the key ``type`` in the given :class:`~adorn.params.Params` object

        Returns:
            str: the value of ``type`` for which this ``Alter`` is appropriate
        """  # noqa: B950
        return "ENV"
