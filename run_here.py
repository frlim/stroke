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
    s_default = 1000  #'auto'
    upper = 1

    patient_profiles = pd.read_csv(
        paths._data_path / 'patient_profiles_01_30_20.csv', index_col=0)
    for id, profile in patient_profiles.iterrows():
        age, sex, nihss, time_since_symptoms = profile.age, profile.sex, profile.nihss, profile.time_since_symptoms
        sex_str = 'male' if sex == constants.Sex.MALE else 'female'
        res_name = str(
            res_name_prefix /
            (f'times={times_path.stem}_hospitals={hospital_path.stem}_pid={id}_sex={sex_str}_age={age}'
            + f'_nihss={nihss}_symptom={time_since_symptoms}_nsim={s_default}_beAHA.csv')
        )
        args = Namespace(
            patients=1,
            simulations=s_default,
            multicore=True,
            hospital_file=str(hospital_path),
            times_file=str(times_path),
            sex=sex,
            age=age,
            nihss=nihss,
            time_since_symptoms=time_since_symptoms,
            res_name=res_name)
        main.main_default_dtn(args)

        res_name = str(
            res_name_prefix /
            (f'times={times_path.stem}_hospitals={hospital_path.stem}_pid={id}_sex={sex_str}_age={age}'
            + f'_nihss={nihss}_symptom={time_since_symptoms}_nsim={s_default}_afAHA.csv')
        )
        args = Namespace(
            patients=1,
            simulations=s_default,
            multicore=True,
            hospital_file=str(hospital_path),
            times_file=str(times_path),
            sex=sex,
            age=age,
            nihss=nihss,
            time_since_symptoms=time_since_symptoms,
            res_name=res_name)
        main.main(args)
