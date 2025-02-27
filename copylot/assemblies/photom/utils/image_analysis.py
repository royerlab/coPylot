import numpy as np
from skimage.feature import peak_local_max
from skimage import filters
from skimage.filters import gaussian


def find_objects_centroids(
    image, sigma=5, threshold_rel=0.5, min_distance=10, max_num_peaks=1
):
    """
    Calculate the centroids of blurred objects in an image.

    Parameters:
    - image: 2D numpy array, single frame from the fluorescence microscopy data.
    - sigma: Standard deviation for Gaussian filter to smooth the image.
    - threshold_rel: Relative threshold for detecting peaks. Adjust according to image contrast.
    - min_distance: The minimum distance between peaks detected.

    Returns:
    - centroids: (N, 2) array where each row is (row, column) of an object's centroid.
    """
    # Smooth the image to enhance peak detection
    smoothed_image = gaussian(image, sigma=sigma)

    # Thresholding to isolate objects
    threshold_value = filters.threshold_otsu(smoothed_image)
    # binary_image = smoothed_image > threshold_value * threshold_rel

    # Detect peaks which represent object centroids
    coordinates = peak_local_max(
        smoothed_image,
        min_distance=min_distance,
        threshold_abs=threshold_value * threshold_rel,
        num_peaks=max_num_peaks,
        exclude_border=True,
    )

    return coordinates


# TODO:this function does not support multithread in qt as it is spawned as subchild process.
def plot_centroids(image_sequence, centroids, mip=True, save_path=None):
    """
    Plot the centroids of objects on top of the image sequence.

    Parameters:
    - image_sequence: 3D numpy array, sequence of frames from the fluorescence microscopy data.
    - centroids: (N, 2) array where each row is (row, column) of an object's centroid.
    """
    import matplotlib.pyplot as plt

    if mip:
        fig = plt.figure()
        plt.imshow(np.max(image_sequence, axis=0), cmap="gray")
        for i, centroid in enumerate(centroids):
            plt.scatter(centroid[1], centroid[0], color="red")
            plt.text(centroid[1], centroid[0], str(i + 1), color="white", fontsize=8)

        if save_path is not None:
            plt.savefig(save_path)
        # plt.show()
    else:
        for frame, frame_centroids in zip(image_sequence, centroids):
            plt.figure()
            plt.imshow(frame, cmap="gray")
            plt.scatter(frame_centroids[1], frame_centroids[0], color="red")
            # plt.show()
    plt.close(fig)


def calculate_centroids(image_sequence, sigma=5, threshold_rel=0.5, min_distance=10):
    """
    Calculate the centroids of objects in a sequence of images.

    Parameters:
    - image_sequence: 3D numpy array, sequence of frames from the fluorescence microscopy data.
    - sigma: Standard deviation for Gaussian filter to smooth the image.
    - threshold_rel: Relative threshold for detecting peaks. Adjust according to image contrast.
    - min_distance: The minimum distance between peaks detected.

    Returns:
    - centroids: (N, 2) array where each row is (row, column) of an object's centroid.
    """
    centroids = []
    for frame in image_sequence:
        frame_centroids = find_objects_centroids(
            frame, sigma=sigma, threshold_rel=threshold_rel, min_distance=min_distance
        )
        centroids.append(frame_centroids)
    return np.array(centroids)
