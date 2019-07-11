"""
Information about a stroke center.
"""
import enum
import numpy as np


class CenterType(enum.IntEnum):
    PRIMARY = 0
    COMPREHENSIVE = 1


class HospitalTimeDistribution:

    def __init__(self, first_quartile, median, third_quartile):
        self.first_quartile = first_quartile
        self.median = median
        self.third_quartile = third_quartile

    @classmethod
    def random_primary(cls):
        med = np.random.uniform(47, 83)
        first = np.random.uniform(37, med)
        third = np.random.uniform(med, 93)
        return cls(first, med, third)

    @classmethod
    def random_comprehensive(cls):
        med = np.random.uniform(39, 70)
        first = np.random.uniform(29, med)
        third = np.random.uniform(med, 80)
        return cls(first, med, third)

    @classmethod
    def random_door_to_puncture(cls):
        med = np.random.uniform(83, 192)
        first = np.random.uniform(63, med)
        third = np.random.uniform(med, 212)
        return cls(first, med, third)


PRIMARY_DIST = HospitalTimeDistribution(47, 61, 83)
COMP_DIST = HospitalTimeDistribution(39, 52, 70)
DTP_DIST = HospitalTimeDistribution(83, 145, 192)

# PRIMARY_DIST = HospitalTimeDistribution(10, 10, 10)
# COMP_DIST = HospitalTimeDistribution(60*4, 60*4, 60*4)
# DTP_DIST = HospitalTimeDistribution(83, 83, 83)
#

class StrokeCenter:

    _next_id = 1

    @classmethod
    def get_next_id(cls):
        this_id = cls._next_id
        cls._next_id += 1
        return this_id

    @property
    def id(self):
        '''Internal ID for hashing purposes'''
        return self._id

    @property
    def center_id(self):
        '''External ID to match with computed travel times'''
        return self._center_id

    @property
    def short_name(self):
        return self._short_name

    @property
    def full_name(self):
        return self._full_name

    @property
    def center_type(self):
        return self._center_type

    @property
    def transfer_destination(self):
        return self._transfer_destination

    @property
    def transfer_time(self):
        return self._transfer_time

    @property
    def door_to_needle(self):
        return self._door_to_needle

    @property
    def door_to_puncture(self):
        return self._door_to_puncture

    def __init__(self, full_name, short_name, center_type, center_id,
                 time=None, dtn_dist=None, dtp_dist=None):
        self._id = StrokeCenter.get_next_id()
        self._center_id = center_id
        self._full_name = full_name
        self._short_name = short_name
        self._center_type = center_type
        self.time = time
        self._transfer_destination = None
        self._transfer_time = None
        self._door_to_needle = None
        self._door_to_puncture = None

        # Distributions for door to needle and door to puncture times
        if dtn_dist is None:
            if center_type is CenterType.PRIMARY:
                dtn_dist = PRIMARY_DIST
            elif center_type is CenterType.COMPREHENSIVE:
                dtn_dist = COMP_DIST
        self._dtn_dist = dtn_dist

        if center_type is CenterType.COMPREHENSIVE:
            if dtp_dist is None:
                dtp_dist = DTP_DIST
            self._dtp_dist = dtp_dist
        else:
            self._dtp_dist = None

    def __str__(self):
        out = self.short_name
        if self.center_type is CenterType.PRIMARY:
            out += ' (PSC)'
        elif self.center_type is CenterType.COMPREHENSIVE:
            out += ' (CSC)'

        return out

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    @classmethod
    def primary(cls, time, index=1, random_dist=False):
        '''Create a dummy primary center with given travel time'''
        name = f'Primary {index}'
        if random_dist:
            dist = HospitalTimeDistribution.random_primary()
        else:
            dist = None
        return cls(name, name, CenterType.PRIMARY, index, time, dtn_dist=dist)

    @classmethod
    def comprehensive(cls, time, index=1, random_dist=False):
        name = f'Comprehensive {index}'
        if random_dist:
            dtn_dist = HospitalTimeDistribution.random_comprehensive()
            dtp_dist = HospitalTimeDistribution.random_door_to_puncture()
        else:
            dtn_dist, dtp_dist = None, None
        return cls(name, name, CenterType.COMPREHENSIVE, index, time,
                   dtn_dist, dtp_dist)

    def add_transfer_destination(self, comprehensive, transfer_time):
        self._transfer_destination = comprehensive
        self._transfer_time = transfer_time

    def set_door_to_needle(self, n=1, with_uncertainty=True, perf_level=None):
        '''Set the door to needle time for this stroke center by sampling from
            the stored distribution or selecting the median. If perf_level is
            not None, it will be treated as the n draws from a uniform [0,1] RV
            to set the door to needle time without a new draw.
        '''
        if not with_uncertainty and perf_level is not None:
            raise ValueError('preset level cannot be used without uncertainty')
        if with_uncertainty:
            low = self._dtn_dist.first_quartile
            high = self._dtn_dist.third_quartile
            if perf_level is None:
                val = np.random.uniform(low, high, n)
            else:
                val = low + perf_level * (high - low)
        else:
            val = self._dtn_dist.median

        self._door_to_needle = val

    def set_door_to_puncture(self, n=1, with_uncertainty=True,
                             perf_level=None):
        '''Set the door to puncture time for this stroke center by sampling
            from the stored distribution or selecting the median. If perf_level
            is not None, it will be treated as the n draws from a uniform [0,1]
            RV to set the door to puncture time without a new draw.
        '''
        if self.center_type is CenterType.PRIMARY:
            raise ValueError("Can't set door to puncture on primary center.")
        if not with_uncertainty and perf_level is not None:
            raise ValueError('preset level cannot be used without uncertainty')
        if with_uncertainty:
            low = self._dtp_dist.first_quartile
            high = self._dtp_dist.third_quartile
            if perf_level is None:
                val = np.random.uniform(low, high, n)
            else:
                val = low + perf_level * (high - low)
        else:
            val = self._dtp_dist.median

        self._door_to_puncture = val
