import os
from pdm.core import Core
from pdm.project import Project
from pdm.signals import pre_invoke


def _add_bin_dirs_to_path(project: Project, **_: object) -> None:
    bin_dir = str(project.root / "bin")
    path = os.environ.get("PATH", "")
    if bin_dir not in path.split(":"):
        os.environ["PATH"] = f"{bin_dir}:{path}"


def plugin(core: Core) -> None:
    pre_invoke.connect(_add_bin_dirs_to_path)
