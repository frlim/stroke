import pandas as pd
from pathlib import Path
import glob
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import animation
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'output_file', help='full path to file to model output')
    args = parser.parse_args()

# Load file
output_path = Path(args.output_file)
result = [i for i in glob.glob(str(output_path))]
file_dir = result[0]
df = pd.read_csv(file_dir)

# Type in input we're varying as column name of df
iteration_num = len(df["Age"].unique())
# Center columns
center_columns = df.columns[-20:]
# Split into CSC and PSC
cnum = len(center_columns)
centers_name = np.full(cnum, 'string')
centers_type = np.full(cnum, 'string')
for c, s in enumerate(center_columns):
    centers_name[c], centers_type[c] = s.split()


def data_one_patient(p_number):
    # Indexes in dataframe
    s_idx = 1 + p_number * 24
    e_idx = s_idx + 24
    idx_arr = np.arange(s_idx, e_idx, 2)

    # Get the "False" rows (each row is repeated twice for True/False)
    center_counts = df[center_columns].iloc[idx_arr]
    age = df["Age"].iloc[idx_arr].unique()
    sex = df["Sex"].iloc[idx_arr].unique()
    race = df["RACE"].iloc[idx_arr].unique()

    return center_counts, age, sex, race


def plot_first_patient():
    center_counts, age, sex, race = data_one_patient(0)
    # Sum vertically to get counts per center for this patient
    center_counts = center_counts.sum(axis=0)
    ind = np.arange(len(center_counts))

    fig, ax = plt.subplots()
    p_arr = plt.bar(ind, center_counts.values)

    # SET CSC to a diff color
    for i in (centers_type == '(CSC)').nonzero()[0]:
        p_arr[i].set_facecolor('g')
    # Labels for plot
    ax.set_xticks(ind)
    ax.set_xticklabels(centers_name)
    ax.set_ylim([0, 6000])
    ax.set_title('Age:{}   Sex:{}   RACE-score:{}'.format(age, sex, race))
    ax.set_ylabel('Number of times being the optimal choice')
    ax.set_xlabel('Center ID')

    return fig, ax, p_arr


def plot_the_rest(frame, p_arr, ax):
    center_counts, age, sex, race = data_one_patient(frame)
    # Sum vertically to get counts per center for this patient
    center_counts = center_counts.sum(axis=0)
    # Update height of each bar
    for i, p in enumerate(p_arr):
        p.set_height(center_counts[i])
        ax.set_title('Age:{}   Sex:{}   RACE-score:{}'.format(age, sex, race))


fig, ax, p_arr = plot_first_patient()
anim = animation.FuncAnimation(
    fig,
    plot_the_rest,
    repeat=True,
    blit=False,
    frames=iteration_num,
    fargs=(p_arr, ax),
    interval=250)
plt.show()
