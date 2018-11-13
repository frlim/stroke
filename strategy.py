"""
Strategies with associated stroke centers
"""
import stroke_center as sc
from constants import StrategyKind


class Strategy:
    """The kind of strategy to test and first destination hospital."""

    @property
    def kind(self):
        return self._kind

    @property
    def center(self):
        return self._center

    def __init__(self, kind, center):
        if kind in [StrategyKind.PRIMARY, StrategyKind.DRIP_AND_SHIP]:
            if center.center_type is not sc.CenterType.PRIMARY:
                raise ValueError(f'{center.full_name} is not a primary center')
        elif kind is StrategyKind.DRIP_AND_SHIP:
            if center.transfer_destination is None:
                raise ValueError(f'{center.full_name} has no transfer dest')
        elif kind is StrategyKind.COMPREHENSIVE:
            if center.center_type is not sc.CenterType.COMPREHENSIVE:
                mes = f'{center.full_name} is not a comprehensive center'
                raise ValueError(mes)

        self._kind = kind
        self._center = center

    def __str__(self):
        if self.kind is StrategyKind.PRIMARY:
            return f'Primary to {self.center}'
        elif self.kind is StrategyKind.DRIP_AND_SHIP:
            td = self.center.transfer_destination
            return f'Drip and Ship {self.center} to {td}'
        elif self.kind is StrategyKind.COMPREHENSIVE:
            return f'Comprehensive to {self.center}'
        else:
            raise ValueError('Unrecognized strategy type')

    def __repr__(self):
        return str(self)

    @property
    def __key(self):
        return (self.kind, self.center)

    def __eq__(self, other):
        return self.__key == other.__key

    def __hash__(self):
        return hash(self.__key)

    @classmethod
    def primary(cls, center):
        return cls(StrategyKind.PRIMARY, center)

    @classmethod
    def comprehensive(cls, center):
        return cls(StrategyKind.COMPREHENSIVE, center)

    @classmethod
    def drip_and_ship(cls, primary):
        return cls(StrategyKind.DRIP_AND_SHIP, primary)
