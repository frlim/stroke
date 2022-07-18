"""
Read input files to prepare for model runs
"""
import csv
import os
import warnings

from regex import P
import stroke.stroke_center as sc
import pandas as pd
import gc
if os.name == 'nt': import xlwings as xw
from pathlib import Path
import paths
from stroke import constants
import numpy as np

def get_hospitals(hospital_file, dtn_file=None):
    '''Generate a list of StrokeCenters from a csv
        file containing transfer destinations and times. Optionally use
        recorded hospital performance metrics. The CSV is assumed to be
        formatted like `data/hospitals/Demo.csv`
        dtn_file: excel spreadsheet, deidentified and password-protected
        if a hospital doesn't have DTN or DTP time, use default distributions
        in stroke_center.py
    '''
    # load spreadsheets
    hospitals = paths.load_hospital(hospital_file=hospital_file)
    if dtn_file: # load treatment times
        dtn = paths.load_dtn(dtn_file)
        hospitals_dtn = hospitals.join(dtn, how='left', rsuffix='_dtn') # merge hospital and dtn data
    else: # no treatment times
        # use default dtn, assign NaN to treatment time columns
        hospitals_dtn = hospitals.assign(**dict(
            zip(paths.DTN_COLS, [np.nan] * len(paths.DTN_COLS)))).assign(
                **dict(zip(paths.DTP_COLS, [np.nan] * len(paths.DTP_COLS))))
   
    # Initialize dictionaries
    primaries = {}
    destinations = {}
    comprehensives = {}

    for center_id, row in hospitals_dtn.iterrows():
        center_type = row['CenterType']
        name = str(center_id) # primary or comprehensive
        long_name = f'Center {center_id}' # hosp_key
        dtn_availability = row[paths.DTN_COLS].notna().all() # check if IVTPA data exists
        if dtn_availability: # if data exists
            if center_type == 'Primary':
                generic_distribution = sc.PRIMARY_DIST # HospitalTimeDistribution(47, 61, 83)
            else:
                generic_distribution =  sc.COMP_DIST # HospitalTimeDistribution(39, 52, 70)
            # Real hospital performance for DTN: requires hospital data and generic distribution
            dtn_dist = sc.HospitalTimeDistributionHybrid(
                float(row[paths.DTN_COLS[0]]), float(row[paths.DTN_COLS[1]]),
                float(row[paths.DTN_COLS[2]]), float(row[paths.DTN_COLS[3]]),
                generic_distribution)
        else: # no dtn data, use generic distributions only
            if center_type == 'Primary':
                dtn_dist = sc.PRIMARY_DIST # HospitalTimeDistribution(47, 61, 83)
            else:
                dtn_dist = sc.COMP_DIST # HospitalTimeDistribution(39, 52, 70)
        
        # DTP distribution for comprehensive centers only
        if center_type == 'Comprehensive':
            dtp_availability = row[paths.DTP_COLS].notna().all()
            if dtp_availability: # if dtp data exists for each hospital
                generic_distribution = sc.DTP_DIST # HospitalTimeDistribution(83, 145, 192)
                dtp_dist = sc.HospitalTimeDistributionHybrid(
                    float(row[paths.DTP_COLS[0]]), float(
                        row[paths.DTP_COLS[1]]), float(row[paths.DTP_COLS[2]]),
                    float(row[paths.DTP_COLS[3]]),
                    generic_distribution)
            else: # no dtp data, just use generic distribution
                dtp_dist = sc.DTP_DIST
        else: # no dtp distribution for primary centers
            dtp_dist = None

        # Create instance of new class: StrokeCenter that contains the hospital name and distributions
        if center_type == 'Comprehensive':
            comp = sc.StrokeCenter(
                long_name,
                name,
                sc.CenterType.COMPREHENSIVE,
                center_id,
                dtn_dist=dtn_dist,
                dtp_dist=dtp_dist)
            comprehensives[center_id] = comp # add to dictionary
        elif center_type == 'Primary':
            try: # test block of code for errors
                transfer_id = row['destination_KEY']
                transfer_time = float(row['transfer_time'])
                destinations[center_id] = (transfer_id, transfer_time) # add to dictionary
            except ValueError:
                warnings.warn(f'No transfer destination for {long_name}')

            prim = sc.StrokeCenter(
                long_name,
                name,
                sc.CenterType.PRIMARY,
                center_id,
                dtn_dist=dtn_dist)
            primaries[center_id] = prim # add to dictionary

    # Transfer destinations to comprehensive center from primary center
    # Primary center id is the dictionary key
    for primary_id, (transfer_id, transfer_time) in destinations.items(): # iterate through dictionary
        prim = primaries[primary_id] # get info about primary center
        transfer_destination = comprehensives[transfer_id] # get info about comprehensive destination center
        # Add attribute to primary center for transfer destination: comprehensive hospital key and transfer time
        prim.add_transfer_destination(transfer_destination, transfer_time) # function of StrokeCenter class

    # Returns list of StrokeCenter classes for each primary and comprehensive center
    # Attributes contain name, distribution, etc for each center
    return list(primaries.values()) + list(comprehensives.values())

def get_times(times_file):
    '''
    Generate a dictionary of dictionaries representing each point in the given
        file. Outer keys are location IDs, inner dictionaries have hospital IDs
        as keys and travel times as values. The input file is assumed to be
        formatted like `data/travel_times/Demo.csv`.
    '''
    def _parse_time(time_val):
        if ',' in time_val: # two travel times
            time_arr = [float(t.strip()) for t in time_val.split(',')]
            if len(time_arr) != 2:
                err_msg = 'Time value needs to be in format of'
                err_msg += 'no_traffic_time, traffic_time or just one number'
                raise ValueError(err_msg)
            return [np.min(time_arr),np.max(time_arr)]
        else:
            val = float(time_val)
            return [val,val]
    
    # Read in travel times file
    times = pd.read_csv(times_file,dtype=str,low_memory=False).set_index('LOC_ID')
    times = times.astype(str)
    times = times.applymap(_parse_time)
    return times.to_dict('index') # returns a dictionary

def get_next_patient_number(results_file):
    '''
    Get the number of the last patient recorded in the given results file.
        Returns 0 if the file does not exist
    '''
    if not os.path.isfile(results_file):
        return 0

    with open(results_file, 'r') as f:
        reader = csv.DictReader(f)
        patients = set()
        for row in reader:
            patients.add(int(row['Patient']))

    if patients:
        return max(patients) + 1
    else:
        return 0


def write_detailed_markov_outcomes(markov, fileprefix, point, times=None,
                                   optimal_strategy = None, write=False):
    filedir = Path(fileprefix)
    fileparent_dir = filedir.parent
    filename_prefix = filedir.stem + f'_loc={point}'
    # rearrange loc and AHAversion tag in filename (bad way)
    param_list = filename_prefix.split('_')
    tmp_version = param_list[-2]
    param_list[-2] = param_list[-1]
    param_list[-1] = tmp_version
    filename_prefix = '_'.join(param_list)

    # List of all strategies
    strategies = [str(strategy) for strategy in markov.strategies]
    print('k233', strategies.index('Comprehensive to K233 (CSC)'))
    print('k199', strategies.index('Comprehensive to K199 (CSC)'))

    qalys_df = pd.DataFrame(markov.qalys, columns=strategies)
    print(qalys_df)


    costs_df = pd.DataFrame(markov.costs, columns=strategies)
    lys_df = pd.DataFrame(markov.lys, columns=strategies)

    qalys_df['Variable'] = 'QALY'
    costs_df['Variable'] = 'Cost'
    lys_df['Variable'] = 'LY'
    pgood_df = pd.DataFrame(markov.ais_outcomes.p_good, columns=strategies)
    pgood_df['Variable'] = 'pgood'
    df = pd.concat([lys_df, qalys_df, costs_df, pgood_df], axis=0)
    df.index.name = 'Simulation'
    if times is not None:
        times_df = get_times_df(times)
        df = df.append(times_df)
    out_cols = ['Variable'] + strategies
    outpath = fileparent_dir / (filename_prefix + '_detailed_outcome.csv')
    df_out = df[out_cols]
    if optimal_strategy:
        df_out.columns = [c + ' - most C/E' if c == optimal_strategy else c
                      for c in df_out.columns]
    if write: df_out.to_csv(outpath)
    return df_out, outpath

def write_aggregated_markov_outcomes(markov, fileprefix, point, times=None, optimal_strategy = None
    , write = True):
    df, outpath =  write_detailed_markov_outcomes(markov, fileprefix, point, times)
    agg_df = df.groupby('Variable').describe()
    if optimal_strategy:
        # label which strategy is optimal in agg_df
        # reconstruct column multi index
        c_l = []
        for c in agg_df.columns:
            new_c = list(c)
            if new_c[0] == optimal_strategy:
                new_c[0] = optimal_strategy + ' - most C/E'
            c_l.append(tuple(new_c))
        agg_df.columns = pd.MultiIndex.from_tuples(c_l)
    agg_df.columns.names=['Strategy','statistic']
    agg_outpath = outpath.parent/(outpath.stem.replace('detailed','aggregated')+outpath.suffix)
    if write: agg_df.to_csv(agg_outpath)
    return agg_df, agg_outpath


def write_out_times(times, fileprefix, point):
    filedir = Path(fileprefix)
    fileparent_dir = filedir.parent
    # rearrange loc and AHAversion tag in filename (bad way)
    filename_prefix = filedir.stem + f'_loc={point}'
    param_list = filename_prefix.split('_')
    tmp_version = param_list[-2]
    param_list[-2] = param_list[-1]
    param_list[-1] = tmp_version
    filename_prefix = '_'.join(param_list)
    filename = fileparent_dir / (filename_prefix + f'_times.csv')
    primaries_times = times.onset_needle_primary
    p1 = pd.DataFrame(
        primaries_times,
        columns=times.get_strategies(constants.StrategyKind.PRIMARY))
    comprehensives_times = times.onset_needle_comprehensive
    c1 = pd.DataFrame(
        comprehensives_times,
        columns=times.get_strategies(constants.StrategyKind.COMPREHENSIVE))
    onset_evt_ship = times.onset_evt_ship
    p2 = pd.DataFrame(
        onset_evt_ship,
        columns=times.get_strategies(constants.StrategyKind.DRIP_AND_SHIP))
    # onset_evt_noship = times.onset_evt_noship
    df = pd.concat([p1, p2, c1], axis=1)
    df.index.name = 'Simulation'
    df.to_csv(filename)


def get_times_df(times):
    primaries_times = times.onset_needle_primary

    p1 = pd.DataFrame(
        primaries_times,
        columns=[
            str(s)
            for s in times.get_strategies(constants.StrategyKind.PRIMARY)
        ])
    comprehensives_times = times.onset_needle_comprehensive
    c1 = pd.DataFrame(
        comprehensives_times,
        columns=[
            str(s)
            for s in times.get_strategies(constants.StrategyKind.COMPREHENSIVE)
        ])
    onset_evt_ship = times.onset_evt_ship
    p2 = pd.DataFrame(
        onset_evt_ship,
        columns=[
            str(s)
            for s in times.get_strategies(constants.StrategyKind.DRIP_AND_SHIP)
        ])
    # onset_evt_noship = times.onset_evt_noship
    df = pd.concat([p1, p2, c1], axis=1)
    df.index.name = 'Simulation'
    df['Variable'] = 'onset_to_treatment_time'
    return df


def save_patient(outfile, patient_results, hospitals):
    '''
    Write the results from a single patient at many locations to the given
        file. Results should be a list of dictionaries, one for each row
        of the output where keys are column names.
    Will append to an existing result file if one exists
    '''
    # If not result file currentl exists, create a blank one
    if not os.path.isfile(outfile):
        fieldnames = [
            'Location', 'Patient', 'Use Real DTN', 'Varying Hospitals',
            'PSC Count', 'CSC Count', 'Sex', 'Age', 'Symptoms', 'RACE','NIHSS',
        ]
        fieldnames += [str(hospital) for hospital in hospitals]
        with open(outfile, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

    # Read in existing result file
    keys = ['Location', 'Patient', 'Use Real DTN', 'Varying Hospitals',
            'Sex', 'Age', 'RACE','NIHSS','Symptoms']
    df = pd.read_csv(outfile)
    df[keys] = df[keys].fillna('')
    df = df.set_index(keys)

    # Turn current patient results into a DataFrame
    patient_results_df = pd.DataFrame.from_records(patient_results)
    if 'NIHSS' not in patient_results_df.columns:
        patient_results_df = patient_results_df.assign(NIHSS='')
    elif 'RACE' not in patient_results_df.columns:
        patient_results_df = patient_results_df.assign(RACE='')
    patient_results_df = patient_results_df.set_index(keys)

    # Update result file with new patient results
    df.update(patient_results_df,overwrite=True)
    # Add in new patient_results that did not exist in result file
    df = df.append(patient_results_df[~patient_results_df.index.isin(df.index)],
                   sort=False)

    # Save result file
    df.to_csv(outfile)
