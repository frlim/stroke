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


def results_name(times_file, hospitals_file, fix_performance,
                 simulation_count):
    """Get the name for the file storing results for the given arguments."""
    times_file = os.path.basename(times_file)
    hospitals_file = os.path.basename(hospitals_file)
    out_name = f'times={times_file.strip(".csv")}'
    out_name += f'_hospitals={hospitals_file.strip(".csv")}'
    out_name += '_fixed' if fix_performance else '_random'
    out_name += '_python.csv'
    if not os.path.isdir('output'):
        os.makedirs('output')
    out_file = os.path.join('output', out_name)
    return out_file


def run_model(times_file, hospitals_file, fix_performance=False,
              patient_count=100, simulation_count=1000, cores=None,
              **kwargs):
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

    times = data_io.get_times(times_file)

    res_name = results_name(times_file, hospitals_file, fix_performance,
                            simulation_count)
    first_pat_num = data_io.get_next_patient_number(res_name)

    if cores is False:
        pool = False
    else:
        pool = mp.Pool(cores)

    for pat_num, patient in enumerate(tqdm(patients, desc='Patients')):
        patient_results = []
        for point, these_times in tqdm(times.items(), desc='Map Points',
                                       leave=False):
            for uses_hospital_performance, hospital_list in hospital_lists:
                if pool:
                    results = pool.apply_async(
                        run_one_scenario,
                        (patient, point, these_times, hospital_list,
                         uses_hospital_performance,
                         simulation_count, fix_performance,
                         first_pat_num, pat_num)
                    )
                else:
                    results = run_one_scenario(
                        patient, point, these_times, hospital_list,
                        uses_hospital_performance,
                        simulation_count, fix_performance,
                        first_pat_num, pat_num
                    )
                patient_results.append(results)
        if pool:
            to_fetch = tqdm(patient_results, desc='Map Points', leave=False)
            patient_results = [job.get() for job in to_fetch]
        # Save after each patient in case we cancel or crash
        data_io.save_patient(res_name, patient_results, hospitals)

    return


def run_one_scenario(patient, point, these_times, hospital_list,
                     uses_hospital_performance,
                     simulation_count, fix_performance,
                     first_pat_num, pat_num):
    model = sm.StrokeModel(patient, hospital_list)
    model.set_times(these_times)
    these_results = model.run(
        n=simulation_count,
        fix_performance=fix_performance
    )
    results = collections.OrderedDict()
    results['Location'] = point
    results['Patient'] = first_pat_num + pat_num
    results['Varying Hospitals'] = uses_hospital_performance
    results['Primary Count'] = len(model.primaries)
    results['Comprehensive Count'] = len(model.comprehensives)
    results['Sex'] = str(patient.sex)
    results['Age'] = patient.age
    results['Symptoms'] = patient.symptom_time
    results['RACE'] = patient.severity.score
    cbc = these_results.counts_by_center
    cbc = {str(center): count for center, count in cbc.items()}
    results.update(cbc)

    return results


def main(args):
    times_file = args.times_file
    hospitals_file = args.hospital_file
    patient_count = args.patients
    simulation_count = args.simulations
    if args.multicore:
        cores = None
    else:
        cores = False

    run_model(times_file, hospitals_file, patient_count=patient_count,
              fix_performance=False, simulation_count=simulation_count,
              cores=cores)


if __name__ == '__main__':
    p_default = 10
    s_default = 1000

    parser = argparse.ArgumentParser()
    parser.add_argument('hospital_file',
                        help='full path to file with hospital information')
    parser.add_argument('times_file',
                        help='full path to file with travel times')
    p_help = 'number of random patients to run at each location'
    p_help += f' (default {p_default})'
    parser.add_argument(
        '-p', '--patients', type=int, default=p_default, help=p_help
    )
    s_help = f'number of model runs for each scenario (default {s_default})'
    parser.add_argument(
        '-s', '--simulations', type=int, default=1000, help=s_help
    )
    parser.add_argument('-m', '--multicore', action='store_true',
                        help='Use all available CPU cores')
    args = parser.parse_args()
    main(args)
