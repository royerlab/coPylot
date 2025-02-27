# %%
import numpy as np
from scipy.ndimage import median_filter
from skimage.feature import peak_local_max
import napari
from skimage import measure, filters
from skimage.filters import gaussian
import os
from skimage.morphology import remove_small_objects


# %%
os.environ["DISPLAY"] = ":1002"
viewer = napari.Viewer()

# %%


def find_objects_centroids(
    image, sigma=5, threshold_rel=0.5, min_distance=10, min_area=3
):
    """
    Calculate the centroids of blurred objects in an image, excluding hot pixels or small artifacts.

    Parameters:
    - image: 2D numpy array, single frame from the fluorescence microscopy data.
    - sigma: Standard deviation for Gaussian filter to smooth the image.
    - threshold_rel: Relative threshold for detecting peaks. Adjust according to image contrast.
    - min_distance: The minimum distance between peaks detected.
    - min_area: The minimum area of an object to be considered valid.

    Returns:
    - centroids: (N, 2) array where each row is (row, column) of an object's centroid.
    """
    # Smooth the image to enhance peak detection
    smoothed_image = gaussian(image, sigma=sigma)

    # Thresholding to isolate objects
    threshold_value = filters.threshold_otsu(smoothed_image)
    binary_image = smoothed_image > threshold_value * threshold_rel

    # Remove small objects (hot pixels or small artifacts) from the binary image
    cleaned_image = remove_small_objects(binary_image, min_size=min_area)

    # Label the cleaned image to identify distinct objects
    label_image = measure.label(cleaned_image)
    properties = measure.regionprops(label_image)

    # Calculate centroids of filtered objects
    centroids = [prop.centroid for prop in properties if prop.area >= min_area]

    return np.array(centroids)


# %%
# Define the rectangle and grid parameters
n_points = 5  # Number of points per row/column in the grid
rect_start_x, rect_start_y = 20, 20
rect_end_x, rect_end_y = 80, 80
frame_width, frame_height = 100, 100
n_frames = 25  # Total number of frames
px = 4  # Size of the point in the grid
# Calculate intervals between points in the grid
interval_x = (rect_end_x - rect_start_x) // (n_points - 1)
interval_y = (rect_end_y - rect_start_y) // (n_points - 1)

# Initialize frames
frames = np.zeros((n_frames, frame_width, frame_height), dtype=np.float32)
# Store the coordinates of the grid points per frame
center_coords = np.zeros((n_frames, 2), dtype=np.float32)

# Populate frames with the grid points
for i in range(n_points):
    for j in range(n_points):
        frame_index = i * n_points + j
        x = rect_start_x + j * interval_x
        y = rect_start_y + i * interval_y
        center_coords[frame_index] = [y, x]
        # center_coords[frame_index, i, j] = [x, y]
        frames[
            frame_index, y - px // 2 : y + px // 2, x - px // 2 : x + px // 2
        ] = 100  # Set the point to white

for i in range(frames.shape[0]):
    frames[i] = gaussian(frames[i], sigma=4)

viewer.add_image(frames)

print(center_coords)
# %%
centroids = []
for i in range(frames.shape[0]):
    coords = find_objects_centroids(
        frames[i], sigma=3, threshold_rel=0.5, min_distance=10
    )
    centroids.append([i, np.round(coords[0][0]), np.round(coords[0][1])])

centroids = np.array(centroids)
viewer.add_points(centroids, size=5, face_color="red")
print(centroids)

# %%
# compare with the ground truth
assert np.allclose(centroids[:, 1:], center_coords, atol=1)

# %%
