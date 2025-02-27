# %%
import sys
import os

sys.path.append(os.path.join(os.pardir, os.pardir, os.pardir))
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from copylot.assemblies.photom.utils.scanning_algorithms import ScanAlgorithm
from copylot.assemblies.photom.utils.affine_transform import AffineTransform

mpl.rcParams['agg.path.chunksize'] = 20000

# %%
initial_coord = (549.5, 754.5)
size = (300, 100)
gap = 10
shape = 'disk'
sec_per_cycle = 0.003
sg = ScanAlgorithm(initial_coord, size, gap, shape, sec_per_cycle)

# coord = sg.generate_cornerline()
coord = sg.generate_lissajous()
# coord = sg.generate_sin()

plt.figure()
plt.plot(coord[0], coord[1])
plt.show()

# Load affine matrix
trans_obj = AffineTransform(config_file='../settings/affine_transform.yml')

# %%
# compute affine matrix
xv, yv = np.meshgrid(
    np.linspace(1, 10, 10),
    np.linspace(1, 10, 10),
)
coord = (list(xv.flatten()), list(yv.flatten()))
pts1 = [
    [xv[0, 0], yv[0, 0]],
    [xv[-1, -1], yv[-1, -1]],
    [xv[0, -1], yv[0, -1]],
]

pts2 = [
    [xv[0, 0] + 1, yv[0, 0] + 1],
    [xv[-1, -1] + 1, yv[-1, -1] + 1],
    [xv[0, -1] + 1, yv[0, -1] + 1],
]
trans_obj.compute_affine_matrix(pts1, pts2)
# %%
trans_obj.save_matrix(config_file='./test.yml')
# %%
data_trans = trans_obj.apply_affine(coord)

plt.figure()
plt.plot(coord[0], coord[1])
plt.plot(data_trans[0], data_trans[1])
plt.legend(['raw', 'transformed'])
plt.show()

# %%
