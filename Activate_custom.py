# ----------------------------------------------------------------------
# |
# |  Activate_custom.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2022-10-14 12:38:51
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2022
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
# pylint: disable=missing-module-docstring

import sys

from pathlib import Path
from typing import List, Optional

from Common_Foundation import PathEx                                        # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation.Shell import Commands                                # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation.Shell.All import CurrentShell                        # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation.Streams.DoneManager import DoneManager               # type: ignore  # pylint: disable=import-error,unused-import

from RepositoryBootstrap import Configuration                               # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap import Constants                                   # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap import DataTypes                                   # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap.ActivateActivity import ActivateActivity           # type: ignore  # pylint: disable=import-error,unused-import


# ----------------------------------------------------------------------
from _install_data import GRCOV_VERSIONS, LLVM_VERSIONS
del sys.modules["_install_data"]


# ----------------------------------------------------------------------
def GetCustomActions(                                                       # pylint: disable=too-many-arguments
    # Note that it is safe to remove any parameters that are not used
    dm: DoneManager,
    repositories: List[DataTypes.ConfiguredRepoDataWithPath],               # pylint: disable=unused-argument
    generated_dir: Path,                                                    # pylint: disable=unused-argument
    configuration: Optional[str],
    version_specs: Configuration.VersionSpecs,
    force: bool,                                                            # pylint: disable=unused-argument
    is_mixin_repo: bool,                                                    # pylint: disable=unused-argument
) -> List[Commands.Command]:
    assert configuration

    this_root = Path(__file__).parent
    assert this_root.is_dir(), this_root

    tools_dir = this_root / Constants.TOOLS_SUBDIR
    assert tools_dir.is_dir(), tools_dir

    # Validate the dynamically installed content
    dm.WriteLine("")

    with dm.Nested("Validating 'grcov'...") as grcov_dm:
        _, grcov_version = ActivateActivity.GetVersionedDirectoryEx(
            tools_dir / "grcov",
            version_specs.tools,
        )

        install_data_key = str(grcov_version)

        install_data = GRCOV_VERSIONS.get(install_data_key, None)
        assert install_data is not None

        install_data.installer.ShouldInstall(None, lambda reason: grcov_dm.WriteError(reason))


    with dm.Nested("Validating 'LLVM'...") as llvm_dm:
        llvm_tool_dir, llvm_version = ActivateActivity.GetVersionedDirectoryEx(
            tools_dir / "LLVM",
            version_specs.tools,
        )

        install_data_items_key = str(llvm_version)

        install_data_items = LLVM_VERSIONS.get(install_data_items_key, None)
        assert install_data_items is not None

        validated = False

        for install_data_item in install_data_items:
            if install_data_item.name in configuration or len(install_data_items) == 1:
                install_data_item.installer.ShouldInstall(None, lambda reason: llvm_dm.WriteError(reason))

                validated = True
                break

        assert validated

    # Create the commands
    commands: List[Commands.Command] = []

    assert configuration

    if CurrentShell.family_name == "Windows":
        if "mingw" in configuration:
            mingw_dir = llvm_tool_dir / "mingw"

            for child in mingw_dir.iterdir():
                if child.is_dir():
                    mingw_dir = child
                    break

            assert mingw_dir.is_dir(), mingw_dir

            # Calculate the shared lib dir
            shared_lib_dir = mingw_dir / "x86_64-w64-mingw32" / "bin"

            commands += [
                Commands.AugmentPath.Create(
                    [
                        str(PathEx.EnsureDir(mingw_dir / "bin")),
                        str(PathEx.EnsureDir(shared_lib_dir)),
                    ],
                ),
            ]

        elif "msvc" in configuration:
            commands.append(Commands.AugmentPath.Create(str(PathEx.EnsureDir(llvm_tool_dir / "msvc" / "bin"))))

        else:
            assert False, configuration  # pragma: no cover

    else:
        commands += [
            Commands.AugmentPath.Create(str(PathEx.EnsureDir(llvm_tool_dir / "bin"))),
            Commands.Augment("LD_LIBRARY_PATH", str(PathEx.EnsureDir(llvm_tool_dir / "lib" / "x86_64-unknown-linux-gnu"))),
        ]

    return commands


# ----------------------------------------------------------------------
# Note that it is safe to remove this function if it will never be used.
def GetCustomActionsEpilogue(                                               # pylint: disable=too-many-arguments
    # Note that it is safe to remove any parameters that are not used
    dm: DoneManager,                                                        # pylint: disable=unused-argument
    repositories: List[DataTypes.ConfiguredRepoDataWithPath],               # pylint: disable=unused-argument
    generated_dir: Path,                                                    # pylint: disable=unused-argument
    configuration: Optional[str],                                           # pylint: disable=unused-argument
    version_specs: Configuration.VersionSpecs,                              # pylint: disable=unused-argument
    force: bool,                                                            # pylint: disable=unused-argument
    is_mixin_repo: bool,                                                    # pylint: disable=unused-argument
) -> List[Commands.Command]:
    """\
    Returns a list of actions that should be invoked as part of the activation process. Note
    that this is called after `GetCustomActions` has been called for each repository in the dependency
    list.

    ********************************************************************************************
    Note that it is very rare to have the need to implement this method. In most cases, it is
    safe to delete the entire method. However, keeping the default implementation (that
    essentially does nothing) is not a problem.
    ********************************************************************************************
    """

    return []
