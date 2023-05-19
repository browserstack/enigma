""" Helper functions for scripts """
import json
import logging
import os
import shutil

logger = logging.getLogger(__name__)


def read_json_from_file(file_path):
    """ Wrapper helper to read json from file """
    return json.loads("\n".join(read_content_from_file(file_path)))


def read_content_from_file(file_path):
    """ Wrapper helper to get content from file """
    content = []
    with open(file_path, mode="r", encoding='utf-8') as read_file:
        all_lines = read_file.readlines()
        for each_line in all_lines:
            content.append(each_line.strip())
    return content


def write_content_to_file(file_path, content_lines):
    """ Wrapper helper to write lines to file """
    with open(file_path, mode='w', encoding='utf-8') as out_file:
        for each_line in content_lines:
            out_file.write(each_line)


def ensure_folder_exists(folder_path):
    """ Ensure folder path exists """
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)


def ensure_file_exists(file_path):
    """
    Ensure file path exists
    Sideeffect: creates empty file
    """
    if not os.path.exists(file_path):
        with open(
            file_path,
            mode='w',
            encoding='utf-8'
        ) as file_handle:
            file_handle.write("")


def remove_directory_with_contents(folder_path):
    """ Remove the folder along with its contents """
    if os.path.isdir(folder_path):
        logger.debug("Deleting %s", folder_path)
        try:
            shutil.rmtree(folder_path)
        except Exception as exception:
            # shutil.rmtree() sometimes throws an error on windows,
            # so we only logging the error and not raising it
            logger.exception(
                "Got Error while deleting the path %s. Error: %s",
                folder_path,
                exception
            )
