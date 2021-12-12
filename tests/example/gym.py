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
from collections import defaultdict
from dataclasses import dataclass
from enum import auto
from enum import Enum
from sys import version_info
from typing import Dict
from typing import List
from typing import Optional
from typing import Set

if (version_info.major > 3) or (version_info.major == 3 and version_info.minor >= 8):
    from typing import Literal
else:
    from typing_extensions import Literal

from adorn.params import Params
from adorn.unit.anum import Anum
from adorn.unit.dataclass import DataClass
from adorn.unit.complex import Complex
from adorn.unit.parameter_value import DependentFromObj
from adorn.unit.parameter_value import DependentTypeCheck
from adorn.unit.parameter_value import DependentUnion
from adorn.unit.template import Template


class Gymnum(Anum):
    """Gym Enum"""

    _registry = defaultdict(dict)


@Gymnum.register()
class FeedType(Enum):
    """Type of feed fed to an animal"""

    Grass = auto()
    Corn = auto()
    Unknown = auto()


@Gymnum.register()
class Lift(Enum):
    """Types of lift done at the gym"""

    Squat = auto()
    Bench = auto()
    Deadlift = auto()


class GymData(DataClass):
    """registry for gym related dataclasses"""

    _registry = dict()


@GymData.register()
@dataclass
class Workout:
    """dataclass for tracking a workout"""

    lift: Lift
    reps: int
    weight: float
    maxed: bool = False


class Gym(Complex):
    """Gym"""

    _registry = defaultdict(dict)
    _subclass_registry = dict()
    _intermediate_registry = defaultdict(list)
    _parent_registry = defaultdict(list)


class Food(Gym):
    """Food"""

    def __init__(self) -> None:
        super().__init__()


@Food.register(None)
class Meat(Food):
    """Meat"""

    def __init__(self, weight: float) -> None:
        super().__init__()
        self.weight = weight


@Meat.register("beef")
class Beef(Meat):
    """Beef"""

    def __init__(self, feed: FeedType = FeedType.Corn, **kwargs) -> None:
        super().__init__(**kwargs)
        self.feed = feed

    def __eq__(self, other):
        if not isinstance(other, Beef):
            return False
        return (self.weight == other.weight) and (self.feed == other.feed)


@Meat.register("pork")
class Pork(Meat):
    """Pork"""

    def __eq__(self, other):
        if not isinstance(other, Pork):
            return False
        return self.weight == other.weight


class IntentionallyUnregistered(Meat):
    """Not Registered ON PURPOSE"""

    pass


@Food.register(None)
class Fruit(Food):
    """Fruit"""

    def __init__(self) -> None:
        super().__init__()


@Fruit.register("apple")
class Apple(Fruit):
    """Apple"""

    def __init__(self) -> None:
        super().__init__()

    def __eq__(self, other):
        return isinstance(other, Apple)


@Fruit.register("avocado")
class Avocado(Fruit):
    """Avocado"""

    def __init__(self) -> None:
        super().__init__()

    def __eq__(self, other):
        return isinstance(other, Avocado)


class GrandParent(Gym):
    """GrandParent"""

    def __init__(self, gp: str) -> None:
        super().__init__()
        self.gp = gp


@GrandParent.register(None)
class ParentA(GrandParent):
    """ParentA"""

    def __init__(self, a: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self.a = a


@GrandParent.register(None)
class ParentB(GrandParent):
    """ParentB"""

    def __init__(self, b: bool = True, **kwargs) -> None:
        super().__init__(**kwargs)
        self.b = b


@GrandParent.register(None)
class BadParent(GrandParent):
    """Children break adorn"""


@ParentA.register("0")
class Child0(ParentA):
    """Child0"""

    parameter_order = ["zero", "a", "gp"]

    def __init__(self, zero: List[str], **kwargs) -> None:
        super().__init__(**kwargs)
        self.zero = zero

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Child0):
            return False
        return all(getattr(self, i) == getattr(o, i) for i in ["zero", "a", "gp"])


@ParentA.register("1")
class Child1(ParentA):
    """Child1"""

    def __init__(self, one: Dict[int, Set[bool]], **kwargs) -> None:
        super().__init__(**kwargs)
        self.one = one

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Child1):
            return False
        return all(getattr(self, i) == getattr(o, i) for i in ["one", "a", "gp"])


@ParentB.register("2")
class Child2(ParentB):
    """Child2"""

    def __init__(
        self,
        food: Optional[Food],
        fruit: Fruit,
        meat: Meat,
        workout: Optional[Workout] = None,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.food = food
        self.fruit = fruit
        self.meat = meat
        self.workout = workout

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Child2):
            return False
        return all(
            getattr(self, i) == getattr(o, i)
            for i in ["food", "fruit", "meat", "b", "gp", "workout"]
        )


@BadParent.register("bad_0")
class BadChild0(BadParent):
    """parameter order is missing gp key"""

    parameter_order = ["b"]


@Child2.register("beef_2")
class BeefChild2(Template, Gym):
    """Beef Child2"""

    def __init__(self, weight: int):
        super().__init__()
        self.weight = weight

    @property
    def _params(self) -> Params:
        return Params(
            {
                "type": "2",
                "food": None,
                # if we don't cast to float the Params for
                # Child2, won't type check which is naughty
                "meat": {"type": "beef", "weight": float(self.weight)},
                "fruit": {"type": "apple"},
                "gp": "doesnt_matter",
            }
        )


class Ambig(Complex):
    """Ambig"""

    _registry = defaultdict(dict)
    _subclass_registry = dict()
    _intermediate_registry = defaultdict(list)
    _parent_registry = defaultdict(list)

    _attr: Optional[List[str]]

    def __eq__(self, o: object) -> bool:
        return type(self) == type(o) and all(
            getattr(self, i) == getattr(o, i) for i in self._attr
        )


class D(Ambig):
    """D"""

    def __init__(self, k: List[str]) -> None:
        super().__init__()
        self._k = k

    @property
    def k(self) -> List[str]:
        """K"""
        return self._k

    @property
    def dd(self) -> Dict[str, int]:
        """DD"""
        raise NotImplementedError


@D.register(None)
class MD(D):
    """MD"""

    def __init__(self, k: List[str]) -> None:
        super().__init__(k)


@MD.register("md")
class BMD(MD):
    """BMD"""

    _attr = ["filename", "k", "dd"]

    def __init__(self, filename: str, k: List[str], dd: Dict[str, int]) -> None:
        super().__init__(k)
        self.filename = filename
        self._dd = dd

    @property
    def dd(self) -> Dict[str, int]:
        """DD"""
        return self._dd


@D.register(None)
class ID(D):
    """ID"""

    def __init__(self, k: List[str]) -> None:
        super().__init__(k)


@ID.register("id")
class BID(ID):
    """BID"""

    _attr = ["filename", "k", "dd"]

    def __init__(self, filename: str, k: List[str], dd: Dict[str, int]) -> None:
        super().__init__(k)
        self.filename = filename
        self._dd = dd

    @property
    def dd(self) -> Dict[str, int]:
        """DD"""
        return self._dd


class S(Ambig):
    """S"""

    def __init__(self, d: D) -> None:
        super().__init__()
        self.d = d


@S.register("ms")
class BMS(S):
    """BMS"""

    _attr = ["d"]

    def __init__(self, d: MD) -> None:
        super().__init__(d)


@S.register("is")
class BIS(S):
    """BIS"""

    _attr = ["d"]

    def __init__(self, d: ID) -> None:
        super().__init__(d)


class DL(Ambig):
    """DL"""

    def __init__(self) -> None:
        super().__init__()


@DL.register("bdl")
class BDL(DL):
    """BDL"""

    _attr = ["s", "d", "sh"]
    parameter_order = ["sh", "d", "s"]

    def __init__(
        self, s: DependentTypeCheck[S, Literal[{"d": "d"}]], d: D, sh: bool
    ) -> None:
        super().__init__()
        self.s = s
        self.d = d
        self.sh = sh


class DLC(Ambig):
    """DLC"""

    def __init__(self) -> None:
        super().__init__()


@DLC.register("dlc")
class DictDLC(DLC):
    """DictDLC"""

    _attr = ["dct"]

    def __init__(
        self,
        dct: Dict[str, DL],
    ) -> None:
        self.dct = dct
        self.dl = dct[next(iter(dct.keys()))]

    @property
    def dd(self):
        """Propogate DD up"""
        return self.dl.d.dd


class MO(Ambig):
    """MO"""

    def __init__(self) -> None:
        super().__init__()


@MO.register(None)
class MMO(MO):
    """MMO"""

    def __init__(self) -> None:
        super().__init__()


@MMO.register("mmo")
class LMMO(MMO):
    """LMMO"""

    _attr = ["l_ambig"]

    def __init__(self, l_ambig: float) -> None:
        super().__init__()
        self.l_ambig = l_ambig


@MO.register(None)
class DMO(MO):
    """DMO"""

    _attr = ["dd"]

    def __init__(self, dd: Dict[str, int]):
        super().__init__()
        self.dd = dd


@DMO.register("dmo")
class FDMO(DMO):
    """FDMO"""


class OP(Ambig):
    """OP"""

    def __init__(self, dmo: DMO) -> None:
        super().__init__()
        self.dmo = dmo


@OP.register("op")
class BOP(OP):
    """BOP"""

    _attr = ["dmo", "l_ambig"]

    def __init__(self, dmo: DMO, l_ambig: float) -> None:
        super().__init__(dmo)
        self.l_ambig = l_ambig


class LRS(Ambig):
    """LRS"""

    def __init__(self, op: OP) -> None:
        super().__init__()
        self.op = op


@LRS.register("lrs")
class BLRS(LRS):
    """BLRS"""

    _attr = ["op", "per"]

    def __init__(self, op: OP, per: int) -> None:
        super().__init__(op=op)
        self.per = per


class ME(Ambig):
    """ME"""

    def __init__(self, kw: str, okw: Optional[int] = None) -> None:
        super().__init__()
        self.kw = kw
        self.okw = okw


@ME.register("me")
class BME(ME):
    """BME"""

    _attr = ["flt", "kw", "okw"]

    def __init__(self, flt: float, **kwargs) -> None:
        super().__init__(**kwargs)
        self.flt = flt


class SME(Ambig):
    """SME"""

    def __init__(self, dd: Dict[str, int]) -> None:
        super().__init__()
        self.dd = dd


@SME.register("bsme")
class BSME(SME):
    """BMSE"""

    _attr = ["lst", "dd"]

    def __init__(self, lst: List[ME], dd: Dict[str, int]) -> None:
        super().__init__(dd=dd)
        self.lst = lst


@SME.register("dsme")
class DSME(SME):
    """DSME"""

    _attr = ["dct"]

    def __init__(self, dct: Dict[str, SME], dd: Dict[str, int]) -> None:
        super().__init__()
        self.dct = dct
        self.dd = dd


class LIM(Ambig):
    """LIM"""

    def __init__(
        self,
        mo: MO,
        dlc: DLC,
        sme: SME,
    ) -> None:
        super().__init__()
        self.mo = mo
        self.dlc = dlc
        self.sme = sme


@LIM.register("lim")
class BLIM(LIM):
    """BLIM"""

    _attr = ["mo", "dlc", "sme", "lrs", "op"]
    parameter_order = ["dlc", "mo", "sme", "op", "lrs"]

    def __init__(
        self,
        mo: DependentUnion[DependentFromObj[MO, Literal[{"dd": "dlc.dd"}]], MO],
        dlc: DLC,
        sme: DependentFromObj[SME, Literal[{"dd": "dlc.dd"}]],
        lrs: DependentUnion[DependentTypeCheck[LRS, Literal[{"op": "op"}]], None],
        op: DependentUnion[DependentTypeCheck[OP, Literal[{"dmo": "mo"}]], None],
    ) -> None:
        super().__init__(mo, dlc, sme)
        self.lrs = lrs
        self.op = op
