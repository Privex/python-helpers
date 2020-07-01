#!/usr/bin/env bash
################################################################
#                                                              #
#         Local development test runner script for:            #
#                                                              #
#                  Privex Python Helpers                       #
#            (C) 2019 Privex Inc.   GNU AGPL v3                #
#                                                              #
#      Privex Site: https://www.privex.io/                     #
#                                                              #
#      Github Repo: https://github.com/Privex/python-helpers   #
#                                                              #
################################################################
#
# Basic Usage:
#
#     ./local_tests.sh
#
# Run only specific tests (and don't update deps):
#
#     ./local_deps tests/test_general.py tests/test_collections.py
#
################################################################
#
# Runs the unit tests across multiple Python versions locally, similar to Travis-CI.
#
# If pyenv is available, will install all python versions listed in PYENV_VERS into pyenv, and
# create a virtualenv for each version.
#
# If pyenv is unavailable, will attempt to use the system python executables listed in PY_VERS
# (will skip any that aren't available).
#
# To force use of system python EXE's, set env var USE_PYENV=0 like so:
#
#    USE_PYENV=0 ./local_tests.sh
#
################################################################

set -e

_TESTDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/lib_test.sh
source "${_TESTDIR}/lib/lib_test.sh"

((_SHELLCORE_INIT == 0)) && init_shellcore

# Set USE_PYENV=0 to disable the use of 'pyenv' if it's detected.
: "${USE_PYENV=1}"
: "${QUIET=0}"
USE_PYENV=$((USE_PYENV))

# PY_VERS is an array which defines the local system python executables for each python version to run the tests for.
[ -z ${PY_VERS+x} ] && PY_VERS=("python3.6" "python3.7" "python3.8")
# PYENV_VERS is an array of Python version numbers to install & use for running tests if 'pyenv' is available.
[ -z ${PYENV_VERS+x} ] && PYENV_VERS=("3.6.9" "3.7.1" "3.8.0")

has_command pyenv && HAS_PYENV=1 || HAS_PYENV=0

if ((HAS_PYENV == 1)) && ((USE_PYENV == 1)); then
    eval "$(pyenv init -)"
    PYENV_AVAIL_VERS=($(pyenv versions --bare))
    for v in "${PYENV_VERS[@]}"; do
        containsElement "$v" "${PYENV_AVAIL_VERS[@]}" && continue
        pyenv_install "$v"
    done
    for v in "${PYENV_VERS[@]}"; do
        msg green " >> Setting shell python version to $v"
        export PYENV_VERSION="$v"
        _CURR_PY_VER=($(python3 -V))
        CURR_PY_VER="${_CURR_PY_VER[1]}"
        VENV_PY_VER="venv_pyenv_${CURR_PY_VER}"
        _PYTHON_EXE="python3"
        main_tests "${_PYTHON_EXE}" "${VENV_PY_VER}" "$@"
    done
    msg green " >> Clearing pyenv shell variable ..."
    unset PYENV_VERSION
else
    for v in "${PY_VERS[@]}"; do
        if ! has_command "$v" || ! "$v" -V; then
            msg red " >> Python version $v is unavailable. Skipping."
            continue
        fi
        _CURR_PY_VER=($("$v" -V))
        CURR_PY_VER="${_CURR_PY_VER[1]}"
        VENV_PY_VER="venv_py_${CURR_PY_VER}"
        _PYTHON_EXE="$v"
        main_tests "${_PYTHON_EXE}" "${VENV_PY_VER}" "$@"
    done
fi

msg bold blue "\n\n-------------------------------------------------------\n"
msg bold blue "#            FINISHED ALL UNIT TESTS."
msg bold blue "\n-------------------------------------------------------\n"
msg bold blue "#                    SUMMMARY"
msg bold blue "\n-------------------------------------------------------\n"


cat "$TEST_SUMMARY"

