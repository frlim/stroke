"""
Patient information for a stroke triage decision
"""
from . import severity as sev, constants
import numpy.random as rng


class Patient:
    """Patient-level inputs."""

    def __init__(self, sex, age, symptom_time, severity):
        """Initialize a patient with required inputs"""
        self.sex = sex
        self.age = age
        self.symptom_time = symptom_time
        self.severity = severity

    @classmethod
    def with_RACE(cls, sex, age, symptom_time, race):
        """Generate a patient with severity characterized by RACE score"""
        return cls(sex, age, symptom_time, sev.RACE(race))

    @classmethod
    def with_NIHSS(cls, sex, age, symptom_time, nihss):
        """Generate a patient with severity characterized by NIHSS"""
        return cls(sex, age, symptom_time, sev.NIHSS(nihss))

    @classmethod
    def random(cls, sex=None, age=None, race=None, nihss=None,
               time_since_symptoms=None):
        """
        Generate a random patient. Fix any input by passing it as an argument.
        """
        if sex is None:
            sex = rng.choice(list(constants.Sex))

        if age is None:
            age = rng.randint(30, 85)

        if race is not None:
            severity = sev.RACE(race)
        if race is None and nihss is not None:
            severity = sev.NIHSS(nihss)
        else:
            severity = sev.RACE(rng.randint(0, 9))

        if time_since_symptoms is None:
            time_since_symptoms = rng.uniform(10, 100)

        return cls(sex, age, time_since_symptoms, severity)
