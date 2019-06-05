"""
Run analysis on a set of map points given times to nearby hospitals
"""
import os
import argparse
import collections
import multiprocessing as mp
import data_io
from stroke.patient import Patient
import stroke.stroke_model as sm
try:
    get_ipython
    from tqdm import tqdm_notebook as tqdm
except NameError:
    from tqdm import tqdm
from pathlib import Path
import numpy as np

NON_COUNT_COLS = ['Location','Patient','Varying Hospitals','PSC Count','CSC Count',
    'Sex','Age','Symptoms','RACE']

def results_name(base_dir, times_file, hospitals_file, fix_performance,
                 simulation_count, sex):
    """Get the name for the file storing results for the given arguments."""
    times_file = os.path.basename(times_file)
    hospitals_file = os.path.basename(hospitals_file)
    out_name = f'times={times_file.strip(".csv")}'
    out_name += f'_hospitals={hospitals_file.strip(".csv")}'
    out_name += '_fixed' if fix_performance else '_random'
    out_name += '_male' if sex==0 else '_female'
    out_name += '_python.csv'
    out_dir = os.path.join(base_dir, 'output')
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    out_file = os.path.join(out_dir, out_name)
    return out_file


def run_model(
        times_file,
        hospitals_file,
        fix_performance=False,
        patient_count=10,
        simulation_count=1000,
        cores=None,
        base_dir='',  # default: current working directory
        locations=None,  # default: run for all location in times_file
        **kwargs):
    '''Run the model on the given map points for the given hospitals. The
        times file should be in data/travel_times and contain travel times to
        appropriate hospitals. The hospitals file should be in data/hospitals
        and contain transfer destinations and times for all primary hospitals.

        kwargs -- passed through to inputs.Inputs.random to hold parameters
                    constant
    '''
    hospitals = data_io.get_hospitals(hospitals_file, use_default_times=False)
    hospitals_default = data_io.get_hospitals(hospitals_file, use_default_times=True)
    hospital_lists = [(True, hospitals), (False, hospitals_default)]

    patients = [Patient.random(**kwargs) for _ in range(patient_count)]
    sex = patients[0].sex

    times = data_io.get_times(times_file)
    if locations:  # Not none
        times = {loc: time for loc, time in times.items() if loc in locations}

    res_name = results_name(base_dir, times_file, hospitals_file,
                            fix_performance, simulation_count, sex)
    first_pat_num = data_io.get_next_patient_number(res_name)

    if cores is False:
        pool = False
    else:
        pool = mp.Pool(cores)

    for pat_num, patient in enumerate(tqdm(patients, desc='Patients')):
        patient_results = []
        for point, these_times in tqdm(
                times.items(), desc='Map Points', leave=False):
            for uses_hospital_performance, hospital_list in hospital_lists:
                if pool:
                    results = pool.apply_async(
                        run_one_scenario,
                        (patient, point, these_times, hospital_list,
                         uses_hospital_performance, simulation_count,
                         fix_performance, first_pat_num, pat_num))
                else:
                    results = run_one_scenario(
                        patient, point, these_times, hospital_list,
                        uses_hospital_performance, simulation_count,
                        fix_performance, first_pat_num, pat_num)
                patient_results.append(results)
        if pool:
            to_fetch = tqdm(patient_results, desc='Map Points', leave=False)
            patient_results = [job.get() for job in to_fetch]
        # Save after each patient in case we cancel or crash
        data_io.save_patient(res_name, patient_results, hospitals)
    if pool:
        pool.close()
    return


DTN_FILE = Path('Z:\\stroke_data')/'deidentified_DTN.xlsx'
def run_model_real_data(
        times_file,
        hospitals_file,
        dtn_file=DTN_FILE,
        fix_performance=False,
        patient_count=10,
        simulation_count=1000,
        cores=None,
        base_dir='',  # default: current working directory
        locations=None,  # default: run for all location in times_file
        **kwargs):
    '''Run the model on the given map points for the given hospitals. The
        times file should be in data/travel_times and contain travel times to
        appropriate hospitals. The hospitals file should be in data/hospitals
        and contain transfer destinations and times for all primary hospitals.
        kwargs -- passed through to inputs.Inputs.random to hold parameters
                    constant
    '''
    hospitals = data_io.get_hospitals_real_data(hospitals_file,dtn_file)
    hospital_lists = [(True, hospitals)]

    patients = [Patient.random(**kwargs) for _ in range(patient_count)]
    sex = patients[0].sex

    times = data_io.get_times_real_data(times_file)
    if locations:  # Not none
        times = {loc: time for loc, time in times.items() if loc in locations}

    res_name = results_name(base_dir, times_file, hospitals_file,
                            fix_performance, simulation_count, sex)
    first_pat_num = data_io.get_next_patient_number(res_name)

    if cores is False:
        pool = False
    else:
        pool = mp.Pool(cores)
    for pat_num, patient in enumerate(tqdm(patients, desc='Patients')):
        patient_results = []
        for point, these_times in tqdm(
                times.items(), desc='Map Points', leave=False):
            for uses_hospital_performance, hospital_list in hospital_lists:
                if pool:
                    results = pool.apply_async(
                        run_one_scenario,
                        (patient, point, these_times, hospital_list,
                         uses_hospital_performance, simulation_count,
                         fix_performance, first_pat_num, pat_num))
                else:
                    results = run_one_scenario(
                        patient, point, these_times, hospital_list,
                        uses_hospital_performance, simulation_count,
                        fix_performance, first_pat_num, pat_num)
                patient_results.append(results)
        if pool:
            to_fetch = tqdm(patient_results, desc='Map Points', leave=False)
            patient_results = [job.get() for job in to_fetch]
        # Save after each patient in case we cancel or crash
        data_io.save_patient(res_name, patient_results, hospitals)
    if pool:
        pool.close()
    return


def run_one_scenario(patient, point, these_times, hospital_list,
                     uses_hospital_performance, simulation_count,
                     fix_performance, first_pat_num, pat_num):
    model = sm.StrokeModel(patient, hospital_list)
    model.set_times(these_times)
    these_results = model.run(
        n=simulation_count, fix_performance=fix_performance)
    results = collections.OrderedDict()
    results['Location'] = point
    results['Patient'] = first_pat_num + pat_num
    results['Varying Hospitals'] = uses_hospital_performance
    results['PSC Count'] = len(model.primaries)
    results['CSC Count'] = len(model.comprehensives)
    results['Sex'] = str(patient.sex)
    results['Age'] = patient.age
    results['Symptoms'] = patient.symptom_time
    results['RACE'] = patient.severity.score
    cbc = these_results.counts_by_center
    cbc = {str(center): count for center, count in cbc.items()}
    results.update(cbc)
    # add zero counts for hospital that are never optimal
    zero_c = {
        str(hospital): 0
        for hospital in hospital_list if str(hospital) not in results.keys()
    }
    results.update(zero_c)
    return results


def parse_extra_inputs(args):
    kwargs = {}
    if hasattr(args,'sex'):
        kwargs['sex'] = args.sex
    if hasattr(args,'age'):
        kwargs['age'] = args.age
    if hasattr(args,'race'):
        kwargs['race'] =args.race
    if hasattr(args,'time_since_symptoms'):
        kwargs['time_since_symptoms'] = args.time_since_symptoms
    return kwargs

def main(args):
    times_file = args.times_file
    hospitals_file = args.hospital_file
    patient_count = args.patients
    simulation_count = args.simulations
    kwargs = parse_extra_inputs(args)

    # if args.base_dir:
    #     base_dir = args.base_dir  # dir to put output file in
    # else:
    #     base_dir = ''  # default: current working directory
    base_dir=''

    if hasattr(args, 'locations'):
        locations = args.locations
    else:
        locations = None

    if args.multicore:
        cores = None
    else:
        cores = False

    run_model_real_data(
        times_file,
        hospitals_file,
        patient_count=patient_count,
        fix_performance=False,
        simulation_count=simulation_count,
        cores=cores,
        base_dir=base_dir,
        locations=locations,
        **kwargs)


if __name__ == '__main__':
    p_default = 2
    s_default = 1000

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'hospital_file', help='full path to file with hospital information')
    parser.add_argument(
        'times_file', help='full path to file with travel times')
    p_help = 'number of random patients to run at each location'
    p_help += f' (default {p_default})'
    parser.add_argument(
        '-p', '--patients', type=int, default=p_default, help=p_help)
    s_help = f'number of model runs for each scenario (default {s_default})'
    parser.add_argument(
        '-s', '--simulations', type=int, default=1000, help=s_help)
    parser.add_argument(
        '-m',
        '--multicore',
        action='store_true',
        help='Use all available CPU cores')
    args = parser.parse_args()
    main(args)
