"""
Read input files to prepare for model runs
"""
import csv
import os
import warnings
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
    if dtn_file:
        dtn = paths.load_dtn(dtn_file)
        hospitals_dtn = hospitals.join(dtn, how='left', rsuffix='_dtn')
    else:
        # use default dtn, assign NaN to treatment time columns
        hospitals_dtn = hospitals.assign(**dict(
            zip(paths.DTN_COLS, [np.nan] * len(paths.DTN_COLS)))).assign(
                **dict(zip(paths.DTP_COLS, [np.nan] * len(paths.DTP_COLS))))

    primaries = {}
    destinations = {}
    comprehensives = {}
    for center_id, row in hospitals_dtn.iterrows():
        center_type = row['CenterType']
        name = str(center_id)
        long_name = f'Center {center_id}'
        dtn_availability = row[paths.DTN_COLS].notna().all()
        if dtn_availability:
            if center_type == 'Primary':
                generic_distribution = sc.PRIMARY_DIST
            else:
                generic_distribution =  sc.COMP_DIST
            dtn_dist = sc.HospitalTimeDistributionHybrid(
                float(row[paths.DTN_COLS[0]]), float(row[paths.DTN_COLS[1]]),
                float(row[paths.DTN_COLS[2]]), generic_distribution)
        else:
            if center_type == 'Primary':
                dtn_dist = sc.PRIMARY_DIST
            else:
                dtn_dist = sc.COMP_DIST
        if center_type == 'Comprehensive':
            dtp_availability = row[paths.DTP_COLS].notna().all()
            if dtp_availability:
                generic_distribution = sc.DTP_DIST
                dtp_dist = sc.HospitalTimeDistribution(
                    float(row[paths.DTP_COLS[0]]), float(
                        row[paths.DTP_COLS[1]]), float(row[paths.DTP_COLS[2]]),
                    generic_distribution)
            else:
                dtp_dist = sc.DTP_DIST
        else:
            dtp_dist = None

        if center_type == 'Comprehensive':
            comp = sc.StrokeCenter(
                long_name,
                name,
                sc.CenterType.COMPREHENSIVE,
                center_id,
                dtn_dist=dtn_dist,
                dtp_dist=dtp_dist)
            comprehensives[center_id] = comp
        elif center_type == 'Primary':
            try:
                transfer_id = row['destination_KEY']
                transfer_time = float(row['transfer_time'])
                destinations[center_id] = (transfer_id, transfer_time)
            except ValueError:
                warnings.warn(f'No transfer destination for {long_name}')
            except:
                # old structure
                try:
                    transfer_id = int(float(row['destinationID']))
                    transfer_time = float(row['transfer_time'])
                    destinations[center_id] = (transfer_id, transfer_time)
                except ValueError:
                    warnings.warn(f'No transfer destination for {long_name}')
            prim = sc.StrokeCenter(
                long_name,
                name,
                sc.CenterType.PRIMARY,
                center_id,
                dtn_dist=dtn_dist)
            primaries[center_id] = prim

    for primary_id, (transfer_id, transfer_time) in destinations.items():
        prim = primaries[primary_id]
        transfer_destination = comprehensives[transfer_id]
        prim.add_transfer_destination(transfer_destination, transfer_time)

    return list(primaries.values()) + list(comprehensives.values())


def get_times(times_file):
    '''
    Generate a dictionary of dictionaries representing each point in the given
        file. Outer keys are location IDs, inner dictionaries have hospital IDs
        as keys and travel times as values. The input file is assumed to be
        formatted like `data/travel_times/Demo.csv`.
    '''
    return pd.read_csv(times_file).set_index('LOC_ID').to_dict('index')


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


def get_header(hospitals):
    '''
    Get a list of column names for an output file with the given hospitals
    '''
    fieldnames = [
        'Location', 'Patient', 'Varying Hospitals', 'PSC Count', 'CSC Count',
        'Sex', 'Age', 'Symptoms', 'RACE'
    ]
    fieldnames += [str(hospital) for hospital in hospitals]
    return fieldnames


def write_detailed_markov_outcomes(markov, fileprefix, point, times=None, write=False):
    filedir = Path(fileprefix)
    fileparent_dir = filedir.parent
    filename_prefix = filedir.stem + f'_loc={point}'
    # rearrange loc and AHAversion tag in filename (bad way)
    param_list = filename_prefix.split('_')
    tmp_version = param_list[-2]
    param_list[-2] = param_list[-1]
    param_list[-1] = tmp_version
    filename_prefix = '_'.join(param_list)
    strategies = [str(strategy) for strategy in markov.strategies]
    qalys_df = pd.DataFrame(markov.qalys, columns=strategies)
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
    if write: df[out_cols].to_csv(outpath)
    return df[out_cols], outpath

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
    '''
    fieldnames = get_header(hospitals)

    if not os.path.isfile(outfile):
        with open(outfile, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

    df = pd.read_csv(outfile)
    keys = result_input_keys()
    for results in patient_results:
        # # add zero counts for hospital that are never optimal
        # zero_c = {
        #     str(hospital): 0
        #     for hospital in hospitals if str(hospital) not in results.keys()
        # }
        # results.update(zero_c)
        try:
            for i, k in enumerate(keys):
                if i == 0:
                    # print(df[k])
                    l = df[k] == results[k]
                else:
                    l = l & (df[k] == results[k])
            if l.any():
                row_num = df.loc[l].index[0]
                # transfer old patient number to new result
                pid = df['Patient'].iloc[row_num]
                results['Patient'] = pid
                # replace with new result
                df.iloc[row_num] = pd.Series(results)
            else:
                # append to existing data frame
                df = df.append(pd.Series(results), ignore_index=True)
        except:
            df = df.append(pd.Series(results), ignore_index=True)
    # Save results
    # convert to integer
    df = df.astype('int64', errors='ignore', copy=False)
    df.to_csv(outfile, index=False)
    # To minmize memory usage
    del df
    gc.collect()


def result_input_keys():
    'Dictionary with all keys and empty value'
    keys = []
    keys.append('Location')
    keys.append('Varying Hospitals')
    keys.append('Sex')
    keys.append('Age')
    keys.append('RACE')
    keys.append('Symptoms')
    return keys
