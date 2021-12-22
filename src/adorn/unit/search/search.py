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
"""Abstract classes for creating a search space for an ``adorn`` config"""
from adorn.unit.complex import Complex


class SearchElement(Complex):
    """Specification of a single component to search over"""


class SearchSpace(Complex):
    """Specification of multiple components to search over"""

    def __len__(self) -> int:  # pragma: no cover
        """Number of elements to be searched over

        Raises:
            NotImplementedError: needs to be implemented by child class
        """
        raise NotImplementedError
