"""Objects that enable grid searching adorn configs"""
from collections import defaultdict
from functools import reduce
from itertools import chain
from itertools import product
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union

from adorn.params import Params
from adorn.unit.search.search import SearchElement
from adorn.unit.search.search import SearchSpace
from adorn.unit.template import Template


class GridElement(SearchElement):
    """Individual component that make up a space to search over"""

    _registry = defaultdict(dict)
    _subclass_registry = dict()
    _intermediate_registry = defaultdict(list)
    _parent_registry = defaultdict(list)

    def __len__(self) -> int:
        """Number of elements the component is adding to the search space"""
        raise NotImplementedError

    def __call__(self) -> List[Dict[str, Any]]:
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


class GridSearch(SearchSpace):
    """Generate a grid search space by composing multiple grid components"""

    _registry = defaultdict(dict)
    _subclass_registry = dict()
    _intermediate_registry = defaultdict(list)
    _parent_registry = defaultdict(list)

    def __call__(self) -> List[Dict[str, Any]]:
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
