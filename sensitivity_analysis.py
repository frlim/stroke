import argparse
from pathlib import Path
import main
from argparse import Namespace
from stroke import constants
import numpy as np
p_default = 10
s_default = 1000


if __name__ == '__main__':

    hospital_path = str(Path('data/hospitals/Demo.csv'))
    times_path = str(Path('data/travel_times/Demo.csv'))

    for age in range(30,95,5):
        sex = constants.Sex.MALE
        race = 5 # 0 to 9
        time_since_symptoms = 50 # 10 to 100
        args = Namespace(patients=1,
                        simulations=s_default,
                        multicore=True,
                        hospital_file=str(hospital_path),
                        times_file=str(times_path),
                        sex=sex,
                        age=age,
                        race=race,
                        time_since_symptoms=time_since_symptoms)
        main.main(args)
