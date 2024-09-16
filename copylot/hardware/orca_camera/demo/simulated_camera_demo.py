from copylot.hardware.orca_camera.simulated_camera import SimulatedOrcaCamera


if __name__ == '__main__':
    visualize = True
    camera = SimulatedOrcaCamera()
    stack = camera.run(100)

    if visualize:
        import napari

        viewer = napari.Viewer()
        viewer.add_image(stack, name="stack")

        napari.run()
