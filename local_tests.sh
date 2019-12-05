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

# Error handling function for ShellCore
_sc_fail() { echo >&2 "Failed to load or install Privex ShellCore..." && exit 1; }
# If `load.sh` isn't found in the user install / global install, then download and run the auto-installer
# from Privex's CDN.
[[ -f "${HOME}/.pv-shcore/load.sh" ]] || [[ -f "/usr/local/share/pv-shcore/load.sh" ]] ||
    { curl -fsS https://cdn.privex.io/github/shell-core/install.sh | bash >/dev/null; } || _sc_fail

# Attempt to load the local install of ShellCore first, then fallback to global install if it's not found.
[[ -d "${HOME}/.pv-shcore" ]] && source "${HOME}/.pv-shcore/load.sh" ||
    source "/usr/local/share/pv-shcore/load.sh" || _sc_fail

autoupdate_shellcore

sg_load_lib trap

: ${USE_PYENV=1}

if [ -z ${PY_VERS+x} ]; then
    PY_VERS=("python3.6" "python3.7" "python3.8")
fi

if [ -z ${PYENV_VERS+x} ]; then
    PYENV_VERS=("3.6.7" "3.7.1" "3.8.0")
fi

###
# Python Virtualenv shortcuts
###

activate() {
    local envdir="./venv"
    if [[ "$#" -gt 0 ]]; then envdir="$1"; fi
    source "${envdir}/bin/activate"
    msg bold green "Activated virtualenv in $envdir"
}

# Usage:  mkvenv [python_exe] [env_folder]
# mkvenv                  # no args = use system python3 and make in ./venv
# mkvenv python3.7        # use system python3.7 and make in ./venv
# mkvenv python3.6 ./env  # use system python3.6 and make in ./env
mkvenv() {
    local pyexe="python3"
    local envdir="./venv"
    if [[ "$#" -gt 0 ]]; then pyexe="$1"; fi
    if [[ "$#" -gt 1 ]]; then envdir="$2"; fi
    local pyver=$(/usr/bin/env "$pyexe" -V)
    /usr/bin/env "$pyexe" -m venv "$envdir"
    msg bold green "Made virtual env using $pyver @ $envdir"
}

pyenv_install() {
    (($# < 1)) && msg bold red "ERROR: pyenv_install expects at least 1 arg - python version to install" && return 1

    local os_name="$(uname -s)" py_ver="$1"
    if [[ "$os_name" == "Darwin" ]]; then
        export CFLAGS="-I$(brew --prefix readline)/include -I$(brew --prefix openssl)/include"
        export CFLAGS="${CFLAGS} -I$(xcrun --show-sdk-path)/usr/include"
        export LDFLAGS="-L$(brew --prefix readline)/lib -L$(brew --prefix openssl)/lib"
        export PYTHON_CONFIGURE_OPTS="--enable-unicode=ucs2"
    fi
    msg bold green " >>> Installing Python ${py_ver} via pyenv..."
    pyenv install -v "$py_ver"
    msg bold green " >>> Successfully installed Python ${py_ver}"
}

main_tests() {
    if [[ -d "$VENV_PY_VER" ]]; then
        msg green " >> Virtualenv ${VENV_PY_VER} already exists. Activating it and updating packages."
        activate "${VENV_PY_VER}"
        if (($# > 0)); then
            msg green " >> Installing only main project as extra args were specified"
            ./setup.py install
        else
            msg green " >> Running pip install -U '.[dev]' ..."
            pip install -U '.[dev]'
        fi
    else
        msg green " >> Creating virtualenv at $VENV_PY_VER using python version: ${_CURR_PY_VER[*]}"
        mkvenv "$_PYTHON_EXE" "${VENV_PY_VER}"
        activate "${VENV_PY_VER}"
        msg green " >> [NEW VIRTUALENV] Running pip install -U '.[dev]' ..."
        pip install -U '.[dev]'
    fi
    if (($# > 0)); then
        #            msg green " >> Installing only main project as extra args were specified"
        #            pip install -U '.'
        msg green " >> Running pytest with args: $* ..."
        python3 -m pytest --cov=./privex -rxXs -v "$@"
    else
        #            msg green " >> Running pip install -U '.[dev]' ..."
        #            pip install -U '.[dev]'
        msg green " >> Running pytest ..."
        python3 -m pytest --cov=./privex -rxXs -v
    fi
    msg green " >> Deactivating virtualenv ..."
    set +eu
    deactivate
    set -eu
}

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
        main_tests "$@"
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
        main_tests "$@"
        #        if [[ -d "$VENV_PY_VER" ]]; then
        #            msg green " >> Virtualenv ${VENV_PY_VER} already exists. Activating it and updating packages."
        #            activate "${VENV_PY_VER}"
        #        else
        #            msg green " >> Creating virtualenv at $VENV_PY_VER using python version: ${_CURR_PY_VER[*]}"
        #            mkvenv "python3" "${VENV_PY_VER}"
        #            activate "${VENV_PY_VER}"
        #        fi
        #        msg green " >> Running pip install -U '.[dev]' ..."
        #        pip install -U '.[dev]'
        #        msg green " >> Running pytest ..."
        #        python3 -m pytest --cov=./privex -rxXs -v
        #        msg green " >> Deactivating virtualenv ..."
        #        deactivate
    done
fi
