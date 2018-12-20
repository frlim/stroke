import pandas as pd
from pathlib import Path
import glob
import matplotlib.pyplot as plt
import numpy as np
import argparse
import matplotlib.cm as cm
from matplotlib.widgets import Slider,RadioButtons
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
df = pd.read_csv(file_dir).fillna(0)  # fill empty val wtih 0

# Get the columns' names
center_columns = df.columns[-20:]
cnum = len(center_columns)
sex_age_symp_race = df.columns[[5, 6, 7, 8]]
ax_title = output_path.name.split('.')[0]   # for axes title
nloc = 12  # number of locations there are in results
cloc = nloc - 1  # python indexing


def get_center_id(str):
    return str.split()[0]


# Current stroke model has 2 results: use hospital data == True or False
# We will use the True result for DTN, DTP from Demo.csv
df2 = df[0::2]

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
    # Get data for specific location ID as loc
    df3 = df2[loc::nloc]
    # Get the optimal center for each row aka each patient, return only center id no type
    best_by_patient = df3[center_columns].idxmax(axis=1).apply(get_center_id)
    n_sims = np.sum(df3[center_columns].values,axis=1) / 100 # want in terms of percent
    diff_1_2 = np.abs(np.diff(np.sort(df3[center_columns].values)[:,-2:],axis=1)).flatten()/n_sims
    unstable_logic = diff_1_2 < 1 # close calls
    for i, center_name in enumerate(sorted_centers):
        best_logic = best_by_patient == center_name
        circle_logic = best_logic & np.logical_not(unstable_logic)
        xs = df3["Age"][circle_logic].values
        ys = df3["RACE"][circle_logic].values
        zs = df3["Symptoms"][circle_logic].values
        optimal = np.any(best_logic)
        label = colors.make_label(loc, center_name, optimal)
        color = colors.make_color(center_name)
        ax.scatter(xs, ys, zs, c=color, marker='o', label=label)
        triangle_logic = best_logic & unstable_logic
        xs2 = df3["Age"][triangle_logic].values
        ys2 = df3["RACE"][triangle_logic].values
        zs2 = df3["Symptoms"][triangle_logic].values
        ax.scatter(xs2, ys2, zs2, c=color, marker='+')

def plot2(ax, loc):
    ''' Plot 2nd-best center '''
    sorted_centers = tdf.iloc[loc].sort_values().index  # sort by traveltime
    sorted_centers = sorted_centers[sorted_centers != "ID"]  # remove ID col
    # Get data for specific location ID as loc
    df3 = df2[loc::nloc]
    n_sims = np.sum(df3[center_columns].values,axis=1) / 100 # want in terms of percent
    diff_1_2 = np.abs(np.diff(np.sort(df3[center_columns].values)[:,-2:],axis=1)).flatten()/n_sims
    unstable_logic = diff_1_2 < 1 # close calls
    best_2nd_idx = np.argsort(df3[center_columns].values,axis=1)[:,-2]
    for i, center_name in enumerate(center_columns):
        center_name = center_name.split()[0]
        l = best_2nd_idx == i
        l = l & unstable_logic
        if np.any(l):
            xs = df3["Age"].loc[l].values
            ys = df3["RACE"].loc[l].values
            zs = df3["Symptoms"].loc[l].values
            label = colors.make_label(loc, center_name, False)
            color = colors.make_color(center_name)
            ax.scatter(xs, ys, zs, c=color, marker='+', label=label)



class ColorTracker:
    def __init__(self):
        self._psc = -1
        self._csc = -1
        self.dict = {}
        self.label_dict = {}

    def make_color(self, center_name):
        if center_name not in self.dict.keys():
            # generate new color only if not already in dict
            type = hdf[hdf["CenterID"] == int(center_name)]["CenterType"].iloc[0]
            if type == "Primary":
                self._psc += 1
                i = self._psc
                color = psc_colors[self._psc]
            else:
                self._csc += 1
                color = csc_colors[self._csc]
            self.dict[center_name]=color
        return self.dict[center_name]

    def make_label(self, loc, center_name, optimal):
        if center_name not in self.label_dict.keys():
            travel_time = tdf[center_name].iloc[loc]  # travel time
            center_info = hdf[hdf["CenterID"] == int(center_name)].iloc[
                0]  # pop out of series
            label = center_name
            label += '({:s})'.format(center_info["CenterType"][0])
            if not np.isnan(travel_time):
                label += ' TT:{:.0f}'.format(travel_time)
                label += ' DTN:({:.0f},{:.0f})'.format(center_info['DTN_1st'],
                                                   center_info['DTN_3rd'])
            if center_info["CenterType"] == 'Comprehensive':
                label += ' DTP:({:.0f},{:.0f})'.format(center_info['DTP_1st'],
                                                   center_info['DTP_3rd'])
            else: # primary center
                center_logic = hdf['CenterID']==int(center_name)
                dest = int(hdf[center_logic]['destinationID'].iloc[0])
                dest_type = hdf[hdf['CenterID']==dest]['CenterType'].iloc[0][0]# get 1st value
                transfer_time = hdf[center_logic]['transfer_time'].iloc[0]
                label += ' Tran:{:d}({:s}),{:.0f}'.format(dest,dest_type,transfer_time)
            self.label_dict[center_name] = label
        # if label was already made
        label = self.label_dict[center_name]
        if optimal:
            label = '*' + label
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
    radio.set_active(0)
    process_ax(ax)
    fig.canvas.draw_idle()

def click(label):
    ax.clear()
    if label == '1st':
        plot(ax,int(sloc.val))
    else:
        plot2(ax,int(sloc.val))
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
psc_colors = cm.get_cmap('autumn')(np.linspace(0, 1, n_psc))
csc_colors = cm.get_cmap('winter')(np.linspace(0, 1, n_csc))
colors = ColorTracker()

# Plotting gets called here
# 3D scatter plot
plot(ax, 0)
process_ax(ax)

# Location slider
axloc = plt.axes([0.20, 0.1, 0.3, 0.03], facecolor='silver')
sloc = Slider(axloc, 'Location ID', 0, cloc, valinit=0, valstep=1)
sloc.on_changed(update)

# Buttons
rax = plt.axes([0.025, 0.5, 0.08, 0.10], facecolor='silver')
radio = RadioButtons(rax, ('1st', '2nd'), active=0)
radio.on_clicked(click)
# Show
plt.show()
