"""
Strategies with associated stroke centers
"""
import functools
from . import stroke_center as sc
from .constants import StrategyKind


@functools.total_ordering
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

    def __lt__(self, other):
        """
        A strategy appears before another strategy in a sort if it is the
            preferred option given identical costs and outcomes.
            First preference is for less travel time, then sorting by
            strategy kind as primary < comprehensive < drip and ship.
            Finally sort alphabetically by center name
        """
        return ((self.center.time, self.kind, self.center.full_name) <
                (other.center.time, other.kind, other.center.full_name))

    @classmethod
    def primary(cls, center):
        """Go to only the given primary center"""
        return cls(StrategyKind.PRIMARY, center)

    @classmethod
    def comprehensive(cls, center):
        """Go directly to the given comprehensive center"""
        return cls(StrategyKind.COMPREHENSIVE, center)

    @classmethod
    def drip_and_ship(cls, primary):
        """Go to the given primary center then transfer to designated
            comprehensive center."""
        return cls(StrategyKind.DRIP_AND_SHIP, primary)
