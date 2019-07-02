from pathlib import Path
import main
from argparse import Namespace
from stroke import constants


if __name__ == '__main__':
    # change to data
    hospital_path =Path('data/hospitals/Demo.csv')
    times_path = Path('data/travel_times/Demo.csv')
    res_name_prefix = Path('E:/stroke_model_output/output_demo')
    s_default = 1000
    upper = 1
    for sex in [constants.Sex.MALE,constants.Sex.FEMALE]:
        for age in range(30, 85 + upper, 5):  # 30 to 85
            for race in range(0, 9 + upper, 1):  # 0 to 9
                for time_since_symptoms in range(10, 100 + upper, 10):  # 10 to 100
                    sex_str = 'male' if sex==constants.Sex.MALE else 'female'
                    res_name=str(res_name_prefix/
                    f'times={times_path.stem}_hospitals={hospital_path.stem}_sex={sex_str}_age={age}_race={race}_symptom={time_since_symptoms}_nsim={s_default}_beAHA.csv')
                    kwargs = {}
                    kwargs['sex'] = sex
                    kwargs['age'] = age
                    kwargs['race'] = race
                    kwargs['time_since_symptoms'] = time_since_symptoms
                    main.run_model(times_file=times_path,
                    hospitals_file=hospital_path,
                    fix_performance=False,
                    patient_count=1,
                    simulation_count=s_default,
                    cores=None, # use multicore if None
                    res_name=res_name,
                    **kwargs
                    )

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
