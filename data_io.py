"""
Read input files to prepare for model runs
"""
import os
import pandas as pd
import stroke.stroke_center as sc


def get_hospitals(hospital_file, use_default_times=False):
    '''Generate a list of StrokeCenters from a csv
        file containing transfer destinations and times. Optionally use
        recorded hospital performance metrics. The CSV is assumed to be
        formatted like `data/hospitals/CT.csv` and be in the data/hospitals
        directory
    '''
    hospital_file = os.path.join('data', 'hospitals', hospital_file)
    data = pd.read_csv(hospital_file, sep='|')

    comp_dict = {}
    comp_data = data[data.CenterType == 'Comprehensive']
    for i in comp_data.index:
        name = comp_data.OrganizationName[i]
        city = comp_data.City[i] + ', ' + comp_data.State[i]
        long_name = f'{name} ({city})'
        if use_default_times:
            dtn_dist = None
            dtp_dist = None
        else:
            dtn_dist = sc.HospitalTimeDistribution(
                comp_data.DTN_1st[i],
                comp_data.DTN_Median[i],
                comp_data.DTN_3rd[i]
            )
            dtp_dist = sc.HospitalTimeDistribution(
                comp_data.DTP_1st[i],
                comp_data.DTP_Median[i],
                comp_data.DTP_3rd[i]
            )

        center_id = comp_data.CenterID[i]

        comp = sc.StrokeCenter(long_name, name, sc.CenterType.COMPREHENSIVE,
                               center_id,
                               dtn_dist=dtn_dist, dtp_dist=dtp_dist)
        comp_dict[center_id] = comp

    primaries = []
    prim_data = data[data.CenterType == 'Primary']
    for i in prim_data.index:
        name = prim_data.OrganizationName[i]
        city = prim_data.City[i] + ', ' + prim_data.State[i]
        long_name = f'{name} ({city})'
        if use_default_times:
            dtn_dist = None
        else:
            dtn_dist = sc.HospitalTimeDistribution(
                prim_data.DTN_1st[i],
                prim_data.DTN_Median[i],
                prim_data.DTN_3rd[i]
            )

        prim = sc.StrokeCenter(long_name, name, sc.CenterType.PRIMARY,
                               prim_data.CenterID[i], dtn_dist=dtn_dist)
        transfer_id = int(prim_data.destinationID[i])
        transfer_time = prim_data.transfer_time[i]
        transfer_destination = comp_dict[transfer_id]

        prim.add_transfer_destination(transfer_destination, transfer_time)
        primaries.append(prim)

    return primaries + list(comp_dict.values())
