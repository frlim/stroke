"""
Patient information for a stroke triage decision
"""
import severity as sev


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
