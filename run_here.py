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
    s_default = 10000  #'auto'
    upper = 1

    patient_profiles = pd.read_csv(
        paths._data_path / 'patient_profiles_01_30_20.csv', index_col=0)
    for id, profile in patient_profiles.iterrows():
        print(f"Patient #{id}")
        age, sex, nihss, time_since_symptoms = profile.age, profile.sex, profile.nihss, profile.time_since_symptoms
        sex_str = 'male' if sex == constants.Sex.MALE else 'female'
        res_name = str(
            res_name_prefix /
            (f'times={times_path.stem}_hospitals={hospital_path.stem}_pid={id}_sex={sex_str}_age={age}'
            + f'_nihss={nihss}_symptom={time_since_symptoms}_nsim={s_default}_beAHA.csv')
        )
        locations = ['L298'] # or None to run all locations
        args = Namespace(
            patient_count=1,
            simulation_count=s_default,
            cores=None, #None: multicore, False: run single core
            hospitals_file=str(hospital_path),
            times_file=str(times_path),
            sex=sex,
            age=age,
            nihss=nihss,
            time_since_symptoms=time_since_symptoms,
            locations=locations,
            res_name=res_name)
        # print("Before AHA")
        # main.run_model_defaul_dtn(**vars(args))

        res_name = str(
            res_name_prefix /
            (f'times={times_path.stem}_hospitals={hospital_path.stem}_pid={id}_sex={sex_str}_age={age}'
            + f'_nihss={nihss}_symptom={time_since_symptoms}_nsim={s_default}_afAHA.csv')
        )
        args = Namespace(
            patient_count=1,
            simulation_count=s_default,
            cores=None, #None: multicore, False: run single core
            hospitals_file=str(hospital_path),
            times_file=str(times_path),
            sex=sex,
            age=age,
            nihss=nihss,
            time_since_symptoms=time_since_symptoms,
            locations=locations,
            res_name=res_name)
        print("After AHA")
        main.run_model_real_data(**vars(args))
        break
