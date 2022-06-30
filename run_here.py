# Used to run Han's version of the model
# Base and enhanced version of the model (incorporating hospital performance data)
# Takes function to run the base and enhanced version of the model form main.py

import main
from argparse import Namespace
from stroke import constants
import paths
import pandas as pd

if __name__ == '__main__':
    # get file paths base on OS
    res_name_prefix = paths.RES_NAME_PREFIX
    hospital_path = paths.HOSPITAL_PATH
    times_path = paths.TIMES_PATH
    #s_default - 'auto' for automatic mode or else enter an integer
    s_default = 10000  #'auto', number of simulations
    upper = 1 # unused parameter

    # Read in patient profiles/characteristics
    patient_profiles = pd.read_csv(paths.PATIENT_PATH, index_col=0)

    # Iterate through eac patient
    # id = index, profile = row
    for id, profile in patient_profiles.iterrows():
        print(f"Patient #{id}")
        age, sex, nihss, time_since_symptoms = profile.age, profile.sex, profile.nihss, profile.time_since_symptoms
        sex_str = 'male' if sex == constants.Sex.MALE else 'female'
        # Define output file name
        res_name = str(
            res_name_prefix /
            (f'times={times_path.stem}_hospitals={hospital_path.stem}_pid={id}_sex={sex_str}_age={age}'
            + f'_nihss={nihss}_symptom={time_since_symptoms}_nsim={s_default}_beAHA.csv')
        )

        # Determine which locations to run the patient for
        locations = ['L298'] # or None to run all locations
        #locations = [f'L{i}' for i in range(500)]

        args = Namespace( # overrides parameters set in main.py
            patient_count=1, # run one patient from csv file at a time
            simulation_count=s_default, # number of simulations at each location
            cores=None, #None: multicore, False: run single core
            hospitals_file=str(hospital_path),
            times_file=str(times_path),
            pid=id,
            sex=sex,
            age=age,
            nihss=nihss,
            time_since_symptoms=time_since_symptoms,
            locations=locations,
            res_name=res_name)
        # Run base version of the model, no hospital performance
        print("Before AHA")
        main.run_model_defaul_dtn(**vars(args))

        # Define output file name
        res_name = str(
            res_name_prefix /
            (f'times={times_path.stem}_hospitals={hospital_path.stem}_pid={id}_sex={sex_str}_age={age}'
            + f'_nihss={nihss}_symptom={time_since_symptoms}_nsim={s_default}_afAHA.csv')
        )
        args = Namespace( # overrides parameters set in main.py
            patient_count=1,
            simulation_count=s_default,
            cores=None, #None: multicore, False: run single core
            hospitals_file=str(hospital_path),
            times_file=str(times_path),
            pid=id,
            sex=sex,
            age=age,
            nihss=nihss,
            time_since_symptoms=time_since_symptoms,
            locations=locations,
            res_name=res_name)
        # Run enhanced version of the model, including hospital performance
        print("After AHA")
        main.run_model_real_data(**vars(args))

