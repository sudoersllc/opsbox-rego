import os
import shutil
import subprocess
from tqdm import tqdm
import argparse
from loguru import logger
import sys


def find_projects_with_pyproject(base_dir: str) -> list:
    """Find all subdirectories containing a pyproject.toml file before hitting the first one and stop traversing subdirectories of those directories.

    Args:
        base_dir (str): The directory to start searching for projects with pyproject.toml files.

    Returns:
        A list of directories containing pyproject.toml files.
    """
    projects = []

    def traverse_directory(directory):
        for root, dirs, files in os.walk(directory):
            if "pyproject.toml" in files:
                projects.append(root)
                # Stop traversing subdirectories of this directory
                dirs.clear()
                continue

    traverse_directory(base_dir)
    return projects


def build_project(project_dir: str):
    """Run `uv build` in the specified project directory.

    Args:
        project_dir (str): The directory to run `uv build` in.
    """
    try:
        subprocess.run(
            ["uv", "build"],
            cwd=project_dir,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        print(f"Failed to build project in {project_dir}: {e.stderr.decode().strip()}")


def collect_dist_files(projects: list[str], common_dist_dir: str):
    """Copy dist files from each project into a common dist directory.

    Args:
        projects (list[str]): A list of directories containing dist files.
        common_dist_dir (str): The directory to copy dist files to.
    """
    if not os.path.exists(common_dist_dir):
        os.makedirs(common_dist_dir)

    for project in projects:
        dist_dir = os.path.join(project, "dist")
        if os.path.exists(dist_dir):
            for file_name in os.listdir(dist_dir):
                source_file = os.path.join(dist_dir, file_name)
                destination_file = os.path.join(common_dist_dir, file_name)

                # Avoid copying the same file to itself
                if os.path.abspath(source_file) != os.path.abspath(destination_file):
                    shutil.copy2(source_file, destination_file)  # Overwrites if exists


def clean_dist_files(projects: list[str], common_dist_dir: str):
    """Clean dist. files and folders from subdir dist directories.

    Args:
        projects (list[str]): A list of directories containing dist files.
        common_dist_dir (str): The directory to clean dist files from.
    """
    for project in projects:
        dist_dir = os.path.join(project, "dist")
        if os.path.exists(dist_dir):
            shutil.rmtree(dist_dir, ignore_errors=True)

    if os.path.exists(common_dist_dir):
        shutil.rmtree(common_dist_dir, ignore_errors=True)


def add_args():
    """Add arguments to the argument parser."""
    parser = argparse.ArgumentParser(
        description="Build projects and collect dist files."
    )
    parser.add_argument(
        "--build-dir",
        type=str,
        default=os.getcwd(),
        help="The directory to look for projects to build.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean the dist directory before collecting dist files.",
    )
    parser.add_argument(
        "--dist-dir",
        type=str,
        default=os.path.join(os.getcwd(), "dist"),
        help="The directory to collect dist files in.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )
    return parser


def main():
    # setup logger
    logger.remove()
    args = add_args().parse_args()  # Parse arguments

    if args.verbose:
        logger.add(
            sink=sys.stdout,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            level="DEBUG",
        )
    else:
        logger.add(
            sink=sys.stdout,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            level="INFO",
        )

    # Set the base directory and common dist directory
    base_dir = args.build_dir
    common_dist_dir = args.dist_dir

    logger.debug(f"Base directory: {base_dir}")
    logger.debug(f"Common dist directory: {common_dist_dir}")

    # Gather subdirectories of the base directory
    subdirs = [
        os.path.join(base_dir, name)
        for name in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, name))
    ]

    # Find projects with pyproject.toml in subdirectories
    projects = []
    for subdir in subdirs:
        logger.debug(f"Finding projects with pyproject.toml in {subdir}")
        items = find_projects_with_pyproject(subdir)
        logger.info(f"Found {len(items)} projects with pyproject.toml in {subdir}")
        projects.extend(items)

    if len(projects) == 0:
        logger.critical(f"No projects with pyproject.toml found in {base_dir}")
        return

    # Clean dist files before collecting
    if args.clean:
        logger.info("Cleaning dist files...")
        clean_dist_files(projects, common_dist_dir)

    # Build projects and collect dist files
    logger.info("Starting build process...")
    for project in tqdm(projects, desc="Building Project", unit="project"):
        build_project(project)

    logger.info("Collecting dist files...")
    collect_dist_files(projects, common_dist_dir)

    logger.success(f"All dist files collected in {common_dist_dir}")


if __name__ == "__main__":
    main()
