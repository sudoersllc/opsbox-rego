import argparse
import os
from pathlib import Path
from itertools import chain
import shutil
import subprocess
import sys
import pathspec
from rich.console import Console
from rich.progress import Progress
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from io import StringIO

# Create a console object to use for logging and measuring the size of the main panel.
console = Console()

screen = True

class ProjectDiscoverer:
    def __init__(self, root_directory: str | Path, layout: Layout, only_subdirs: bool = True):
        """Initialize the ProjectDiscoverer object.
        
        Args:
            root_directory (str | Path): The root directory to search for projects in.
            layout (Layout): The layout object to use for updating the screen.
            only_subdirs (bool): Whether to only search subdirectories for projects. Defaults to True.
        """
        self.root_directory = Path(root_directory)
        self.only_subdirs = only_subdirs
        self.spec = self.load_gitignore()
        self.layout = layout

    def find_projects(self) -> list[Path]:
        """Find all projects in the root directory and return a list of their paths.

        Returns:
            list[Path]: A list of paths to the projects.
        """
        self.layout["header"].update(
            Panel("Finding projects...", title="[bold blue]Project Discovery[/]", border_style="blue")
        )
        subdirs = []
        buffer = StringIO()

        # glob for all subdirectories or just the root directory
        if self.only_subdirs:
            glob = self.root_directory.glob('**/*/pyproject.toml')
        else:
            glob = self.root_directory.glob('**/pyproject.toml')

        with Live(self.layout, refresh_per_second=4, screen=screen):
            for path in glob:
                subdirs.append(path)
                buffer.write(f"{str(path)}\n")
                self.layout["main"].update(
                    Panel(buffer.getvalue(), title="[bold green]Projects Found[/]", border_style="green")
                )

        # filter out ignored subdirectories
        subdirs = [path for path in subdirs if not self.spec.match_file(str(path))]
        subdirs = [path.parent for path in subdirs]
        return subdirs

    def load_gitignore(self, gitignore_path: str = '.gitignore') -> pathspec.PathSpec:
        """Load the .gitignore file and return a PathSpec object.
        
        Args:
            gitignore_path (str): The path to the .gitignore file. Defaults to '.gitignore'.
            
        Returns:
            PathSpec: A PathSpec object that can be used to match files.
        """
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r') as f:
                # This creates a PathSpec from the lines in the file.
                spec = pathspec.PathSpec.from_lines('gitwildmatch', f)
        else:
            spec = pathspec.PathSpec.from_lines('gitwildmatch', [])
        return spec
    
class ProjectBuilder:
    def __init__(self, project_paths: list[Path], layout: Layout):
        self.project_paths = project_paths
        self.layout = layout
        self._check_uv_exists()

    def _check_uv_exists(self):
        """Check if uv is installed on the system."""
        if not shutil.which('uv'):
            # Print a nice message to the console and exit if uv is not installed.
            self.layout["main"].update(
                Panel("uv is not installed. Please install it.", title="[red]Error[/red]", border_style="red")
            )
            sys.exit(1)
        else:
            self.layout["main"].update(
                Panel("uv is installed.", title="[green]Success[/green]", border_style="green")
            )

    def _move_dists(self, destination: str | Path):
        """Move the dist files to the destination directory.

        Args:
            destination (str | Path): The path to the destination directory.
        """
        projects = self.project_paths

        # Setup progress bar panel
        progress_bar = Progress()
        progress_panel = Panel(progress_bar, title="[bold cyan]Progress[/bold cyan]", border_style="cyan")
        self.layout["header"].update(progress_panel)

        # Setup main panel for moving files
        self.layout["main"].update(
            Panel("Copying dist files...", title="[bold magenta]Copying Dist Files[/]", border_style="magenta")
        )

        # Setup dist paths
        dists = list(chain.from_iterable([list(project.glob('dist/*')) for project in projects]))
        dists = [dist for dist in dists if '.git' not in str(dist)]

        # Move dist files
        with Live(self.layout, refresh_per_second=4, screen=screen):
            out_lines = []
            task = progress_bar.add_task("[cyan]Copying dist files...", total=len(dists))
            for dist in dists:
                destination_path = Path(destination) / dist.name
                if destination_path.exists():
                    destination_path.unlink()  # Remove the existing file
                shutil.move(dist, destination_path)

                # Update output lines and main panel
                out_lines.insert(0, f"[green]>[/green] Copied {dist} to {destination_path}\n")
                self.layout["main"].update(
                    Panel("".join(out_lines), title="[bold green]Copying Dist Files[/]", border_style="green")
                )
                progress_bar.update(task, advance=1)
                out_lines[0] = out_lines[0].replace("[green]>[/green]", "")
                out_lines[0] = f"[dim]{out_lines[0]}[/dim]"

    def _clean_dists(self, destination: str | Path):
        """Clean the dist files in the projects and the destination directory.
        
        Args:
            destination (str | Path): The path to the destination directory.
        """
        projects = self.project_paths

        # Setup dist paths for cleaning
        dists = list(chain.from_iterable([list(project.glob('dist/*')) for project in projects]))
        dists = dists + list(Path(destination).glob('*'))
        dists = [dist for dist in dists if '.git' not in str(dist)]

        # Setup progress bar panel
        progress_bar = Progress()
        progress_panel = Panel(progress_bar, title="[bold cyan]Progress[/bold cyan]", border_style="cyan")
        self.layout["header"].update(progress_panel)

        # Setup main panel for cleaning dists
        self.layout["main"].update(
            Panel("Cleaning dist files...", title="[bold red]Cleaning Dist Files[/]", border_style="red")
        )

        # Clean dist files
        with Live(self.layout, refresh_per_second=4, screen=screen):
            out_lines = []
            task = progress_bar.add_task("[cyan]Cleaning dist files...", total=len(dists))
            for dist in dists:
                try:
                    if dist.is_dir():
                        shutil.rmtree(dist)
                    else:
                        dist.unlink()
                except Exception as e:
                    out_lines.insert(0, f"[red]> Failed to remove {dist}: {e}[/red]\n")
                    self.layout["main"].update(
                        Panel("".join(out_lines), title="[red]Failed to Clean Dist Files[/red]", border_style="red")
                    )
                    self.layout["header"].update(
                        Panel("Failed to clean dist files", title="[red]Major Error[/red]", border_style="red")
                    )
                    sys.exit(1)
                out_lines.insert(0, f"[green]>[/green] Removed {dist}\n")
                self.layout["main"].update(
                    Panel("".join(out_lines), title="[bold red]Cleaning Dist Files[/]", border_style="red")
                )
                progress_bar.update(task, advance=1)
                out_lines[0] = out_lines[0].replace("[green]>[/green]", "")
                out_lines[0] = f"[dim]{out_lines[0]}[/dim]"

    def _clean_venvs(self):
        """Clean the virtual environments in the projects."""
        projects = self.project_paths

        # Setup paths for virtual environments
        venvs = list(chain.from_iterable([list(project.glob('.venv')) for project in projects]))

        # Setup progress bar panel
        progress_bar = Progress()
        progress_panel = Panel(progress_bar, title="[bold cyan]Progress[/bold cyan]", border_style="cyan")
        self.layout["header"].update(progress_panel)

        # Setup main panel for cleaning venvs
        self.layout["main"].update(
            Panel("Cleaning venv files...", title="[bold red]Cleaning Virtual Environments[/]", border_style="red")
        )

        # Clean venv files
        with Live(self.layout, refresh_per_second=4, screen=screen):
            out_lines = []
            task = progress_bar.add_task("[cyan]Cleaning venv files...", total=len(venvs))
            for venv in venvs:
                try:
                    shutil.rmtree(venv)
                except Exception as e:
                    out_lines.insert(0, f"[red]> Failed to remove {venv}: {e}[/red]\n")
                    self.layout["main"].update(
                        Panel("".join(out_lines), title="[red]Failed to Clean Virtual Environments[/red]", border_style="red")
                    )
                    self.layout["header"].update(
                        Panel("Failed to clean venv files", title="[red]Major Error[/red]", border_style="red")
                    )
                    sys.exit(1)
                out_lines.insert(0, f"[green]>[/green] Removed {venv}\n")
                self.layout["main"].update(
                    Panel("".join(out_lines), title="[bold red]Cleaning Virtual Environments[/]", border_style="red")
                )
                progress_bar.update(task, advance=1)
                out_lines[0] = out_lines[0].replace("[green]>[/green]", "")
                out_lines[0] = f"[dim]{out_lines[0]}[/dim]"

    def _proccess_build(self):
        """Build the projects and update the progress bar and main panel."""
        projects = self.project_paths

        # Setup progress bar panel
        progress_bar = Progress()
        progress_panel = Panel(progress_bar, title="[bold cyan]Progress[/bold cyan]", border_style="cyan")

        # Build projects
        with Live(self.layout, refresh_per_second=4, screen=screen):
            task = progress_bar.add_task("[cyan]Building projects...", total=len(projects))
            for project in projects:
                self.layout["header"].update(progress_panel)
                process = subprocess.Popen(
                    ["uv", "build"],
                    cwd=project,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                    
                output_lines = []
                while True:
                    line = process.stderr.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        output_lines.insert(0, line)
                        # Add a green marker to the current line.
                        output_lines[0] = f"[green]>[/green] {output_lines[0]}"
                        self.layout["main"].update(
                            Panel("".join(output_lines), title=f"Build Output for [yellow]{project}[/yellow]", border_style="yellow")
                        )

                        # Update the line to a dim style for previous messages.
                        output_lines[0] = output_lines[0].replace("[green]>[/green]", "")
                        output_lines[0] = f"[dim]{output_lines[0]}[/dim]"

                if process.returncode != 0:
                    err_msg = process.stderr.read()
                    self.layout["header"].update(
                        Panel("Build failure!", title="[red]Major Error[/red]", border_style="red")
                    )
                    self.layout["main"].update(
                        Panel(f"Build failed: {err_msg.strip()}", title=f"[red]Build Failure for[/red] [yellow]{project}[/yellow]", border_style="red")
                    )
                    sys.exit(process.returncode)
            
                progress_bar.update(task, advance=1)

    def build(self, dist_dir: str = './dist', clean: bool = True):
        """Build the projects and move the dist files to the target directory.

        Args:
            dist_dir (str): The directory to move the dist files to. Defaults to './dist'.
            clean (bool): Whether to clean the dist directory before collecting dist files. Defaults to True.
        """
        # Clean dist files and virtual environments if requested.
        if clean:
            self._clean_dists(dist_dir)
            self._clean_venvs()

        # Build projects
        self._proccess_build()

        # Move built dist files to the target directory.
        self._move_dists(dist_dir)
        
def add_args():
    """Add arguments to the argument parser."""
    parser = argparse.ArgumentParser(
        description="Build projects and collect dist files."
    )
    parser.add_argument(
        "--scan-dir",
        type=str,
        default=os.getcwd(),
        help="The directory to look for projects to build.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        default=False,
        help="Clean the dist directory before collecting dist files.",
    )
    parser.add_argument(
        "--dist-dir",
        type=str,
        default=os.path.join(os.getcwd(), "dist"),
        help="The directory to collect dist files in.",
    )
    parser.add_argument(
        "--no-screen",
        action="store_true",
        help="Disable screen mode for the progress bars.",
    )
    return parser

def main():
    # Setup console and layout.
    layout = Layout()
    layout.split(
        Layout(name="header", size=3),
        Layout(name="main"),
    )

    args = add_args().parse_args()  # Parse arguments
    global screen # Use the global screen variable
    screen = not args.no_screen # Set the screen variable to the opposite of the no-screen argument.

    # Discover projects.
    pd = ProjectDiscoverer(args.scan_dir, layout, (True if args.scan_dir != os.getcwd() else False))
    projects = pd.find_projects()

    # Build projects.
    builder = ProjectBuilder(projects, layout)
    builder.build(args.dist_dir, args.clean)

if __name__ == '__main__':
    main()
