from pathlib import Path
import main
from argparse import Namespace
from stroke import constants
import os
import paths

if __name__ == '__main__':
    # get file paths base on OS 
    res_name_prefix = paths.RES_NAME_PREFIX
    hospital_path = paths.HOSPITAL_PATH
    times_path = paths.TIMES_PATH
    s_default = 'auto'
    upper = 1
    for sex in [constants.Sex.MALE,constants.Sex.FEMALE]:
        for age in range(60, 85 + upper, 5):  # 30 to 85
            for race in range(0, 9 + upper, 1):  # 0 to 9
                for time_since_symptoms in range(10, 100 + upper, 10):  # 10 to 100
                    sex_str = 'male' if sex==constants.Sex.MALE else 'female'
                    res_name=str(res_name_prefix/
                    f'times={times_path.stem}_hospitals={hospital_path.stem}_sex={sex_str}_age={age}_race={race}_symptom={time_since_symptoms}_nsim={s_default}_beAHA.csv')
                    args = Namespace(
                        patients=1,
                        simulations=s_default,
                        multicore=True,
                        hospital_file=str(hospital_path),
                        times_file=str(times_path),
                        sex=sex,
                        age=age,
                        race=race,
                        time_since_symptoms=time_since_symptoms,
                        res_name=res_name)
                    main.main_default_dtn(args)

                    res_name=str(res_name_prefix/
                    f'times={times_path.stem}_hospitals={hospital_path.stem}_sex={sex_str}_age={age}_race={race}_symptom={time_since_symptoms}_nsim={s_default}_afAHA.csv')
                    args = Namespace(
                        patients=1,
                        simulations=s_default,
                        multicore=True,
                        hospital_file=str(hospital_path),
                        times_file=str(times_path),
                        sex=sex,
                        age=age,
                        race=race,
                        time_since_symptoms=time_since_symptoms,
                        res_name=res_name)
                    main.main(args)

    # sex = constants.Sex.MALE
    # age=70
    # race=8
    # time_since_symptoms=50
    # s_default = 5
    # upper = 1
    # sex_str = 'male' if sex==constants.Sex.MALE else 'female'
    # res_name=f'output/output_062819/times={times_path.stem}_hospitals={hospital_path.stem}_sex={sex_str}_age={age}_race={race}_symptom={time_since_symptoms}_nsim={s_default}_afAHA.csv'
    # args = Namespace(
    #     patients=1,
    #     simulations=s_default,
    #     multicore=False,
    #     hospital_file=str(hospital_path),
    #     times_file=str(times_path),
    #     sex=sex,
    #     age=age,
    #     race=race,
    #     time_since_symptoms=time_since_symptoms,
    #     res_name=res_name)
    # main.main(args)

    # res_name=f'output/output_062819/times={times_path.stem}_hospitals={hospital_path.stem}_sex={sex_str}_age={age}_race={race}_symptom={time_since_symptoms}_nsim={s_default}_afAHA.csv'
    # args = Namespace(
    #     patients=1,
    #     simulations=s_default,
    #     multicore=True,
    #     hospital_file=str(hospital_path),
    #     times_file=str(times_path),
    #     sex=sex,
    #     age=age,
    #     race=race,
    #     time_since_symptoms=time_since_symptoms,
    #     res_name=res_name)
    # main.main(args)
