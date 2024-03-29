@echo off
@REM ----------------------------------------------------------------------
@REM |
@REM |  Enlists and setups a repository and its dependencies.
@REM |
@REM |  Run as:
@REM |      Bootstrap.cmd <common code dir> [--name <unique_environment_name>] [Optional Setup.cmd args]*
@REM |
@REM |      Where:
@REM |          <common code dir>                : Name of the directory in which common dependencies are enlisted.
@REM |                                             This location can be reused across multiple projects and
@REM |                                             enlistments.
@REM |
@REM |          --name <unique_environment_name> : Setup an environment with a unique name. This allows for the
@REM |                                             creation of side-by-side environments that are otherwise identical.
@REM |                                             It is very rare to setup an environment with a unique name.
@REM |
@REM |          [Optional Setup.cmd args]        : Any additional args passed to Setup.cmd for the respository
@REM |                                             and its dependencies. See Setup.cmd for more information on
@REM |                                             the possible arguments and their use.
@REM |
@REM ----------------------------------------------------------------------

if "%~1"=="" (
    @echo.
    @echo [31m[1mERROR:[0m This script bootstraps enlistment and setup activities for a repository and its dependencies.
    @echo [31m[1mERROR:[0m
    @echo [31m[1mERROR:[0m Usage:
    @echo [31m[1mERROR:[0m     %0 ^<common code dir^> [--name ^<custom Setup.cmd environment name^>] [Optional Setup.cmd args]*
    @echo [31m[1mERROR:[0m
    @echo.

    exit /B -1
)

set _COMMON_CODE_DIR=%~1
shift /1

if "%DEVELOPMENT_ENVIRONMENT_REPOSITORY_ACTIVATED_KEY%" NEQ "" (
    @echo.
    @echo [31m[1mERROR:[0m ERROR: Please run this script from a standard ^(non-activated^) command prompt.
    @echo [31m[1mERROR:[0m
    @echo.

    set _ERRORLEVEL=-1
    goto Exit
)

REM Enlist and setup Common_Foundation

if not exist "%_COMMON_CODE_DIR%\Common\Foundation" (
    echo Enlisting in Common_Fundation...
    echo.

    git clone -b release https://github.com/davidbrownell/v4-Common_Foundation.git "%_COMMON_CODE_DIR%\Common\Foundation.tmp"
    if %ERRORLEVEL% NEQ 0 (
        set _ERRORLEVEL=%ERRORLEVEL%
        goto Exit
    )

    move "%_COMMON_CODE_DIR%\Common\Foundation.tmp" "%_COMMON_CODE_DIR%\Common\Foundation"

    echo.
    echo DONE!
    echo.
)

@REM Note that the following loop has been crafted to work around batch's crazy
@REM expansion rules. Modify at your own risk!
:GetRemainingArgs_Begin

if "%~1"=="" goto GetRemainingArgs_End

set _ARG=%~1

if "%_ARG:~,6%"=="--name" goto GetRemainingArgs_Name

@REM If here, we are looking at an arg that should be passed to the script
set _BOOTSTRAP_CLA=%_BOOTSTRAP_CLA% "%_ARG%"
goto GetRemainingArgs_Continue

:GetRemainingArgs_Name
@REM If here, we are looking at a name argument
shift /1
set _BOOTSTRAP_NAME=%1
shift /1
goto GetRemainingArgs_Continue

:GetRemainingArgs_Continue
shift /1
goto GetRemainingArgs_Begin

:GetRemainingArgs_End

REM This works around a strange problem when attempting to invoke a command file using
REM a relative path.
pushd "%_COMMON_CODE_DIR%"
set _COMMON_CODE_ABSOLUTE_DIR=%CD%
popd

set _BOOTSTRAP_NAME_ARG=
if "%_BOOTSTRAP_NAME%" NEQ "" (
    set _BOOTSTRAP_NAME_ARG=--name "%_BOOTSTRAP_NAME%"
)

@REM ----------------------------------------------------------------------
call "%_COMMON_CODE_ABSOLUTE_DIR%\Common\Foundation\Setup.cmd" %_BOOTSTRAP_NAME_ARG% %_BOOTSTRAP_CLA%
if %ERRORLEVEL% NEQ 0 (
    set _ERRORLEVEL=%ERRORLEVEL%
    goto Exit
)

REM Write the environment activation and python execution statements to a temporary file
REM so that this environment remains unactivated. By doing this, the current script can be
REM invoked repeatedly from the same environment.
set _BOOTSTRAP_ACTIVATE_CMD=Activate.cmd

if "%_BOOTSTRAP_NAME%" NEQ "" (
    set _BOOTSTRAP_ACTIVATE_CMD=Activate.%_BOOTSTRAP_NAME%.cmd
)

REM Get the current dir and remove the trailing slash
set _BOOTSTRAP_THIS_DIR=%~dp0
set _BOOTSTRAP_THIS_DIR=%_BOOTSTRAP_THIS_DIR:~0,-1%

(
    echo @echo off
    echo.
    echo call "%_COMMON_CODE_DIR%\Common\Foundation\%_BOOTSTRAP_ACTIVATE_CMD%" python310
    echo if %%ERRORLEVEL%% NEQ 0 exit /B %%ERRORLEVEL%%
    echo.
    echo call Enlist.cmd Enlist "%_BOOTSTRAP_THIS_DIR%" "%_COMMON_CODE_ABSOLUTE_DIR%"
    echo if %%ERRORLEVEL%% NEQ 0 exit /B %%ERRORLEVEL%%
    echo.
    echo call Enlist.cmd Setup "%_BOOTSTRAP_THIS_DIR%" "%_COMMON_CODE_ABSOLUTE_DIR%" %_BOOTSTRAP_CLA%
    echo if %%ERRORLEVEL%% NEQ 0 exit /B %%ERRORLEVEL%%
    echo.
) >..\Bootstrap.tmp.cmd

cmd /C ..\Bootstrap.tmp.cmd
set _ERRORLEVEL=%ERRORLEVEL%
del ..\Bootstrap.tmp.cmd

@REM ----------------------------------------------------------------------
:Exit
set _COMMON_CODE_DIR=
set _ARG=
set _BOOTSTRAP_CLA=
set _BOOTSTRAP_NAME=
set _BOOTSTRAP_NAME_ARG=
set _BOOTSTRAP_THIS_DIR=
set _BOOTSTRAP_ACTIVATE_CMD=
set _COMMON_CODE_ABSOLUTE_DIR=

exit /B %_ERRORLEVEL%
