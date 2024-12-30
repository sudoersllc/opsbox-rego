import os
import shutil
import subprocess
from tqdm import tqdm

def find_projects_with_pyproject(base_dir):
    """Find all subdirectories containing a pyproject.toml file before hitting the first one and stop traversing subdirectories of those directories."""
    projects = []
    def traverse_directory(directory):
        flip = False
        for root, dirs, files in os.walk(directory):
            if 'pyproject.toml' in files and flip is True:
                projects.append(root)
                # Stop traversing subdirectories of this directory
                dirs.clear()
                continue
            elif 'pyproject.toml' in files:
                flip = True
                continue

    traverse_directory(base_dir)
    print(f"Found {len(projects)} projects with pyproject.toml")
    return projects

def build_project(project_dir):
    """Run `python -m build` in the specified project directory."""
    try:
        subprocess.run(
            ["uv", "build"], cwd=project_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        print(f"Failed to build project in {project_dir}: {e.stderr.decode().strip()}")

def collect_dist_files(projects, common_dist_dir):
    """Copy dist files from each project into a common dist directory."""
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

def main():
    base_dir = os.getcwd()
    common_dist_dir = os.path.join(base_dir, "dist")

    print("Finding projects with pyproject.toml...")
    projects = find_projects_with_pyproject(base_dir)

    if not projects:
        print("No projects with pyproject.toml found.")
        return

    print("Building project...")
    for project in tqdm(projects, desc="Building project", unit="project"):
        build_project(project)

    print("Collecting dist files...")
    collect_dist_files(projects, common_dist_dir)

    print(f"All dist files collected in {common_dist_dir}")

if __name__ == "__main__":
    main()
