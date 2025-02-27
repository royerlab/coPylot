#%%
from copylot.hardware.cameras.flir.flir_camera import FlirCamera

#%%
if __name__ == '__main__':
    cam = FlirCamera()

    # open the system
    cam.open()

    # serial number
    print(cam.device_id)
    # list of cameras
    print(cam.list_available_cameras())
    #%%
    # Return 10 frames and save output arrays as .csv files (this can be changed)

    # Option 1: take multiple frames in a single acquisition
    # Can control timeout (wait_time) for grabbing images from the camera buffer
    snap1 = cam.snap(n_images=5, wait_time=1000)
    #%%
    cam.save_image(snap1)
    # Option 2: iterate over snap()
    # Saving in each iteration causes a delay between beginning/ending camera acquisition
    # Could also collect the snap2 outputs and then save outside the loop to avoid delays
    # (which is just what Option 1 does implicitly)
    for i in range(0, 5):
        snap2 = cam.snap()
        cam.save_image(snap2)

    # open again
    cam.open()

    # cam bit depth
    print('Default bit depth', cam.bitdepth)
    cam.bitdepth = 3
    assert cam.bitdepth == 3

    # cam shutter mode
    print('Default shutter mode', cam.shutter_mode)
    cam.shutter_mode = 'rolling'
    assert cam.shutter_mode == 'rolling'

    # cam binning - THERE ARE SOME SPECIFIC MULTIPLES
    print('Default binsize', cam.binning)
    cam.binning = (2, 2)
    assert cam.binning == (2, 2)

    # cam image size
    print('Default image size', cam.image_size)  # set to the max by default
    print('Limit image size', cam.image_size_limits)
    cam.image_size = (1000, 2000)
    assert cam.image_size == (1000, 2000)

    # cam gain methods
    print('Default AutoGain', cam.gain, cam.gain_limits)
    cam.gain = 0.8
    assert cam.gain == 0.8

    # cam exposure methods
    print('Default AutoExposure', cam.exposure, cam.exposure_limits)
    cam.exposure = 100.0
    assert cam.exposure == 100.0

    # cam frame rate methods
    print('Default frame rate', cam.framerate)
    # set method might be removed

    cam.close()
