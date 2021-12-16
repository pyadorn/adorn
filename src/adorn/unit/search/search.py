from collections import defaultdict
from functools import reduce
from itertools import chain, product
from typing import Any, Dict, List, Tuple, Union

from adorn.params import Params
from adorn.unit.complex import Complex
from adorn.unit.template import Template


class SearchElement(Complex):
    pass


class GridElement(SearchElement):
    _registry = defaultdict(dict)
    _subclass_registry = dict()
    _intermediate_registry = defaultdict(list)
    _parent_registry = defaultdict(list)

    def __len__(self) -> int:
        raise NotImplementedError

    def __call__(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @staticmethod
    def str_to_list(str_or_list: Union[str, List[str]]) -> List[str]:
        if isinstance(str_or_list, str):
            return [str_or_list]
        return str_or_list


class GridElementTemplate(GridElement, Template):
    pass


@GridElement.register("base_grid")
class BaseGrid(GridElement):
    def __init__(self, keys: Union[str, List[str]], values: List[Any]) -> None:
        super().__init__()
        self.keys = self.str_to_list(keys)
        self.values = values

    def __len__(self) -> int:
        return len(self.values)

    def __call__(self) -> List[Dict[str, Any]]:
        return [{k: v for k in self.keys} for v in self.values]


@BaseGrid.register("id_grid")
class IdGrid(GridElementTemplate):
    def __init__(self, keys: Union[str, List[str]], value: Any) -> None:
        super().__init__()
        self.keys = self.str_to_list(keys)
        self.value = value

    @property
    def _params(self) -> Params:
        return Params(
            {
                "type": "base_grid",
                "values": [self.values]
            }
        )


class SearchSpace(Complex):
    def __len__(self) -> int:
        raise NotImplementedError


class GridSearch(SearchSpace):
    _registry = defaultdict(dict)
    _subclass_registry = dict()
    _intermediate_registry = defaultdict(list)
    _parent_registry = defaultdict(list)

    def __call__(self) -> List[Params]:
        raise NotImplementedError

    @staticmethod
    def tuple_to_dict(tpl: Tuple[Dict[str, Any], ...]) -> Dict[str, Any]:
        return dict(chain(*map(lambda i: i.items(), tpl)))


@GridSearch.register("base_grid_search")
class BaseGridSearch(GridSearch):
    def __init__(self, search_space: List[GridElement]) -> None:
        super().__init__()
        self.search_space = search_space

    def __len__(self) -> int:
        return reduce(lambda i, j: len(i) * len(j), self.search_space.values(), [1])

    def __call__(self) -> List[Params]:
        iter_of_tpl = product(*[i() for i in self.search_space])
        return [Params(self.tuple_to_dict(tpl)) for tpl in iter_of_tpl]


@GridSearch.register("list_grid_search")
class ListGridSearch(GridSearch):
    def __init__(self, search_space: List[GridSearch]) -> None:
        super().__init__()
        self.search_space = search_space

    def __len__(self) -> int:
        return reduce(lambda i, j: len(i) + len(j), self.search_space, [])

    def __call__(self) -> List[Params]:
        return [Params(j) for i in self.search_space for j in i()]


@GridSearch.register("compose_grid_search")
class ComposeGridSearch(GridSearch):
    def __init__(self, search_space: List[GridSearch]) -> None:
        super().__init__()
        self.search_space = search_space

    def __len__(self) -> int:
        return reduce(lambda i, j: len(i) * len(j), self.search_space, [])

    def __call__(self) -> List[Params]:
        iter_of_tpl = product(*[i() for i in self.search_space])
        return [Params(self.tuple_to_dict(tpl)) for tpl in iter_of_tpl]


@GridSearch.register("file_grid_search")
class FileGridSearch(GridSearch):
    def __init__(self, filenames: List[str]) -> None:
        super().__init__()
        self.filenames = filenames

    def __len__(self) -> int:
        return len(self.filenames)

    def __call__(self) -> List[Params]:
        return [Params.from_file(i) for i in self.filenames]