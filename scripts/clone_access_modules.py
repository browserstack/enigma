""" Script to clone access modules from git urls specified in config.json """

import logging
import os
import shutil
import sys
import time

from git import Repo, GitCommandError

from . import helpers

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()
    ]
)


def ensure_access_modules_config(config):
    """ Validate access_modules config """
    if "access_modules" not in config:
        raise Exception(
            "Not configured properly."
            "Config is expected to have access_modules key"
        )

    if "git_urls" not in config["access_modules"]:
        raise Exception(
            "Not configured properly."
            " Config is expected to have git_urls key"
            " as an array of git repos for access modules"
        )


def remove_stale_cloned_modules():
    """
    Remove already present modules so that we can clone new ones
    This is to ensure that we are on the correct commit
    """
    for each_access_module in os.listdir('Access/access_modules'):
        helpers.remove_directory_with_contents(
            f"Access/access_modules/{each_access_module}")


def initialize_init_file():
    """
    Initialize __init__.py file in access modules root directory
    from a template. This is to ensure that the modules are loaded
    properly
    """
    shutil.copyfile(
        'Access/base_email_access/access_modules_init.py',
        "Access/access_modules/__init__.py"
    )


def get_repo_url_and_branch(formatted_git_arg):
    """ Get url and branch from formatted git url string """
    url = formatted_git_arg
    target_branch = None
    if "#" in url:
        target_branch = url.split("#")[1]
        url = url.split("#")[0]
    return url, target_branch


def clone_repo(formatted_git_arg, retry_limit):
    """ Clone a single repo """
    url, target_branch = get_repo_url_and_branch(formatted_git_arg)

    folder_name = url.split("/").pop()[:-4]
    target_folder_path = "./Access/access_modules/" + folder_name

    retry_exception = None
    for clone_attempt in range(1, retry_limit + 1):
        try:
            logger.info("Cloning Repo")
            if target_branch:
                Repo.clone_from(url, target_folder_path, branch=target_branch)
            else:
                Repo.clone_from(url, target_folder_path)
        except (GitCommandError, Exception) as exception:
            sleep_time = 10 * clone_attempt
            logger.error(
                "Error while cloning repo. Error %s.",
                exception,
            )
            logger.info(
                "Retrying cloning: %s/%s. Backoff sleep %s",
                clone_attempt,
                retry_limit,
                sleep_time,
            )
            retry_exception = exception
            time.sleep(sleep_time)
        else:
            retry_exception = None
            break

    if retry_exception is not None:
        logger.exception("Max retry count reached while cloning repo")
        raise retry_exception

    return target_folder_path


def move_modules_from_cloned_repo(cloned_path):
    """
    Move access modules from the cloned folder to proper structure
    """
    for each_path in os.listdir(cloned_path):
        blacklist_paths = [
            ".git",
            ".github",
            "secrets",
            "docs",
        ]
        if (
            os.path.isdir(cloned_path + "/" + each_path)
            and each_path not in blacklist_paths
        ):
            try:
                os.rename(
                    cloned_path + "/" + each_path,
                    "./Access/access_modules/" + each_path
                )
            except Exception as exception:
                logger.exception(
                    "Failed to move access module to proper structure %s",
                    exception
                )
                raise Exception(
                    f"Failed to move access module to proper structure {exception}") from exception


def ensure_access_modules_requirements(
        cloned_path, core_requirements_file_path):
    """ Consolidate requirements from multiple access modules """
    for each_path in os.listdir(cloned_path):
        if each_path == "requirements.txt":
            current_requirements_file = cloned_path + "/" + each_path

            all_requirements = helpers.read_content_from_file(
                current_requirements_file)
            all_requirements.extend(
                helpers.read_content_from_file(core_requirements_file_path))

            # Ensure requirements are unique
            merged_requirements = list(set(all_requirements))

            # Update the requirements.txt
            helpers.write_content_to_file(
                core_requirements_file_path, sorted(merged_requirements))


def clone_access_modules():
    """ Core function to clone access modules repo """
    config = helpers.read_json_from_file("./config.json")
    ensure_access_modules_config(config)

    retry_limit = config["access_modules"].get("RETRY_LIMIT", 5)
    git_urls = config["access_modules"]["git_urls"]
    requirements_file_path = 'Access/access_modules/requirements.txt'

    helpers.ensure_folder_exists('Access/access_modules')

    remove_stale_cloned_modules()
    initialize_init_file()

    helpers.ensure_file_exists(requirements_file_path)
    # Ensure cleanup of requirements file before starting cloning process
    helpers.write_content_to_file(requirements_file_path, [])

    for formatted_git_arg in git_urls:
        cloned_path = clone_repo(formatted_git_arg, retry_limit)

        ensure_access_modules_requirements(cloned_path, requirements_file_path)
        move_modules_from_cloned_repo(cloned_path)

        logger.info("Cloning successful!")
        helpers.remove_directory_with_contents(cloned_path)


def __main__():
    logger.info("Starting cloning setup")
    try:
        clone_access_modules()
    except Exception as exception:
        logger.exception("Access module cloning failed!")
        logger.exception(exception)
        sys.exit(1)


__main__()
