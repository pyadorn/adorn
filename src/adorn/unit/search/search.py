"""Abstract classes for creating a search space for an ``adorn`` config"""
from adorn.unit.complex import Complex


class SearchElement(Complex):
    """Specification of a single component to search over"""

    pass


class SearchSpace(Complex):
    """Specification of multiple components to search over"""

    def __len__(self) -> int:
        """Number of elements to be searched over

        Raises:
            NotImplementedError: needs to be implemented by child class
        """
        raise NotImplementedError
