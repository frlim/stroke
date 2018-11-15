"""
Read input files to prepare for model runs
"""
import csv
import os
import stroke.stroke_center as sc


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
                comp = sc.StrokeCenter(long_name, name, sc.CenterType.COMPREHENSIVE,
                                       center_id, dtn_dist=dtn_dist, dtp_dist=dtp_dist)
                comprehensives[center_id] = comp
            elif center_type == 'Primary':
                transfer_id = int(float(row['destinationID']))
                transfer_time = float(row['transfer_time'])
                destinations[center_id] = (transfer_id, transfer_time)
                prim = sc.StrokeCenter(long_name, name, sc.CenterType.PRIMARY,
                                       center_id, dtn_dist=dtn_dist)
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
    
    return max(patients) + 1
    

def get_header(results_file):
    '''
    Get a list of column names for the given results file if it exists.
    '''
    if not os.path.isfile(results_file):
        return None
        
    with open(results_file, 'r') as f:
        reader = csv.DictReader(f)
        return reader.fieldnames
    
            
def save_patient(outfile, patient_results):
    '''
    Write the results from a single patient at many locations to the given
        file. Results should be a list of dictionaries, one for each row
        of the output where keys are column names.
    '''
    fieldnames = get_header(outfile)
    if fieldnames is None:
        fieldnames = list(patient_results[0].keys())
        
    if not os.path.isfile(results_file):
        with open(results_file, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
    with open(results_file, 'a') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames,
                                restval=0)
        for results in patient_results:
            writer.writerow(results)
