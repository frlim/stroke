"""
Patient information for a stroke triage decision
"""


class Patient:
    """Patient-level inputs."""

    def __init__(self, sex, age, symptom_time, severity):
        """Initialize a patient with required inputs"""
        self.sex = sex
        self.age = age
        self.symptom_time = symptom_time
        self.severity = severity
