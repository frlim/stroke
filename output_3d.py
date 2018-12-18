import pandas as pd
from pathlib import Path
import glob
import matplotlib.pyplot as plt
import numpy as np
import argparse
import matplotlib.cm as cm
from matplotlib.widgets import Slider
# This import registers the 3D projection, but is otherwise unused.
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 unused import

out_path = Path('output')
out_name = 'sich*.csv'
out_default = str(out_path / out_name)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'output', nargs='?', default=out_default, help='path to output file')
    args = parser.parse_args()

# Load file
output_path = Path(args.output)
result = [i for i in glob.glob(str(output_path))]
file_dir = result[0]
df = pd.read_csv(file_dir)

# Get the columns' names
center_columns = df.columns[-20:]
cnum = len(center_columns)
sex_age_symp_race = df.columns[[5, 6, 7, 8]]
ax_title = df["Sex"].unique()  # for axes title
nloc = 12  # number of locations there are in results
cloc = nloc - 1  # python indexing


def get_center_id(str):
    return str.split()[0]


# Current stroke model repeats results twice so take only the odd rows
df2 = df[1::2]

# Get travel times file for the legend
times_path = str(Path('data/travel_times/Demo.csv'))
tdf = pd.read_csv(times_path)

# Get travel times file for the legend
hosp_path = str(Path('data/hospitals/Demo.csv'))
hdf = pd.read_csv(hosp_path)

# hdf["CenterID"]


def plot(ax, loc):
    sorted_centers = tdf.iloc[loc].sort_values().index  # sort by traveltime
    sorted_centers = sorted_centers[sorted_centers != "ID"]  # remove ID col
    colors = ColorTracker()
    for i, center_name in enumerate(sorted_centers):
        # Get data for specific location ID as loc
        df3 = df2[loc::nloc]
        # Get the optimal center for each row aka each patient, return only center id no type
        best_by_patient = df3[center_columns].idxmax(
            axis=1).apply(get_center_id)
        best_logic = best_by_patient == center_name
        xs = df3["Age"][best_logic].values
        ys = df3["RACE"][best_logic].values
        zs = df3["Symptoms"][best_logic].values
        optimal = np.any(best_logic)
        label = colors.make_label(loc, center_name, optimal)
        color = colors.make_color(center_name)
        ax.scatter(xs, ys, zs, c=color, marker='o', label=label)


class ColorTracker:
    def __init__(self):
        self._psc = -1
        self._csc = -1

    def make_color(self, center_name):
        type = hdf[hdf["CenterID"] == int(center_name)]["CenterType"].iloc[0]
        if type == "Primary":
            self._psc += 1
            i = self._psc
            colors = psc_colors
        else:
            self._csc += 1
            i = self._csc
            colors = csc_colors
        return colors[-i - 1]

    def make_label(self, loc, center_name, optimal):
        travel_time = tdf[center_name].iloc[loc]  # travel time
        center_info = hdf[hdf["CenterID"] == int(center_name)].iloc[
            0]  # pop out of series
        label = center_name
        if optimal: label = '*' + label
        label += '({:s})'.format(center_info["CenterType"][0])
        if np.isnan(travel_time): return label
        label += ' TT:{:.0f}'.format(travel_time)
        label += ' DTN:({:.0f},{:.0f})'.format(center_info['DTN_1st'],
                                               center_info['DTN_3rd'])
        if center_info["CenterType"] == "Primary": return label
        label += ' DTP:({:.0f},{:.0f})'.format(center_info['DTP_1st'],
                                               center_info['DTP_3rd'])
        return label


# For slider to work
def process_ax(ax):
    ax.set_xlabel('Age')
    ax.set_xlim([30, 85])
    ax.set_ylabel('RACE score')
    ax.set_ylim([0, 9])
    ax.set_zlabel('Time since Onset')
    ax.set_zlim([10, 100])
    ax.legend(loc='center left', bbox_to_anchor=(0.95, 0.5))
    ax.set_title(ax_title)


# For slider to work
def update(val):
    loc = sloc.val
    ax.clear()
    plot(ax, int(loc))
    process_ax(ax)
    fig.canvas.draw_idle()


# Set up figure. axes, and color
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.set_facecolor('#A9A9A9')  # set background to medium gray
fig.patch.set_facecolor('#A9A9A9')  # match with axes background for aesthetics
ax.w_xaxis.set_pane_color((.5, .5, .5))
ax.w_yaxis.set_pane_color((.5, .5, .5))
ax.w_zaxis.set_pane_color((.5, .5, .5))
# Shrink current axis by 10%
box = ax.get_position()
ax.set_position([box.x0, box.y0, box.width * 0.9,
                 box.height])  # set for 1 time
n_psc = 16
n_csc = 4
psc_colors = cm.get_cmap('cool')(np.linspace(0, 1, n_psc))
csc_colors = cm.get_cmap('summer')(np.linspace(0, 1, n_csc))

# Plotting gets called here
# 3D scatter plot
plot(ax, 0)
process_ax(ax)

# Location slider
axloc = plt.axes([0.20, 0.1, 0.3, 0.03], facecolor='silver')
sloc = Slider(axloc, 'Location ID', 0, cloc, valinit=0, valstep=1)
sloc.on_changed(update)

# Show
plt.show()
