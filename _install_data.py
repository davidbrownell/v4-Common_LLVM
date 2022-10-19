# ----------------------------------------------------------------------
# |
# |  _install_data.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2022-10-17 07:25:29
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2022
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains data used during setup and activation"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from Common_Foundation.Shell.All import CurrentShell                        # type: ignore  # pylint: disable=import-error,unused-import

from RepositoryBootstrap import Constants                                   # type: ignore  # pylint: disable=import-error,unused-import

from RepositoryBootstrap.SetupAndActivate.Installers.DownloadNSISInstaller import DownloadNSISInstaller             # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap.SetupAndActivate.Installers.DownloadSevenZipInstaller import DownloadSevenZipInstaller     # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap.SetupAndActivate.Installers.DownloadZipInstaller import DownloadZipInstaller               # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap.SetupAndActivate.Installers.Installer import Installer                                     # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap.SetupAndActivate.Installers.LocalSevenZipInstaller import LocalSevenZipInstaller           # type: ignore  # pylint: disable=import-error,unused-import


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class InstallData(object):
    name: str
    installer: Installer
    prompt_for_interactive: bool            = field(kw_only=True)


# ----------------------------------------------------------------------
_root_dir                                   = Path(__file__).parent


# ----------------------------------------------------------------------
GRCOV_VERSIONS: Dict[str, InstallData]      = {
    "0.8.12": InstallData(
        "standard",
        LocalSevenZipInstaller(
            _root_dir / Constants.TOOLS_SUBDIR / "grcov" / "v0.8.12" / CurrentShell.family_name / "install.7z",
            _root_dir / Constants.TOOLS_SUBDIR / "grcov" / "v0.8.12" / CurrentShell.family_name,
            "0.8.12",
        ),
        prompt_for_interactive=False,
    ),
}


# ----------------------------------------------------------------------
LLVM_VERSIONS: Dict[str, List[InstallData]] = {}

if CurrentShell.family_name == "Windows":
    # ----------------------------------------------------------------------
    def AugmentInstaller(
        installer: Installer,
        output_dir_suffix: str,
    ) -> Installer:
        installer.output_dir /= output_dir_suffix
        return installer

    # ----------------------------------------------------------------------

    LLVM_VERSIONS["15.0.2"] = [
        InstallData(
            "mingw",
            AugmentInstaller(
                DownloadZipInstaller(
                    "https://github.com/mstorsjo/llvm-mingw/releases/download/20220906/llvm-mingw-20220906-ucrt-x86_64.zip",
                    "06c8523447a369303f7a67dda1d2b66a6b2e460640126458f69f1d98afd3fdf1",
                    _root_dir / Constants.TOOLS_SUBDIR / "LLVM" / "v15.0.2" / CurrentShell.family_name / "x64",
                    "20220906",
                ),
                "mingw",
            ),
            prompt_for_interactive=False,
        ),
        InstallData(
            "msvc",
            AugmentInstaller(
                DownloadNSISInstaller(
                    "https://github.com/llvm/llvm-project/releases/download/llvmorg-15.0.2/LLVM-15.0.2-win64.exe",
                    "50d24a9e8cb6767ad5c3eb21422a3ffa8f4a2d797120e8d5be41dd0c88c0d63a",
                    _root_dir / Constants.TOOLS_SUBDIR / "LLVM" / "v15.0.2" / CurrentShell.family_name / "x64",
                    "15.0.2",
                ),
                "msvc",
            ),
            prompt_for_interactive=True,
        ),
    ]

    del AugmentInstaller

else:
    LLVM_VERSIONS["15.0.2"] = [
        InstallData(
            "standard",
            DownloadSevenZipInstaller(
                "https://github.com/davidbrownell/v4-Common_LLVM/releases/download/v15.0.2-alpha.4/install.7z", # TODO
                "f4728ace762ff628df9baa9d67dbf256f3331059f15eea05385b556ac9da6cc7",
                _root_dir / Constants.TOOLS_SUBDIR / "LLVM" / "v15.0.2" / CurrentShell.family_name / "x64",
                "alpha-4",
            ),
            prompt_for_interactive=False,
        ),
    ]
