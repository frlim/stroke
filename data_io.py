"""
Read input files to prepare for model runs
"""
import csv
import os
import warnings
import stroke.stroke_center as sc
import pandas as pd
import gc
import xlwings as xw

def get_hospitals(hospital_file, use_default_times=False):
    '''Generate a list of StrokeCenters from a csv
        file containing transfer destinations and times. Optionally use
        recorded hospital performance metrics. The CSV is assumed to be
        formatted like `data/hospitals/Demo.csv`
    '''
    primaries = {}
    destinations = {}
    comprehensives = {}
    with open(hospital_file, 'r') as f:
        reader = csv.DictReader(f)

        for row in reader:
            center_id = int(row['CenterID'])
            center_type = row['CenterType']
            name = str(center_id)
            long_name = f'Center {center_id}'

            if use_default_times:
                dtn_dist = None
                dtp_dist = None
            else:
                dtn_dist = sc.HospitalTimeDistribution(
                    float(row['DTN_1st']),
                    float(row['DTN_Median']),
                    float(row['DTN_3rd'])
                )
                if center_type == 'Comprehensive':
                    dtp_dist = sc.HospitalTimeDistribution(
                        float(row['DTP_1st']),
                        float(row['DTP_Median']),
                        float(row['DTP_3rd'])
                    )
                else:
                    dtp_dist = None

            if center_type == 'Comprehensive':
                comp = sc.StrokeCenter(long_name, name,
                                       sc.CenterType.COMPREHENSIVE,
                                       center_id, dtn_dist=dtn_dist,
                                       dtp_dist=dtp_dist)
                comprehensives[center_id] = comp
            elif center_type == 'Primary':
                try:
                    transfer_id = int(float(row['destinationID']))
                    transfer_time = float(row['transfer_time'])
                    destinations[center_id] = (transfer_id, transfer_time)
                except ValueError:
                    warnings.warn(f'No transfer destination for {long_name}')
                prim = sc.StrokeCenter(long_name, name, sc.CenterType.PRIMARY,
                                       center_id, dtn_dist=dtn_dist)
                primaries[center_id] = prim

    for primary_id, (transfer_id, transfer_time) in destinations.items():
        prim = primaries[primary_id]
        transfer_destination = comprehensives[transfer_id]
        prim.add_transfer_destination(transfer_destination, transfer_time)

    return list(primaries.values()) + list(comprehensives.values())


def _load_dtn_file(dtn_file, cell_range='A1:M275'):
    sheet = xw.Book(str(dtn_file)).sheets[0]
    return sheet[cell_range].options(
        convert=pd.DataFrame, index=False, header=True).value


def get_hospitals_real_data(hospital_file, dtn_file, cell_range='A1:M275'):
    '''Generate a list of StrokeCenters from a csv
        file containing transfer destinations and times. Optionally use
        recorded hospital performance metrics. The CSV is assumed to be
        formatted like `data/hospitals/Demo.csv`
        dtn_file: excel spreadsheet, deidentified and password-protected
        if a hospital doesn't have DTN or DTP time, use default distributions
        in stroke_center.py
    '''
    # load spreadsheet
    dtn = _load_dtn_file(dtn_file, cell_range)
    hospitals = pd.read_csv(hospital_file)
    hospitals_dtn = hospitals.merge(dtn, on='HOSP_KEY', how='left')
    primaries = {}
    destinations = {}
    comprehensives = {}
    dtn_cols = ['IVTPA_P25','IVTPA_MEDIAN','IVTPA_P75']
    dtp_cols = ['ARTPUNC_P25','ARTPUNC_MEDIAN','ARTPUNC_P75']
    for idx, row in hospitals_dtn.iterrows():
        center_id = int(row['HOSP_KEY'])
        center_type = row['CenterType']
        name = str(center_id)
        long_name = f'Center {center_id}'
        dtn_availability = row[dtn_cols].notna().all()
        if dtn_availability:
            dtn_dist = sc.HospitalTimeDistribution(
                float(row['IVTPA_P25']), float(row['IVTPA_MEDIAN']),
                float(row['IVTPA_P75']))
        else:
            if center_type == 'Primary':
                dtn_dist = sc.PRIMARY_DIST
            else:
                dtn_dist = sc.COMP_DIST
        if center_type == 'Comprehensive':
            dtp_availability = row[dtp_cols].notna().all()
            if dtp_availability:
                dtp_dist = sc.HospitalTimeDistribution(
                    float(row['ARTPUNC_P25']), float(row['ARTPUNC_MEDIAN']),
                    float(row['ARTPUNC_P75']))
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


def get_times_real_data(times_file):
    '''
    Generate a dictionary of dictionaries representing each point in the given
        file. Outer keys are location IDs, inner dictionaries have hospital IDs
        as keys and travel times as values. The input file is assumed to be
        formatted like `data/travel_times/Demo.csv`.
    '''
    return pd.read_csv(times_file).set_index('ID').to_dict('index')


def get_times(times_file):
    '''
    Generate a dictionary of dictionaries representing each point in the given
        file. Outer keys are location IDs, inner dictionaries have hospital IDs
        as keys and travel times as values. The input file is assumed to be
        formatted like `data/travel_times/Demo.csv`.
    '''
    with open(times_file, 'r') as f:
        reader = csv.DictReader(f)
        return {int(row['ID']): row for row in reader}


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
        'Location', 'Patient', 'Varying Hospitals', 'PSC Count',
        'CSC Count', 'Sex', 'Age', 'Symptoms', 'RACE'
    ]
    fieldnames += [str(hospital) for hospital in hospitals]
    return fieldnames


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
