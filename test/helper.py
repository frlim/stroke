"""
Helper functions to use in building up tests
"""
import stroke.stroke_center as sc


def get_centers():
    """Get a small default set of stroke centers with destinations"""
    comprehensives = []
    comprehensive_times = [50, 60]
    for i, comp_time in enumerate(comprehensive_times):
        comprehensive = sc.StrokeCenter.comprehensive(comp_time, i)
        comprehensives.append(comprehensive)

    primaries = []
    prim_times = [15, 30, 20]
    transfer_times = [65, 30, 30]
    transfer_dests = [0, 1, 0]
    for i, prim_time in enumerate(prim_times):
        primary = sc.StrokeCenter.primary(prim_time, i)
        td = comprehensives[transfer_dests[i]]
        primary.add_transfer_destination(td, transfer_times[i])
        primaries.append(primary)

    return primaries, comprehensives
