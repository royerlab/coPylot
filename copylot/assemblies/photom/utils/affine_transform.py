from collections.abc import Iterable
from warnings import warn

from skimage import transform
import numpy as np
from copylot.assemblies.photom.utils.io import yaml_to_model, model_to_yaml
from copylot.assemblies.photom.utils.settings import AffineTransformationSettings
from pathlib import Path


class AffineTransform:
    """
    A class object for handling affine transformation.
    """

    def __init__(self, tx_matrix: np.array = None, config_file: Path = None):
        """
        Initialize the affine transformation object.
        :param tx_matrix: affine transformation matrix
        """
        self.T_affine = tx_matrix
        self.config_file = config_file

        if self.T_affine is None:
            self.reset_T_affine()
        else:
            tx_matrix = np.array(tx_matrix)
            assert tx_matrix.shape == (3, 3)
            self.T_affine = tx_matrix

        if self.config_file is None:
            self.config_file = Path("./affine_transform.yml")
            self.make_config()
        else:
            settings = yaml_to_model(self.config_file, AffineTransformationSettings)
            self.T_affine = np.array(settings.affine_transform_yx)

    def make_config(self, config_file="./affine_transform.yml"):
        if not Path(self.config_file).exists():
            i = 1
            # Generate the first filename
            filename = Path(self.config_file)
            # While a file with the current filename exists, increment the number
            while Path(filename).exists():
                i += 1
                self.config_file = f"{filename.parent}_{i}{filename.suffix}"
            self.config_file.mkdir(parents=True, exist_ok=True)
            # Make model and save to file
            model = AffineTransformationSettings(
                affine_transform_yx=self.T_affine.tolist()
            )
            model_to_yaml(model, self.config_file)

        # # Load the config file
        # settings = yaml_to_model(self.config_file, AffineTransformationSettings)
        # self.T_affine = np.array(settings.affine_transform_yx)

    def reset_T_affine(self):
        """
        Reset affine matrix to identity matrix.
        """
        self.T_affine = np.eye(3)

    def compute_affine_matrix(self, origin, dest):
        """
        Compute affine matrix from 2 origin & 2 destination coordinates.
        :param origin: 3 sets of coordinate of origin e.g. [(x1, y1), (x2, y2), (x3, y3)]
        :param dest: 3 sets of coordinate of destination e.g. [(x1, y1), (x2, y2), (x3, y3)]
        :return: affine matrix
        """
        if not (isinstance(origin, Iterable) and len(origin) >= 3):
            raise ValueError("origin needs 3 coordinates.")
        if not (isinstance(dest, Iterable) and len(dest) >= 3):
            raise ValueError("dest needs 3 coordinates.")
        self.T_affine = transform.estimate_transform(
            "affine", np.float32(origin), np.float32(dest)
        ).params
        return self.T_affine

    def get_affine_matrix(self):
        """
        Get the current affine matrix.
        :return: affine matrix
        """
        return self.T_affine

    def set_affine_matrix(self, matrix: np.array):
        assert matrix.shape == (3, 3)
        self.T_affine = matrix

    def apply_affine(self, coord_list: list) -> list:
        """
        Perform affine transformation.
        :param coord_list: a list of origin coordinate (e.g. [[x,y], ...] or [[list for ch0], [list for ch1]])
        :return: destination coordinate
        """
        coord_array = np.stack(coord_list, axis=0)
        if len(coord_list) <= 2:
            coord_array = coord_array.reshape(2, -1)
        else:
            coord_array = coord_array.T
        if self.T_affine is None:
            warn(
                "Affine matrix has not been determined yet. \ncoord_list is returned without transformation."
            )
            dest_list = coord_array
        else:
            coord_array = np.vstack((coord_array, np.ones((1, coord_array.shape[1]))))
            dest_list = self.T_affine @ coord_array
        return [list(i) for i in dest_list]

    # will be used for non numpy & opencv version
    def trans_pointwise(self, coord_list):
        """
        Convert coordinate list from channel wise to point wise.
        (e.g. [[1, 2, 4, .... <ch0>], [4, 2, 5, ... <ch1>] to [[1, 4], [2, 2], ...])
        :param coord_list: coordinate list in channel wise
        :return: coordinate list in point wise
        """
        return list(map(lambda x, y: [x, y], coord_list[0], coord_list[1]))

    # will be used for non numpy & opencv version
    def trans_chwise(self, coord_list):
        """
        Convert coordinate list from channel wise to point wise.
        (e.g. [[1, 4], [2, 2], ...] to [[1, 2, 4, .... <ch0>], [4, 2, 5, ... <ch1>])
        :param coord_list: coordinate list in point wise
        :return: coordinate list in channel wise
        """
        chwise1 = list(map(lambda x: x[0], coord_list))
        chwise2 = list(map(lambda x: x[1], coord_list))
        return [chwise1, chwise2]

    def save_matrix(self, matrix: np.array = None, config_file: Path = None) -> None:
        """
        Save affine matrix to a YAML file.

        Parameters
        ----------
        matrix :np.array, optional
            3x3 affine_transformation, by default None will save the current matrix
        config_file : str, optional
            path to the YAML file, by default None will save to the current config_file.
            This updates the config_file attribute.
        Raises
        ------
        ValueError
            matrix is not defined
        """

        if matrix is None:
            if self.T_affine is None:
                raise ValueError("provided matrix is not defined")
            else:
                matrix = self.T_affine
        else:
            matrix = np.array(matrix)
            assert matrix.shape == (3, 3)

        if config_file is not None:
            self.config_file = config_file

        model = AffineTransformationSettings(
            affine_transform_yx=matrix.tolist(),
        )
        model_to_yaml(model, self.config_file)

    def load_matrix(self, config_file: Path = None) -> None:
        """
        Load affine matrix from a YAML file.

        Parameters
        ----------
        config_file : str, optional
            path to the YAML file, by default None will load the current config_file.
            This updates the config_file attribute.
        """
        if config_file is not None:
            self.config_file = config_file

        settings = yaml_to_model(self.config_file, AffineTransformationSettings)
        self.T_affine = np.array(settings.affine_transform_yx)
