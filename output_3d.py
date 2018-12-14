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

if __name__ == '__main__':
    out_default = str(
        Path('output/times=Demo_hospitals=Demo_random_python.csv'))
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'output', default=out_default, help='path to output file')
    args = parser.parse_args()

# Load file
output_path = Path(args.output)
result = [i for i in glob.glob(str(output_path))]
file_dir = result[0]
#file_dir = out_default
df = pd.read_csv(file_dir)

# Get the columns' names
center_columns = df.columns[-20:]
cnum = len(center_columns)
sex_age_symp_race = df.columns[[5, 6, 7, 8]]
ax_title = df["Sex"].unique()  # for axes title
nloc = 12  # number of locations there are in results
cloc = nloc - 1  # python indexing

# Current stroke model repeats results twice so take only the odd rows
df2 = df[1::2]
# Get the optimal center for each row aka each patient
best_by_patient = df2[center_columns].idxmax(axis=1)

# Get travel times file for the legend
times_path = str(Path('data/travel_times/Demo.csv'))
tdf = pd.read_csv(times_path)


def plot(ax, loc):
    ic = 0
    for center_name in center_columns:
        best_logic = best_by_patient == center_name
        if np.any(best_logic):
            df3 = df2[loc::nloc]
            xs = df3["Age"][best_logic].values
            ys = df3["RACE"][best_logic].values
            zs = df3["Symptoms"][best_logic].values
            label = make_label(loc, center_name)
            ax.scatter(xs, ys, zs, c=colors[ic], marker='o', label=label)
            ic += 1


def make_label(loc, center_name):
    row = tdf.iloc[loc]  # travel times for location ID
    row = row[~row.isnull()]  # remove NaN time entries
    row = row[1:]  # Remove "ID" header
    row = row.sort_values(axis=0)  # sort by increasing time
    name, type = center_name.split()  # Split out to name and type
    distance = (row.index.values == name).nonzero()[0]
    if distance.size > 0:  # center has travel time
        d = distance[0]  # pop scalar from array
        time = row.iloc[d]  # travel time for this center in mins
        label = center_name + '  d:{:d}  t:{:.1f}'.format(d, time)
    else:
        label = center_name
    return label


# For slider to work
def process_ax(ax):
    ax.set_xlabel('Age')
    ax.set_xlim([30, 85])
    ax.set_ylabel('RACE score')
    ax.set_ylim([0, 9])
    ax.set_zlabel('Time since Onset')
    ax.set_zlim([10, 100])
    ax.legend(loc='upper right')
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
fig.tight_layout()  # decrease margin
ax = fig.add_subplot(111, projection='3d')
ax.set_facecolor('#A9A9A9')  # set background to medium gray
fig.patch.set_facecolor('#A9A9A9')  # match with axes background for aesthetics
n_best_center = len(
    best_by_patient.unique())  # < cnum, give better color distinction
colors = cm.seismic(np.linspace(0, 1, n_best_center))

# Plotting gets called here
# 3D scatter plot
plot(ax, 0)
process_ax(ax)

# Location slider
axloc = plt.axes([0.25, 0.1, 0.65, 0.03], facecolor='silver')
sloc = Slider(axloc, 'Location ID', 0, cloc, valinit=0, valstep=1)
sloc.on_changed(update)

# Show
plt.show()
