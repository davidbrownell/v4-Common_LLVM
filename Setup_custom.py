# ----------------------------------------------------------------------
# |
# |  Setup_custom.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2022-10-14 12:37:50
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

import copy
import os
import uuid
import sys
import textwrap

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from semantic_version import Version as SemVer          # pylint: disable=unused-import

from Common_Foundation.ContextlibEx import ExitStack                        # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation import PathEx                                        # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation.Shell.All import CurrentShell                        # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation.Shell import Commands                                # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation.Streams.DoneManager import DoneManager               # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation import SubprocessEx                                  # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation import TextwrapEx                                    # type: ignore  # pylint: disable=import-error,unused-import
from Common_Foundation import Types                                         # type: ignore  # pylint: disable=import-error,unused-import

from RepositoryBootstrap import Configuration                               # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap import Constants                                   # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap.SetupAndActivate.Installers.DownloadNSISInstaller import DownloadNSISInstaller             # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap.SetupAndActivate.Installers.DownloadSevenZipInstaller import DownloadSevenZipInstaller     # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap.SetupAndActivate.Installers.DownloadZipInstaller import DownloadZipInstaller               # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap.SetupAndActivate.Installers.Installer import Installer                                     # type: ignore  # pylint: disable=import-error,unused-import
from RepositoryBootstrap.SetupAndActivate.Installers.LocalSevenZipInstaller import LocalSevenZipInstaller           # type: ignore  # pylint: disable=import-error,unused-import


# ----------------------------------------------------------------------
from _install_data import GRCOV_VERSIONS, LLVM_VERSIONS
del sys.modules["_install_data"]


# ----------------------------------------------------------------------
def GetConfigurations() -> Union[
    Configuration.Configuration,
    Dict[
        str,                                # configuration name
        Configuration.Configuration,
    ],
]:
    configurations: Dict[str, Configuration.Configuration] = {}

    if CurrentShell.family_name == "Windows":
        target_architectures = ["x64", ] # TODO: "x86"
    else:
        target_architectures = [CurrentShell.current_architecture, ]

    common_foundation_dependency = Configuration.Dependency(
        uuid.UUID("DD6FCD30-B043-4058-B0D5-A6C8BC0374F4"),
        "Common_Foundation",
        "python310",
        "https://github.com/davidbrownell/v4-Common_Foundation.git",
    )

    for llvm_version in LLVM_VERSIONS.keys():
        version_specs = Configuration.VersionSpecs(
            [Configuration.VersionInfo("LLVM", SemVer(llvm_version)), ],
            {},
        )

        if CurrentShell.family_name == "Windows":
            for target_architecture in target_architectures:
                configurations["{}-mingw-{}".format(llvm_version, target_architecture)] = Configuration.Configuration(
                    """Uses LLVM 'v{}' (using mingw (aka "Msys2 MinGW Clang" at https://blog.conan.io/2022/10/13/Different-flavors-Clang-compiler-Windows.html)) targeting '{}'.""".format(llvm_version, target_architecture),
                    [common_foundation_dependency, ],
                    version_specs,
                )

            for msvc_version in [
                "17.4",
            ]:
                for target_architecture in target_architectures:
                    configurations["{}-msvc-{}-{}".format(llvm_version, msvc_version, target_architecture)] = Configuration.Configuration(
                        """Uses LLVM 'v{}' (using Microsoft Visual Studio 'v{}' (aka "LLVM/Clang" at https://blog.conan.io/2022/10/13/Different-flavors-Clang-compiler-Windows.html)) targeting '{}'.""".format(
                            llvm_version,
                            msvc_version,
                            target_architecture,
                        ),
                        [
                            Configuration.Dependency(
                                uuid.UUID("6e6cbb2c-6512-470f-ba88-a6e4ad85fed0"),
                                "Common_cpp_MSVC",
                                "{}-{}".format(msvc_version, target_architecture),
                                "https://github.com/davidbrownell/v4-Common_cpp_MSVC.git",
                            ),
                        ],
                        version_specs,
                    )

        else:
            for target_architecture in target_architectures:
                configurations["{}-{}".format(llvm_version, target_architecture)] = Configuration.Configuration(
                    "Uses LLVM 'v{}' (without any external dependencies) targeting '{}'.".format(
                        llvm_version,
                        target_architecture,
                    ),
                    [common_foundation_dependency, ],
                    version_specs,
                )

    return configurations


# ----------------------------------------------------------------------
def GetCustomActions(
    # Note that it is safe to remove any parameters that are not used
    dm: DoneManager,
    explicit_configurations: Optional[List[str]],
    force: bool,
    interactive: Optional[bool],
) -> List[Commands.Command]:

    commands: List[Commands.Command] = []

    root_dir = Path(__file__).parent
    assert root_dir.is_dir(), root_dir

    # Create a link to the foundation's .pylintrc file
    foundation_root_file = Path(Types.EnsureValid(os.getenv(Constants.DE_FOUNDATION_ROOT_NAME))) / ".pylintrc"
    assert foundation_root_file.is_file(), foundation_root_file

    commands.append(
        Commands.SymbolicLink(
            root_dir / foundation_root_file.name,
            foundation_root_file,
            remove_existing=True,
            relative_path=True,
        ),
    )

    with dm.Nested("\nProcessing 'Common_LLVM' tools...") as extract_dm:
        with extract_dm.Nested("Processing 'grcov'...") as grcov_dm:
            for index, (grcov_version, install_data) in enumerate(GRCOV_VERSIONS.items()):
                with grcov_dm.Nested("'{}' ({} of {})...".format(grcov_version, index + 1, len(GRCOV_VERSIONS))) as version_dm:
                    install_data.installer.Install(
                        version_dm,
                        force=force,
                        prompt_for_interactive=install_data.prompt_for_interactive,
                        interactive=interactive,
                    )

        with extract_dm.Nested("Processing 'LLVM'...") as llvm_dm:
            for index, (version, install_data_items) in enumerate(LLVM_VERSIONS.items()):
                with llvm_dm.Nested(
                    "'{}' ({} of {})...".format(
                        version,
                        index + 1,
                        len(LLVM_VERSIONS),
                    ),
                ) as version_dm:
                    if explicit_configurations and not any(explicit_configuration.startswith(version) for explicit_configuration in explicit_configurations):
                        version_dm.WriteVerbose("The version was skipped.\n")
                        continue

                    for install_data_item in install_data_items:
                        with version_dm.Nested("'{}'...".format(install_data_item.name)) as this_dm:
                            install_data_item.installer.Install(
                                this_dm,
                                force=force,
                                prompt_for_interactive=install_data_item.prompt_for_interactive,
                                interactive=interactive,
                            )

                        if CurrentShell.family_name != "Windows":
                            # Create a simple test program to ensure that LLVM was installed correctly
                            with version_dm.Nested("Validating installation...") as validate_dm:
                                temp_directory = CurrentShell.CreateTempDirectory()

                                was_successful = False

                                # ----------------------------------------------------------------------
                                def OnExit():
                                    if was_successful:
                                        PathEx.RemoveTree(temp_directory)
                                        return

                                    validate_dm.WriteInfo("The temporary directory '{}' has not been deleted.".format(temp_directory))

                                # ----------------------------------------------------------------------

                                with ExitStack(OnExit):
                                    source_filename = temp_directory / "test.cpp"

                                    with validate_dm.Nested("Creating source file..."):
                                        with source_filename.open("w") as f:
                                            f.write(
                                                textwrap.dedent(
                                                    """\
                                                    #include <iostream>

                                                    int main() {
                                                        std::cout << "Hello world!\\n";
                                                        return 0;
                                                    }
                                                    """,
                                                ),
                                            )

                                    with validate_dm.Nested("Compiling...") as compile_dm:
                                        command_line = 'clang++ "{}"'.format(source_filename.name)

                                        compile_dm.WriteVerbose("Command Line: {}\n\n".format(command_line))

                                        modified_env = copy.deepcopy(os.environ)

                                        modified_env["PATH"] = "{}:{}".format(
                                            modified_env["PATH"],
                                            install_data_item.installer.output_dir / "bin",
                                        )

                                        modified_env["LD_LIBRARY_PATH"] = "{}".format(
                                            install_data_item.installer.output_dir / "lib" / "x86_64-unknown-linux-gnu",
                                        )

                                        result = SubprocessEx.Run(
                                            command_line,
                                            cwd=temp_directory,
                                            env=modified_env,  # type: ignore
                                        )

                                        compile_dm.result = result.returncode

                                        if compile_dm.result != 0:
                                            compile_dm.WriteError(
                                                textwrap.dedent(
                                                    """\
                                                    Errors here generally indicate that glibc has not been installed (especially if the error is associated with 'features.h').
                                                    Visit https://www.gnu.org/software/libc/ for more information.

                                                    Please install glibc using your distro's favorite package manager.

                                                    Examples:
                                                        Ubuntu:     `apt-get install -y libc6-dev`

                                                    COMPILER ERROR
                                                    --------------
                                                    {}

                                                    """,
                                                ).format(
                                                    TextwrapEx.Indent(result.output.strip(), 4),
                                                ),
                                            )

                                            return []

                                        with compile_dm.YieldVerboseStream() as stream:
                                            stream.write(result.output)

                                    with validate_dm.Nested("Testing...") as testing_dm:
                                        command_line = "./a.out"

                                        testing_dm.WriteVerbose("Command Line: {}\n\n".format(command_line))

                                        result = SubprocessEx.Run(
                                            command_line,
                                            cwd=temp_directory,
                                        )

                                        testing_dm.result = result.returncode

                                        if testing_dm.result == 0:
                                            testing_dm.result = 0 if result.output == "Hello world!\n" else -1

                                        if testing_dm.result != 0:
                                            compile_dm.WriteError(result.output)
                                            return []

                                        with testing_dm.YieldVerboseStream() as stream:
                                            stream.write(result.output)

                                        was_successful = True

    return commands
