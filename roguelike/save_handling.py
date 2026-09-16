"""Single-slot permadeath save file, pickled to the user's home directory."""

import os
import pickle

from roguelike import constants


def save_path():
    return os.path.join(os.path.expanduser("~"), constants.SAVE_FILE_NAME)


def save_exists():
    return os.path.isfile(save_path())


def save_game(state):
    path = save_path()
    tmp_path = path + ".tmp"
    with open(tmp_path, "wb") as f:
        pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(tmp_path, path)


def load_game():
    with open(save_path(), "rb") as f:
        return pickle.load(f)


def delete_save():
    path = save_path()
    if os.path.isfile(path):
        os.remove(path)
