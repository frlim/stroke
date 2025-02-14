"""
Run analysis on a set of map points given times to nearby hospitals
"""
import os
import argparse
import collections
import multiprocessing as mp
import data_io
from stroke.patient import Patient
from stroke import severity,constants,stroke_model as sm
# import stroke.stroke_model as sm
import numpy as np
from tqdm import tqdm
import paths
from pathlib import Path

NON_COUNT_COLS = [
    'Location', 'Patient', 'Varying Hospitals', 'PSC Count', 'CSC Count',
    'Sex', 'Age', 'Symptoms', 'RACE'
]

NUM_CORES = 2

def results_name(base_dir, times_file, hospitals_file, fix_performance,
                 simulation_count, sex):
    """Get the name for the file storing results for the given arguments."""
    times_file = os.path.basename(times_file)
    hospitals_file = os.path.basename(hospitals_file)
    out_name = f'times={times_file.strip(".csv")}'
    out_name += f'_hospitals={hospitals_file.strip(".csv")}'
    out_name += '_fixed' if fix_performance else '_random'
    out_name += '_' + str(sex)
    out_name += '.csv'
    out_dir = os.path.join(base_dir, 'output')
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    out_file = os.path.join(out_dir, out_name)
    return out_file

def _instanstiate_patients(patient_count,**kwargs):
    patient_characteristics = list(locals().keys())
    have_pc_and_race = np.isin(['age','sex','time_since_symptoms','race'],
                      patient_characteristics).all()
    have_pc_and_nihss = np.isin(['age','sex','time_since_symptoms','nihss'],
                      patient_characteristics).all()
    if have_pc_and_race: # not used
        patients = [Patient.with_RACE(**kwargs)]
    elif have_pc_and_nihss: # not used
        patients = [Patient.with_NIHSS(**kwargs)]
    else: # each patient generated with this function
        patients = [Patient.random(**kwargs) for _ in range(patient_count)]
    return patients # returns a list of one patient of the Patient class

# Run base version of the model: no hospital performance data
def run_model_defaul_dtn(
        times_file,
        hospitals_file,
        fix_performance=False,
        patient_count=10,
        simulation_count=1000,
        cores=None,
        base_dir='',  # default: current working directory
        locations=None,  # default: run for all location in times_file
        res_name=None,
        **kwargs):
    '''Run the model on the given map points for the given hospitals. The
        times file should be in data/travel_times and contain travel times to
        appropriate hospitals. The hospitals file should be in data/hospitals
        and contain transfer destinations and times for all primary hospitals.
        kwargs -- passed through to inputs.Inputs.random to hold parameters
                    constant
        This method use travel_time file generated from hospital list Kori gave
        but instead of using DTN times from AHA, we use default_times generated
        from a uniform distribution
        For now, use fix_performance = True to make it fair for the hospitals
    '''
    hospitals = data_io.get_hospitals(hospitals_file) # list of all hospitals and their characteristics
    hospital_lists = [
        (False, hospitals)
    ]  # false means use same DTN distribution for all hospitals

    patients = _instanstiate_patients(patient_count,**kwargs) # list of one patient and their characteristics
    sex = patients[0].sex

    times = data_io.get_times(times_file) # dictionary: main key = location, inner key = hospital, value = travel time
    if locations:
        # Create dictionary times, key = location, value = hospital for all locations specified in run_here.py
        times = {loc: time for loc, time in times.items() if loc in locations} # dictionary list comprehension

    if not res_name: # not used and specified in run_here.py, defines output file name
        res_name = results_name(base_dir, times_file, hospitals_file,
                                fix_performance, simulation_count, sex)

    if cores is False: # no multiprocessing
        pool = False
    else: # multiprocessing
        pool = mp.Pool(NUM_CORES)

    # Runs for one patient: pat_num = 0 and patient = Patient class    
    for pat_num, patient in enumerate(tqdm(patients, desc='Patients')):
        patient_results = []
        # points = locations, these_times = dictionary of hospital keys with values as travel times
        for point, these_times in tqdm( 
                times.items(), desc='Map Points', leave=False):
            # uses_hospital_performance = False, hospital_list = list of hospitals
            for uses_hospital_performance, hospital_list in hospital_lists:
                if pool: # multiprocessing
                    results = pool.apply_async(
                        run_one_scenario,
                        (patient, point, these_times, hospital_list,
                         uses_hospital_performance, simulation_count,
                         fix_performance, res_name))
                else: # no multiprocessing
                    results = run_one_scenario(
                        patient, point, these_times, hospital_list,
                        uses_hospital_performance, simulation_count,
                        fix_performance, res_name)
                patient_results.append(results)
        if pool:
            to_fetch = tqdm(patient_results, desc='Map Points', leave=False)
            patient_results = [job.get() for job in to_fetch]
        # Save after each patient in case we cancel or crash
        data_io.save_patient(res_name, patient_results, hospitals)
    if pool:
        pool.close()
    return

# Runs enhanced version of the model: including hospital performance data
# **kwargs = keyword arguments, allows any number of keyword arguments
# a keyword argument has a name attached to the variable, think of kwargs like a dictionary
def run_model_real_data(
        times_file,
        hospitals_file,
        dtn_file=paths.DTN_FILE,
        fix_performance=False,
        patient_count=10,
        simulation_count=1000,
        cores=None,
        base_dir='',  # default: current working directory
        res_name=None,
        locations=None,  # default: run for all location in times_file
        patients=None,
        **kwargs): 
    '''Run the model on the given map points for the given hospitals. The
        times file should be in data/travel_times and contain travel times to
        appropriate hospitals. The hospitals file should be in data/hospitals
        and contain transfer destinations and times for all primary hospitals.
        kwargs -- passed through to inputs.Inputs.random to hold parameters
                    constant
        Also need dtn_file here to use real hospital performance data
    '''
    hospitals = data_io.get_hospitals(hospitals_file, dtn_file) # Returns list of each center with its attributes
    hospital_lists = [(True, hospitals)] # True means using hospital data

    # Generates list of Patient class (contains 1 patient)
    # Attributes: pid, sex, age, symptom_time, severity
    patients = _instanstiate_patients(patient_count,**kwargs)

    sex = patients[0].sex
    # Times is a dictionary of dictionary
    # Main key = location id (L#), inner key = hopsital key (K#), value = [min_time,  max_time]
    times = data_io.get_times(times_file)
    
    if locations:  # Not none, run a subset of locations
        # Subset times dictionary to just locations we are running
        times = {loc: time for loc, time in times.items() if loc in locations}

    # if not res_name: # doesn't run
    #     res_name = results_name(base_dir, times_file, hospitals_file,
    #                             fix_performance, simulation_count, sex)

    # Determines multiprocessing run or not
    if cores is False: # run on a single core, no multiprocessing
        pool = False
    else:
        pool = mp.Pool(NUM_CORES)

    # Runs for one patient: patients is list of one patient
    # Enumerate: (0, patient0)
    # Desc = description of progress bar
    for pat_num, patient in enumerate(tqdm(patients, desc='Patients')):
        patient_results = []
        for point, these_times in tqdm( # point = location, these_times = hospital: [min_time, max_time]
                times.items(), desc='Map Points', leave=False):
            # uses_hospital_performance = TRUE/FALSE
            # hospital_list = list of hospital classes
            for uses_hospital_performance, hospital_list in hospital_lists:
                if pool: # multiprocessing
                    results = pool.apply_async(
                        run_one_scenario,
                        (patient, point, these_times, hospital_list,
                         uses_hospital_performance, simulation_count,
                         fix_performance, res_name))
                else: # no multiprocessing
                    results = run_one_scenario(
                        patient, point, these_times, hospital_list,
                        uses_hospital_performance, simulation_count,
                        fix_performance, res_name)
                patient_results.append(results)
        
        if pool: # aggregate multiprocessing results
            to_fetch = tqdm(patient_results, desc='Map Points', leave=False)
            patient_results = [job.get() for job in to_fetch]
        
        # Save after each patient in case we cancel or crash
        data_io.save_patient(res_name, patient_results, hospitals)
    
    if pool:
        pool.close()
    return

def run_one_scenario(patient,
                     point,
                     these_times,
                     hospital_list,
                     uses_hospital_performance,
                     simulation_count,
                     fix_performance,
                     res_name=None):
    '''Called in run_model_real_data() and run_model_defaul_dtn()'''
    # model attributes: patient, hospitals, threshold_ICER
    # hospital_list = list of hospital classes
    model = sm.StrokeModel(patient, hospital_list) # create instance of StrokeModel class
    # these_times = dictionary of each hospital key with values [min_time, max_time]
    model.set_times(these_times) # sets attributes no_traffic and traffic
    
    if str(simulation_count) == 'auto': # automatic mode, uses convergence to get number of simulations (not used)
        model_run = model.run_new
    else: # we specify number of simulations with a parameter (simulation_count)
        try:
            simulation_count = int(simulation_count)
            # model.run returns: results.Results(markov), markov, ais_times
            model_run = model.run # runs StrokeModel instance
        except ValueError:
            raise Exception("Num of simulation is not an integer!")

    # these_results = Results class, tabulated version of markov model
    # markov_results = Population class
    # ais_times = IschemicModel class
    these_results, markov_results, ais_times = model_run( # separate into the 3 results
        n=simulation_count, fix_performance=fix_performance)

    if res_name:
        # output details of each simulation: Cost and QALY
        #dimension: simulation# -> row index,hospital-> columns
        # data_io.write_detailed_markov_outcomes(
        #     markov_results, res_name, point, times=ais_times,
        #     optimal_strategy= str(these_results.optimal_strategy), write = True)

        # Optimal strategy marked with 'most C/E'
        # Creates aggreated files, one for each location
        data_io.write_aggregated_markov_outcomes(
            markov_results, res_name, point, times=ais_times,
            optimal_strategy= str(these_results.optimal_strategy), write = True)

    results = collections.OrderedDict()
    results['Location'] = point
    results['Patient'] = patient.pid
    results['Use Real DTN'] = uses_hospital_performance
    results['Varying Hospitals'] = not fix_performance
    results['PSC Count'] = len(model.primaries)
    results['CSC Count'] = len(model.comprehensives)
    results['Sex'] = 'male' if patient.sex == constants.Sex.MALE else 'female'
    results['Age'] = patient.age
    results['Symptoms'] = patient.symptom_time
    if isinstance(patient.severity,severity.NIHSS):
        results['NIHSS'] = patient.severity.score
    else:
        results['RACE'] = patient.severity.score
    cbc = these_results.counts_by_center
    cbc = {str(center): count for center, count in cbc.items()}
    results.update(cbc)
    # add nan for hospital that are never optimal
    zero_c = {
        str(hospital): float('nan')
        for hospital in hospital_list if str(hospital) not in results.keys()
    }
    results.update(zero_c)
    return results


def parse_extra_inputs(args):
    kwargs = {}
    if hasattr(args, 'sex'):
        kwargs['sex'] = args.sex
    if hasattr(args, 'age'):
        kwargs['age'] = args.age
    if hasattr(args, 'race'):
        kwargs['race'] = args.race
    if hasattr(args, 'nihss'):
        kwargs['nihss'] = args.nihss
    if hasattr(args, 'time_since_symptoms'):
        kwargs['time_since_symptoms'] = args.time_since_symptoms
    return kwargs


def main(args):
    '''Runs stroke markov model'''
    times_file = args.times_file
    hospitals_file = args.hospital_file
    patient_count = args.patients # number of patients to run at each location
    simulation_count = args.simulations # number of simulations
    kwargs = parse_extra_inputs(args)

    # if args.base_dir:
    #     base_dir = args.base_dir  # dir to put output file in
    # else:
    #     base_dir = ''  # default: current working directory
    base_dir = ''

    if hasattr(args, 'locations'):
        locations = args.locations
    else:
        locations = None
    if hasattr(args, 'res_name'):
        res_name = args.res_name
    else:
        res_name = None

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
        res_name=res_name,
        **kwargs)


def main_default_dtn(args):
    '''Used in sensitivity analysis'''
    times_file = args.times_file
    hospitals_file = args.hospital_file
    patient_count = args.patients # number of patients to run at each location
    simulation_count = args.simulations # number of simulations
    kwargs = parse_extra_inputs(args)

    # if args.base_dir:
    #     base_dir = args.base_dir  # dir to put output file in
    # else:
    #     base_dir = ''  # default: current working directory
    base_dir = ''

    if hasattr(args, 'locations'):
        locations = args.locations
    else:
        locations = None
    if hasattr(args, 'res_name'):
        res_name = args.res_name
    else:
        res_name = None

    if args.multicore:
        cores = None
    else:
        cores = False

    run_model_defaul_dtn(
        times_file,
        hospitals_file,
        patient_count=patient_count,
        fix_performance=False,
        simulation_count=simulation_count,
        cores=cores,
        base_dir=base_dir,
        locations=locations,
        res_name=res_name,
        **kwargs)


if __name__ == '__main__':
    p_default = 2 # number of patients to run at each location
    s_default = 1000 # number of simulations

    parser = argparse.ArgumentParser() # instance of a class
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
