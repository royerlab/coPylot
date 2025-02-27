# %%
from copylot.assemblies.photom.photom import PhotomAssembly
from copylot.assemblies.photom.utils import affine_transform
from copylot.hardware.mirrors.optotune.mirror import OptoMirror

# from copylot.assemblies.photom.photom_mock_devices import MockLaser, MockMirror
from copylot.hardware.lasers.vortran.vortran import VortranLaser
from copylot.hardware.cameras.flir.flir_camera import FlirCamera
import time
from copylot.assemblies.photom.utils.arduino import ArduinoPWM

# %%
config_file = './photom_VIS_config.yml'
# Mock imports for the mirror and the lasers
laser = VortranLaser('Mock Laser', port='COM9')
mirror = OptoMirror(com_port='COM8')
cam = FlirCamera()
cam.open()

# TODO: modify COM port based on the system
arduino = ArduinoPWM(serial_port='COM10', baud_rate=115200)

# %%
# Make the photom device
photom_device = PhotomAssembly(
    laser=[laser],
    mirror=[mirror],
    affine_matrix_path=[r'./affine_T.yml'],
    camera=[cam],
)

# %%
# Perform calibration
# Top-left and Bottom-right corners of the mirror ROI
mirror_roi = [
    [
        0.018,
        -0.005,
    ],  # [x,y]
    [
        0.0,
        0.013,
    ],
]  # [x,y]

photom_device.camera[0].exposure = 10_000  # [us]
photom_device.camera[0].gain = 0
# photom_device.camera[0].pixel_format = 'Mono16'

config_file = r'./test_auto_affineT.yml'

photom_device.laser[0].power = 5  # [mW]
photom_device.laser[0].pulse_mode = 0
photom_device.laser[0].toggle_emission = True
photom_device.calibrate_w_camera(
    mirror_index=0,
    camera_index=0,
    rectangle_boundaries=mirror_roi,
    grid_n_points=5,
    config_file=config_file,
    save_calib_stack_path='./calib_stack',
    verbose=True,
)
photom_device.laser[0].toggle_emission = False

# %%
# Remove the camera from the photom_device so we can use it in the acquisiton engine
photom_device.camera[0].exposure = 10_000  # [us]
photom_device.camera = []


# %%
# Demo that laser should be in the center
photom_device.laser[0].toggle_emission = True
photom_device.set_position(0, [1024, 1224])  # center [y,x]
time.sleep(3)
photom_device.laser[0].toggle_emission = False
# %%
# Set the ablation parameters
# Test the PWM signal
duty_cycle = 50  # [%] (0-100)
period_ms = 500  # [ms]
total_duration_ms = 5_000  # [ms] total time to run the PWM signal
reps = 2
time_interval_s = 3
photom_device.laser[0].pulse_power = 10  # [%]

# %%
# Ablate the cells
# photom_device.set_position(0, [1024, 1224])  # center [y,x]
photom_device.set_position(0, [0, 0])  # edge [y,x] might not be visble
photom_device.laser[0].toggle_emission = 1
time.sleep(0.2)
photom_device.laser[0].pulse_mode = 1  # True enabled, False disabled
time.sleep(0.2)
frequency = 1000.0 / period_ms  # [Hz]
arduino.set_pwm(duty_cycle, frequency, total_duration_ms)
arduino.start_timelapse(repetitions=reps, time_interval_s=time_interval_s)
# %%
photom_device.laser[0].pulse_mode = 0  # True enabled, False disabled
time.sleep(0.2)
photom_device.laser[0].toggle_emission = 0
time.sleep(0.2)
photom_device.laser[0].power = 5.0  # [mW]

# %%
