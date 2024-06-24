import glob
import os
import textwrap

def display_text(text, width=79):
    """
    Wrap a given text to a specified width.
    
    Args:
        text (str): The text to wrap.
        width (int): The maximum width of each line. Defaults to 79.

    Returns:
        str: The wrapped text with lines not exceeding the specified width.
    """
    return "\n".join(textwrap.wrap(text, width))


def filenames_in_directory(directory_path):
    """
    Retrieve all filenames in the specified directory.

    Args:
        directory_path (str): The path to the directory.

    Returns:
        list: A list of filenames.
    """
    # Use glob to get all files in the directory
    files = glob.glob(os.path.join(directory_path, "*"))
    # Extract just the filenames
    filenames = [os.path.basename(file) for file in files]
    return filenames
