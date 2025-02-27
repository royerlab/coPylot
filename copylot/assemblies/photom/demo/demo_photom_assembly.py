# %%
from copylot.assemblies.photom.photom import PhotomAssembly
from copylot.assemblies.photom.utils import affine_transform
from copylot.hardware.mirrors.optotune.mirror import OptoMirror
from copylot.assemblies.photom.photom_mock_devices import MockLaser, MockMirror
from copylot.hardware.cameras.flir.flir_camera import FlirCamera
import time
from copylot.hardware.lasers.vortran.vortran import VortranLaser as Laser

# %%
config_file = './photom_VIS_config.yml'
# Mock imports for the mirror and the lasers
# laser = MockLaser(name='Mock Laser', power=0)
laser = Laser(name='vortran405', port='COM9')
mirror = OptoMirror(com_port='COM8')


# %%
# Test the moving of the mirrors
mirror.position = (0.009, 0.0090)
time.sleep(1)
mirror.position = (0.000, 0.000)

curr_pos = photom_device.get_position(mirror_index=0)
print(curr_pos)
assert curr_pos == (0.000, 0.000)
# %%
## Test using the photom_device
camera_sensor_width = 1280
camera_sensor_height = 1280

photom_device = PhotomAssembly(
    laser=[laser],
    mirror=[mirror],
    affine_matrix_path=[
        r'C:\Users\ZebraPhysics\Documents\GitHub\coPylot\copylot\assemblies\photom\demo\test_tmp.yml'
    ],
    camera=[camera],
)
photom_device.set_position(
    mirror_index=0, position=[camera_sensor_width // 2, camera_sensor_height // 2]
)
curr_pos = photom_device.get_position(mirror_index=0)
print(curr_pos)

# %%
# Demo the grid scanning
from copylot.assemblies.photom.utils.scanning_algorithms import (
    calculate_rectangle_corners,
    generate_grid_points,
)
import time

mirror_roi = [[-0.01, 0.0], [0.015, 0.018]]
grid_points = generate_grid_points(rectangle_size=mirror_roi, n_points=5)
for idx, coord in enumerate(grid_points):
    mirror.position = [coord[0], coord[1]]
    print(coord)
    time.sleep(0.5)


# %%
# Load the camera
cam = FlirCamera()
cam.open()
photom_device = PhotomAssembly(
    laser=[laser],
    mirror=[mirror],
    affine_matrix_path=[r'./affine_T.yml'],
    camera=[cam],
)
# %%
# Turn on the laser
photom_device.laser[0].power = 0.0
photom_device.laser[0].toggle_emission = True
photom_device.laser[0].power = 30.0
# %%
# mirror_roi = [
#     [-0.005, 0.018],  # [y,x]
#     [0.013, 0.0],
# ]  # Top-left and Bottom-right corners of the mirror ROI
mirror_roi = [[-0.01, 0.0], [0.015, 0.018]]  # [x,y]
photom_device.camera[0].exposure = 1000
photom_device.camera[0].gain = 0
photom_device.camera[0].flip_horizontal = True
photom_device.camera[0].pixel_format = 'Mono16'
photom_device.calibrate_w_camera(
    mirror_index=0,
    camera_index=0,
    rectangle_boundaries=mirror_roi,
    grid_n_points=5,
    config_file='./affine_T_v1_projT.yml',
    save_calib_stack_path='./calib_stack',
    verbose=True,
)

# %%
