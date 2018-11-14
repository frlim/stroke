"""
Run analysis on a set of map points given times to nearby hospitals
"""
import os
import itertools
import warnings
import pandas as pd
import data_io
from stroke.patient import Patient
import stroke.stroke_model as sm
try:
    get_ipython
    from tqdm import tqdm_notebook as tqdm
except NameError:
    from tqdm import tqdm


def results_name(times_file, hospitals_file, fix_performance,
                 simulation_count):
    """Get the name for the file storing results for the given arguments."""
    out_name = f'times={times_file.strip(".csv")}'
    out_name += f'_hospitals={hospitals_file.strip(".csv")}'
    out_name += '_fixed' if fix_performance else '_random'
    out_name += '_python.csv'
    if not os.path.isdir('output'):
        os.makedirs('output')
    out_file = os.path.join('output', out_name)
    return out_file


def run_model(times_file, hospitals_file, fix_performance=False,
              patient_count=100, simulation_count=1000, **kwargs):
    '''Run the model on the given map points for the given hospitals. The
        times file should be in data/travel_times and contain travel times to
        appropriate hospitals. The hospitals file should be in data/hospitals
        and contain transfer destinations and times for all primary hospitals.

        kwargs -- passed through to inputs.Inputs.random to hold parameters
                    constant
    '''
    hospitals = data_io.get_hospitals(hospitals_file, False)
    hospitals_default = data_io.get_hospitals(hospitals_file, True)
    hospital_lists = [(True, hospitals), (False, hospitals_default)]

    patients = [Patient.random(**kwargs) for _ in range(patient_count)]

    times = pd.read_csv(os.path.join('data', 'travel_times', times_file),
                        sep='|').set_index(['Latitude', 'Longitude'])

    res_name = results_name(times_file, hospitals_file, fix_performance,
                            simulation_count)
    if os.path.isfile(res_name):
        results = pd.read_csv(res_name, index_col=[0, 1, 2, 3])
        first_pat_num = results.index.get_level_values(2).max() + 1
    else:
        index = [(lat, lon, pat, hosp) for ((lat, lon), pat, hosp)
                 in itertools.product(times.index, range(patient_count),
                                      [True, False])]
        index = pd.MultiIndex.from_tuples(index, names=['Latitude',
                                                        'Longitude',
                                                        'Patient',
                                                        'Varying Hospitals'])

        results = pd.DataFrame(index=index)
        first_pat_num = 0
    results = results.sort_index()
    warnings.filterwarnings('ignore', message='indexing past lexsort')
    for pat_num, patient in enumerate(tqdm(patients, desc='Patients')):
        for lat, lon in tqdm(times.index, desc='Map Points', leave=False):
            for uses_hospital_performance, hospital_list in hospital_lists:
                these_times = times.loc[(lat, lon)]
                model = sm.StrokeModel(patient, hospital_list)
                model.set_times(these_times)
                these_results = model.run(
                    n=simulation_count,
                    fix_performance=fix_performance
                )
                res_i = (lat, lon, first_pat_num + pat_num,
                         uses_hospital_performance)
                results.loc[res_i, 'Num_Primaries'] = len(model.primaries)
                results.loc[res_i, 'Sex'] = patient.sex
                results.loc[res_i, 'Age'] = patient.age
                results.loc[res_i, 'Symptoms'] = patient.symptom_time
                results.loc[res_i, 'RACE'] = patient.severity.score
                cbc = these_results.counts_by_center.items()
                for center, count in cbc:
                    results.loc[res_i, str(center.center_id)] = count
        # Save after each patient in case we cancel or crash
        results.to_csv(res_name)

    results = results.fillna(0)
    results.to_csv(res_name)
    return results


if __name__ == '__main__':
    times_file = 'CT_test_2018-09-07_11-19.csv'
    hospitals_file = 'CT_2018-09-06_17-23.csv'
    patient_count = 2
    simulation_count = 5000

    run_model(times_file, hospitals_file, patient_count=patient_count,
              fix_performance=False, simulation_count=simulation_count)
