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
"""Objects that enable grid searching adorn configs"""
from functools import reduce
from itertools import chain
from itertools import groupby
from itertools import product
from typing import Any
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import Tuple
from typing import TypeVar
from typing import Union

from adorn.params import Params
from adorn.unit.complex import Complex
from adorn.unit.search.search import SearchElement
from adorn.unit.search.search import SearchSpace
from adorn.unit.template import Template


GRID_OUTPUT = TypeVar("GRID_OUTPUT", List[Params], List[List[Params]])


@SearchElement.root()
class GridElement(SearchElement):
    """Individual component that make up a space to search over"""

    def __init__(self) -> None:
        super().__init__()

    def __len__(self) -> int:  # pragma: no cover
        """Number of elements the component is adding to the search space"""
        raise NotImplementedError

    def __call__(self) -> List[Dict[str, Any]]:  # pragma: no cover
        """Generate the collection of values to add to the search space

        Raises:
            NotImplementedError: needs to be implemented by child class
        """
        raise NotImplementedError

    @staticmethod
    def str_to_list(str_or_list: Union[str, List[str]]) -> List[str]:
        """Convert a string to a list

        Args:
            str_or_list (Union[str, List[str]]): a string to be converted
                to a list or a list that will have nothing done to it

        Returns:
            List[str]: a string that has been promoted to a list or just
                the original list that was passed
        """
        if isinstance(str_or_list, str):
            return [str_or_list]
        return str_or_list


class GridElementTemplate(GridElement, Template):
    """A ``Template`` for components of a grid search"""


@GridElement.register("base_grid")
class BaseGrid(GridElement):
    """Generate a dict to be added to the search space for each value

    Args:
        keys (Union[str, List[str]]): name(s) to assign to each search value
        values (List[Any]): collection of values to search over
    """

    def __init__(self, keys: Union[str, List[str]], values: List[Any]) -> None:
        super().__init__()
        self.keys = self.str_to_list(keys)
        self.values = values

    def __len__(self) -> int:
        """Number of elements added to the search space"""
        return len(self.values)

    def __call__(self) -> List[Dict[str, Any]]:
        """Create a ``Dict`` for each search value to be added to the search space

        Returns:
            List[Dict[str, Any]]: a collection of search values to
                be added to the search space
        """
        return [{k: v for k in self.keys} for v in self.values]


@BaseGrid.register("id_grid")
class IdGrid(GridElementTemplate):
    """Add a single value to a grid search

    This is useful when you want to override a value for a
    given search space
    """

    def __init__(self, keys: Union[str, List[str]], value: Any) -> None:
        super().__init__()
        self.keys = keys
        self.value = value

    @property
    def _params(self) -> Params:
        """Config to create the search component"""
        return Params({"type": "base_grid", "keys": self.keys, "values": [self.value]})


@SearchSpace.root()
class GridSearch(SearchSpace):
    """Generate a grid search space by composing multiple grid components"""

    def __init__(self) -> None:
        super().__init__()

    def __call__(self) -> List[Dict[str, Any]]:  # pragma: no cover
        """Generate all elements of the search space

        Raises:
            NotImplementedError: needs to be implemented by child class
        """
        raise NotImplementedError

    @staticmethod
    def tuple_to_dict(tpl: Tuple[Dict[str, Any], ...]) -> Dict[str, Any]:
        """Convert a tuple of dictionaries to a single dictionary

        Args:
            tpl (Tuple[Dict[str, Any], ...]): collection of dictionaries

        Returns:
            Dict[str, Any]: a dictionary made of all the dictionaries
                passed to this method
        """
        return dict(chain(*map(lambda i: i.items(), tpl)))


@GridSearch.register("base_grid_search")
class BaseGridSearch(GridSearch):
    """Generate a search space by taking the ``itertools.product`` of other search spaces and components

    Args:
        search_space (List[Union[GridElement, GridSearch]]): collection of grid
            objects to be composed
    """  # noqa: B950

    def __init__(self, search_space: List[Union[GridElement, GridSearch]]) -> None:
        super().__init__()
        self.search_space = search_space

    def __len__(self) -> int:
        """Number of elements to be searched over"""
        lengths = map(lambda i: len(i), self.search_space)
        return reduce(lambda i, j: i * j, lengths, 1)

    def __call__(self) -> List[Dict[str, Any]]:
        """Take the ``itertools.product`` of the provided :attr:`~adorn.unit.search.grid.BaseGridSearch.search_space` to generate a new grid search space

        Returns:
            List[Dict[str, Any]]: grid search space made of the ``itertools.product`` of
                grid elements and search spaces
        """  # noqa: B950, RST304
        iter_of_tpl = product(*[i() for i in self.search_space])
        return [self.tuple_to_dict(tpl) for tpl in iter_of_tpl]


@GridSearch.register("list_grid_search")
class ListGridSearch(GridSearch):
    """Concatenate grid search spaces to create a single search space

    Args:
        search_space (List[GridSearch]): multiple search spaces to
            be concatenated
    """

    def __init__(self, search_space: List[GridSearch]) -> None:
        super().__init__()
        self.search_space = search_space

    def __len__(self) -> int:
        """Number of elements to be searched over"""
        lengths = map(lambda i: len(i), self.search_space)
        return reduce(lambda i, j: i + j, lengths, 0)

    def __call__(self) -> List[Dict[str, Any]]:
        """Grid search space made up of a concatenation of search spaces

        Returns:
            List[Dict[str, Any]]: a collection of search space elements
        """
        return [j for i in self.search_space for j in i()]


@GridSearch.register("file_grid_search")
class FileGridSearch(GridSearch):
    """A grid search space made of a collection of adorn configs

    Args:
        filenames (List[str]): location of the adorn configs on disk
    """

    def __init__(self, filenames: List[str]) -> None:
        super().__init__()
        self.filenames = filenames

    def __len__(self) -> int:
        """Number of elements to be searched over"""
        return len(self.filenames)

    def __call__(self) -> List[Dict[str, Any]]:
        """Grid search space made up of serialized adorn configs

        Returns:
            List[Dict[str, Any]]: a collection of search space elements
                where each element was an adorn config read from disk
        """
        return [Params.from_file(i).as_dict() for i in self.filenames]


@Complex.root()
class Organize(Complex):
    """Alter the order of a list of grid points"""

    def __init__(self) -> None:
        super().__init__()

    def __call__(
        self, search_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:  # pragma: no cover
        """Rearrange a list of grid points

        Args:
            search_list (List[Dict[str, Any]]): list of grid points

        Raises:
            NotImplementedError: needs to be implemented by child class
        """
        raise NotImplementedError


@Organize.register("id_organize")
class IDOrganize(Organize):
    """Perform no alterations to the list of grid points"""

    def __call__(self, search_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return the list of grid points without alterations

        Args:
            search_list (List[Dict[str, Any]]): list of grid points

        Returns:
            List[Dict[str, Any]]: list of grid points passed, without
                alterations
        """
        return search_list


@Organize.register("sort_organize")
class SortOrganize(Organize):
    """Sort a list of grid points based on the values contained in each element

    Args:
        keys (Union[str, List[str]]): names of the values to sort the values
            of a list
    """

    def __init__(self, keys: Union[str, List[str]]) -> None:
        super().__init__()
        self.keys = keys

    def generate_key(self, dct: Dict[str, Any]) -> Union[Any, Tuple[Any, ...]]:
        """Get the values associated with a grid point for sorting

        Args:
            dct (Dict[str, Any]): the grid point, which will have values parsed from it

        Returns:
            Union[Any, Tuple[Any, ...]]: values from a grid point to be used for sorting
        """
        return tuple(
            dct[key]
            for key in (self.keys if isinstance(self.keys, list) else [self.keys])
        )

    def __call__(self, search_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort a list of grid points based on a subset of values

        Args:
            search_list (List[Dict[str, Any]]): collection of grid points to be sorted

        Returns:
            List[Dict[str, Any]]: list of grid points passed, sorted
                based on a subset of their values
        """
        return sorted(search_list, key=self.generate_key)


@Complex.root()
class Group(Complex):
    """Partition a list of grid points based on shared characteristics"""

    def __init__(self) -> None:
        super().__init__()

    def __call__(
        self, search_list: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:  # pragma: no cover
        """Partition a list of grid points

        Args:
            search_list (List[Dict[str, Any]]): collection of grid
                points to be partitioned

        Raises:
            NotImplementedError: needs to be implemented by child class
        """
        raise NotImplementedError


@Group.register("id_group")
class IDGroup(Group):
    """Add each element of a list of grid points to its own partition"""

    def __init__(self) -> None:
        super().__init__()

    def __call__(self, search_list: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Place each element of the grid list into its own group

        Args:
            search_list (List[Dict[str, Any]]): collection of grid points

        Returns:
            List[List[Dict[str, Any]]]: each element is in its own partition
        """
        return [[i] for i in search_list]


@Group.register("group_by")
class GroupBy(Group):
    """Partition a list of grid points based on common values

    Args:
        keys (Union[str, List[str]]): names of the values to group
            the grid elements by
    """

    def __init__(self, keys: Union[str, List[str]]) -> None:
        super().__init__()
        self.sort_organize = SortOrganize(keys=keys)

    def __call__(self, search_list: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group grid points based on common values

        Args:
            search_list (List[Dict[str, Any]]): collection of grid points

        Returns:
            List[List[Dict[str, Any]]]: partitions of elements with common values
        """
        return [
            list(i)
            for _, i in groupby(
                self.sort_organize(search_list=search_list),
                key=self.sort_organize.generate_key,
            )
        ]


@Complex.root()
class GridOrchestrator(Complex, Generic[GRID_OUTPUT]):
    """Generate a grid search space and optionally alter the space"""

    constructor_name = "__init__"

    def __init__(self) -> None:
        super().__init__()

    def __call__(self) -> GRID_OUTPUT:  # pragma: no cover
        """Produce a grid search space of collection of grid search spaces

        Raises:
            NotImplementedError: needs to be implemented by child class
        """
        raise NotImplementedError


@GridOrchestrator.register("grid_orch_list")
class GridList(GridOrchestrator[List[Params]]):
    """Generate a grid search space and optionally alter the order of the space

    Args:
        grid_search (GridSearch): specification of a grid search space
        organize (Optional[Organize]): optionally alter the order of a search
            space, if ``None`` the order is not altered
    """

    def __init__(
        self, grid_search: GridSearch, organize: Optional[Organize] = None
    ) -> None:
        super().__init__()
        self.grid_search = grid_search
        self.organize = organize or IDOrganize()

    def __call__(self) -> List[Params]:
        """Generate a search space and order it

        Returns:
            List[Params]: a grid search space that has potentially had
                its order altered
        """
        return self.organize(self.grid_search())


@GridOrchestrator.register("grid_orch_nested_list")
class GridNestedList(GridOrchestrator[List[List[Params]]]):
    """Generate a collection of grid search spaces

    Args:
        grid_search (GridSearch): specification of a grid search space
        group (Optional[Group]): optional specification of how to create
            grid search spaces, if ``None`` each element in the grid search
            becomes its own grid search space
    """

    def __init__(self, grid_search: GridSearch, group: Optional[Group] = None) -> None:
        super().__init__()
        self.grid_search = grid_search
        self.group = group or IDGroup()

    def __call__(self) -> List[List[Params]]:
        """Create a collection of grid search spaces

        Returns:
            List[List[Params]]: a collection of grid search spaces
        """
        return self.group(self.grid_search())
