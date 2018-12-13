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
    out_default = str(Path('output/times=Demo_hospitals=Demo_random_python.csv'))
    parser = argparse.ArgumentParser()
    parser.add_argument('output',default=out_default,help='path to output file')
    args = parser.parse_args()

# Load file
output_path = Path(args.output)
result = [i for i in glob.glob(str(output_path))]
file_dir = result[0]
df = pd.read_csv(file_dir)

# Center columns
center_columns=df.columns[-20:]
cnum = len(center_columns)
sex_age_symp_race = df.columns[[5,6,7,8]]
nloc = 12 # number of locations there are in results
cloc = nloc - 1 # python indexing

df2=df[1::2]
best_by_patient = df2[center_columns].idxmax(axis=1)


fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
colors = cm.viridis(np.linspace(0, 1, cnum))

def plot(ax,loc):
    for i,center_name in enumerate(center_columns):
        best_logic = best_by_patient == center_name
        if np.any(best_logic):
            df3 = df2[loc::nloc]
            xs = df3["Age"][best_logic].values
            ys = df3["RACE"][best_logic].values
            zs = df3["Symptoms"][best_logic].values
            ax.scatter(xs,ys,zs,c=colors[i],marker='o',label=center_name)

def process_ax(ax):
    ax.set_xlabel('Age')
    ax.set_xlim([30,85])
    ax.set_ylabel('RACE score')
    ax.set_ylim([0,9])
    ax.set_zlabel('Time since Onset')
    ax.set_zlim([10,100])
    ax.legend(loc='upper right')

def update(val):
    loc = sloc.val
    ax.clear()
    plot(ax,int(loc))
    process_ax(ax)
    fig.canvas.draw_idle()

plot(ax,0)
process_ax(ax)
axloc = plt.axes([0.25, 0.1, 0.65, 0.03], facecolor='lightgoldenrodyellow')
sloc = Slider(axloc, 'Location ID', 0, cloc, valinit=0, valstep=1)
sloc.on_changed(update)

plt.show()
