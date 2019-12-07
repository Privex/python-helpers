#!/usr/bin/env bash

: "${_SHELLCORE_INIT=0}"
: "${QUIET=0}"

TEST_SUMMARY="$(mktemp)"

_CLEANUP_FILES=()

if [ -z ${PY_TEST_CMD+x} ]; then
    PY_TEST_CMD=('python3' '-m' 'pytest' '-rxXs')
    if ((QUIET == 0)); then
        PY_TEST_CMD+=('-v')
    fi
fi

#quiet_log() { ((QUIET==0)) && cat; }
quiet_log() {
    if ((QUIET == 0)); then
        cat
    else
        cat >/dev/null
    fi
}
quiet_err() { quiet_log >&2; }

# shellcheck disable=SC2015
quiet_msg() { ((QUIET == 0)) && msg "$@" || true; }

# shellcheck disable=SC2015
quiet_msgerr() { ((QUIET == 0)) && msgerr "$@" || true; }

cleanup_files() {
    quiet_msgerr yellow " >>> Cleaning up ${#_CLEANUP_FILES[@]} leftover temporary files...\m"
    for f in "${_CLEANUP_FILES[@]}"; do
        arg_len=$(($(len "$f")))
        if ((arg_len < 5)); then
            msgerr "WARNING: cleanup_files detected passed a path shorter than 5 chars: '$a'"
            msgerr "Will NOT remove this for safety reasons."
            continue
        fi
        if [[ -e "$f" ]]; then
            quiet_msgerr yellow "\t -> Removing" "$(rm -v "$f" | tr -d "\n")"
        else
            quiet_msgerr yellow "\t -> Skipping file '$f' - does not exist!"
        fi
    done
    quiet_msgerr
}

add_cleanup_files() {
    if (($# < 1)); then
        msgerr "ERROR: add_cleanup_file expects at least 1 arg!"
        return 1
    fi
    for a in "$@"; do
        _CLEANUP_FILES+=("$a")
    done
}

#rm_on_exit() {
#    local arg_len _exit_cmd
#    for a in "$@"; do
#        arg_len=$(($(len "$1")))
#        if ((arg_len < 5)); then
#            msgerr "WARNING: rm_on_exit was passed a path shorter than 5 chars: '$a'"
#            msgerr "Will NOT add this to exit trap for safety reasons."
#            continue
#        fi
#        _exit_cmd="rm -v "'"'"$a"'"'
#        msgerr bold yellow "Adding on-exit remove command: $_exit_cmd"
#        add_on_exit "$_exit_cmd"
#    done
#}

init_shellcore() {
    ((_SHELLCORE_INIT != 0)) && return
    # Error handling function for ShellCore
    _sc_fail() { echo >&2 "Failed to load or install Privex ShellCore..." && exit 1; }
    # If `load.sh` isn't found in the user install / global install, then download and run the auto-installer
    # from Privex's CDN.
    [[ -f "${HOME}/.pv-shcore/load.sh" ]] || [[ -f "/usr/local/share/pv-shcore/load.sh" ]] ||
        { curl -fsS https://cdn.privex.io/github/shell-core/install.sh | bash >/dev/null; } || _sc_fail

    # Attempt to load the local install of ShellCore first, then fallback to global install if it's not found.
    [[ -d "${HOME}/.pv-shcore" ]] && source "${HOME}/.pv-shcore/load.sh" ||
        source "/usr/local/share/pv-shcore/load.sh" || _sc_fail

    #    add_on_exit "rm "'"'"$TEST_SUMMARY"'"'
    #    rm_on_exit "$TEST_SUMMARY"
    add_cleanup_files "$TEST_SUMMARY"
    add_on_exit "cleanup_files"

    autoupdate_shellcore
    sg_load_lib trap
    _SHELLCORE_INIT=1
}

###
# Python Virtualenv shortcuts
###

activate() {
    ((_SHELLCORE_INIT == 0)) && init_shellcore
    local envdir="./venv"
    if [[ "$#" -gt 0 ]]; then envdir="$1"; fi
    source "${envdir}/bin/activate"
    msg bold green "Activated virtualenv in $envdir"
}

find_in_path() {
    (($# < 1)) && msg red "find_in_path expects at least one argument!" && return 1
    ((_SHELLCORE_INIT == 0)) && init_shellcore
    local find_str="$1" split_path
    split_path=($(split_by "$PATH" ":"))

    for p in "${split_path[@]}"; do
        if grep -q "$find_str" <<<"$p"; then
            echo "$p"
        fi
    done
    return
}

#####
# Usage:
#     if is_current_venv "./venv_py37"; then
#         echo "The virtualenv at ./venv_py37 is already activated!"
#     else
#         echo "Virtualenv was not activated. Activating ./venv_py37"
#         ./venv_py37/bin/activate
#     fi
#
is_current_venv() {
    [ -z "${VIRTUAL_ENV+x}" ] && return 1
    local envdir="./venv" abs_envdir
    ((_SHELLCORE_INIT == 0)) && init_shellcore
    (($# < 1)) && msgerr yellow "No virtualenv dir passed to is_current_venv... Falling back to $envdir" || envdir="$1"
    abs_envdir="$(cd "$envdir" && pwd)"
    [[ "$abs_envdir" == "$VIRTUAL_ENV" ]] && grep -q "$VIRTUAL_ENV" <<<"$PATH"
}

############
#
# Usage (check if any virtualenv is currently activated, and print details about it, otherwise error and return 1):
#
#     venv_status
#
#
# Usage (check if a specific virtualenv is activated, if it is, print details about it, otherwise error and return 1):
#
#     venv_status "./venv_py37"
#
#
# shellcheck disable=SC2120
venv_status() {
    ((_SHELLCORE_INIT == 0)) && init_shellcore

    if (($# > 0)); then
        if not is_current_venv "$1"; then
            msgerr bold red " !!! -> The virtualenv at '$1' is not currently activated!"
            return 1
        fi
    fi

    if [ -n "${VIRTUAL_ENV+x}" ] && [ -n "$VIRTUAL_ENV" ]; then
        msg
        msg bold green "\t(+) A Python virtual environment is currently active in your shell.\n"
        msg bold purple "\tCurrent VIRTUAL_ENV: ${RESET}${MAGENTA}${VIRTUAL_ENV}"
        msg bold purple "\tCurrent Python executable: ${RESET}${MAGENTA}$(command -v python3)"
        msg bold purple "\tCurrent Python version: ${RESET}${MAGENTA}$(python3 -V)\n"
        venv_paths=($(find_in_path "${VIRTUAL_ENV}"))
        msg bold purple "\tVirtualenv paths present in PATH:\n"
        for p in "${venv_paths[@]}"; do
            msg purple "\t\t - ${p}"
        done
        msg
        return 0
    else
        msgerr
        msgerr bold red " !!! -> No virtualenv is currently activated!"
        msgerr red " !!! -> The variable VIRTUAL_ENV is either unset or empty"
        msgerr
        return 1
    fi
}

force_deactivate() {
    local orig_venv clean_path
    [ -z "${VIRTUAL_ENV+x}" ] && msgerr red "Cannot deactivate as VIRTUAL_ENV is not set!" && return 1

    msg green " >> De-activating previous virtualenv at ${VIRTUAL_ENV}"
    orig_venv="${VIRTUAL_ENV}"

    if has_command deactivate; then
        deactivate
    else
        msgerr yellow " !! Warning: Command 'deactivate' not found. Will manually cleanup virtualenv." | quiet_err
    fi

    [ -n "${VIRTUAL_ENV+x}" ] && unset VIRTUAL_ENV
    if grep -q "$orig_venv" <<<"$PATH"; then
        msg yellow "Warning: found leftover virtualenv directory '$orig_venv' in PATH. Cleaning PATH..." | quiet_err
        msg yellow "\nCurrent path: $PATH\n" | quiet_err
        clean_path=$(echo "$PATH" | sed -E "s#${orig_venv}([a-zA-Z0-9_/]+):?##")
        PATH="$clean_path"
        msg yellow "\nNew path: $PATH\n" | quiet_err
    fi
}

############
# All-in-one virtualenv function - creates new venv folders, deactivates previous project venv's, activates
# requested venv
#
# WARNING: If the requested virtualenv folder doesn't exist, this function will return exit code "1", as to alert the
# calling function that a new virtualenv was created and dependencies need to be installed.
#
# Usage:
#
#     pyactivate [venv_dir] [py_exe]
#
#     venv_dir  - (default: './venv')   virtualenv folder to create / activate
#     py_exe    - (default: 'python3')  if virtualenv doesn't exist, use this python executable to create it.
#
#
# First, it checks to see if the variable VIRTUAL_ENV is set, and checks if the path in VIRTUAL_ENV matches the path
# you're trying to activate. If it does, then it will simply print details about your current virtualenv and return 0.
#
# If there appears to currently be a virtualenv activated, but it isn't the one you passed as the first argument, then
# it will de-activate the current virtualenv, and ensure that the variable
#
# Next it checks if the requested virtualenv folder exists or not. If it doesn't, then it will create the virtualenv
# using the python executable specified (default: python3)
#
# Finally, as long as the requested virtualenv folder wasn't already activated, it will activate the virtualenv.
#
pyactivate() {
    ((_SHELLCORE_INIT == 0)) && init_shellcore
    local envdir="./venv" pyexe="python3" abs_envdir orig_venv clean_path v_activate=1 new_venv=0
    (($# >= 1)) && envdir="$1"
    (($# >= 2)) && pyexe="$2"
    abs_envdir="$(cd "$envdir" && pwd)"

    if is_current_venv "$abs_envdir"; then
        venv_status "$abs_envdir" | quiet_err
        msg green " >> Not altering the virtualenv as the requested virtualenv is already activated."
        v_activate=0
        #        if [[ "$abs_envdir" == "$VIRTUAL_ENV" ]] && grep -q "$VIRTUAL_ENV" <<<"$PATH"; then
        #            msg bold green " !!! Virtualenv is already activated"
        #            msg purple "\tCurrent VIRTUAL_ENV: ${VIRTUAL_ENV}"
        #            venv_paths=($(find_in_path "${VIRTUAL_ENV}"))
        #            msg purple "\tVirtualenv paths present in PATH:"
        #            for p in "${venv_paths[@]}"; do
        #                msg purple "\t\t - ${p}"
        #            done
        #            return
        #        fi
    elif venv_status | quiet_err; then
        force_deactivate
        #        msg green " >> De-activating previous virtualenv at ${VIRTUAL_ENV}"
        #        orig_venv="${VIRTUAL_ENV}"
        #        deactivate
        #        [ -n "${VIRTUAL_ENV+x}" ] && unset VIRTUAL_ENV
        #        if grep -q "$orig_venv" <<<"$PATH"; then
        #            msgerr yellow "Warning: found leftover virtualenv directory '$orig_venv' in PATH. Cleaning PATH..."
        #            msgerr yellow "\nCurrent path: $PATH\n"
        #            clean_path=$(echo "$PATH" | sed -E "s#${orig_venv}([a-zA-Z0-9_/]+):?##")
        #            PATH="$clean_path"
        #            msgerr yellow "\nNew path: $PATH\n"
        #        fi
    fi

    if [[ ! -d "$abs_envdir" ]]; then
        msg yellow " >> Virtualenv folder '$abs_envdir' did not exist. Creating it now using executable ${pyexe} "
        mkvenv "$pyexe" "$abs_envdir"
        new_venv=1
    fi

    ((v_activate == 1)) && msg green " >> Activating requested virtualenv at $abs_envdir ..." && activate "$abs_envdir"
    ((new_venv == 1)) && return 1 || return 0
}

# Usage:  mkvenv [python_exe] [env_folder]
# mkvenv                  # no args = use system python3 and make in ./venv
# mkvenv python3.7        # use system python3.7 and make in ./venv
# mkvenv python3.6 ./env  # use system python3.6 and make in ./env
mkvenv() {
    ((_SHELLCORE_INIT == 0)) && init_shellcore
    local pyexe="python3" pyver
    local envdir="./venv" abs_envdir
    if [[ "$#" -gt 0 ]]; then pyexe="$1"; fi
    if [[ "$#" -gt 1 ]]; then envdir="$2"; fi
    abs_envdir="$(cd "$envdir" && pwd)"
    pyver=$(/usr/bin/env "$pyexe" -V)
    /usr/bin/env "$pyexe" -m venv "$envdir"

    msg bold green "\nMade virtual env using $pyver @ $envdir\n"
    msg purple "\tPython executable:        \t$(command -v "$pyexe")"
    msg purple "\tPython version:           \t${pyver}"
    msg purple "\tVirtualenv Dir (absolute):\t${abs_envdir}\n"
}

pyenv_install() {
    ((_SHELLCORE_INIT == 0)) && init_shellcore
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
    local _python="python3" _venv_dir="./venv" cmd_appended=0 test_cmd test_output_tmp="$(mktemp)" test_output
    read -r -a test_cmd <<<"${PY_TEST_CMD[@]}"
    (($# >= 1)) && _python="$1"
    (($# >= 2)) && _venv_dir="$2"
    (($# >= 3)) && cmd_appended=1 && read -r -a test_cmd <<<"${test_cmd[*]} ${*:3}"
    ((_SHELLCORE_INIT == 0)) && init_shellcore

    #    add_on_exit "$test_output_tmp"
    add_cleanup_files "$test_output_tmp"

    #    set +ue
    #    sg_load_lib gnusafe
    #    gnusafe || return 1
    #    set -ue

    set +o pipefail
    if pyactivate "$_venv_dir" "$_python"; then
        set -o pipefail
        venv_status | quiet_log
        msg green " >> Virtualenv ${_venv_dir} already exists. Updating packages."
        if ((cmd_appended == 1)); then
            msg green " >> Installing only main project as extra args were specified"
            python3 ./setup.py install | quiet_log
        else
            msg green " >> Running pip install -U '.[dev]' ..."
            python3 -m pip install -U '.[dev]' | quiet_log
        fi
        #    if [[ -d "$_venv_dir" ]]; then
        #        msg green " >> Virtualenv ${_venv_dir} already exists. Activating it and updating packages."
        #        activate "${_venv_dir}"
        #        if (($# > 0)); then
        #            msg green " >> Installing only main project as extra args were specified"
        #            python3 ./setup.py install
        #        else
        #            msg green " >> Running pip install -U '.[dev]' ..."
        #            python3 -m pip install -U '.[dev]'
        #        fi
    else
        set -o pipefail
        #        msg green " >> Creating virtualenv at $_venv_dir using python version: ${_CURR_PY_VER[*]}"
        #        mkvenv "$_PYTHON_EXE" "${_venv_dir}"
        #        activate "${_venv_dir}"
        venv_status | quiet_log
        msg green " >> [NEW VIRTUALENV] Running pip install -U '.[dev]' ..."
        python3 -m pip install -U '.[dev]' | quiet_log
    fi
    msg "\n\n --------------\n"
    msg green " >> Running test command: '${test_cmd[*]}' ..."

    env "${test_cmd[@]}" | tee -a "$test_output_tmp"
    test_output="$(sed -Ene '/[0-9]+ passed(,| in)/p' "$test_output_tmp" | tr -d '=')"

    #    if (($# > 0)); then
    #        #            msg green " >> Installing only main project as extra args were specified"
    #        #            pip install -U '.'
    #        msg green " >> Running pytest with args: $* ..."
    #        "$_python" -m pytest --cov=./privex -rxXs -v "$@"
    #    else
    #        #            msg green " >> Running pip install -U '.[dev]' ..."
    #        #            pip install -U '.[dev]'
    #        msg green " >> Running pytest ..."
    ##        "$_python" -m pytest --cov=./privex -rxXs -v
    #        env "${PY_TEST_CMD[@]}"
    #    fi
    {
        msg bold green "\n ============== TESTS FINISHED SUCCESSFULLY ============== \n"
        msg purple "\tPython executable:        \t$(command -v python3)"
        msg purple "\tPython version:           \t$(python3 -V)"
        msg purple "\tVirtualenv Dir:           \t${_venv_dir}\n"
        msg purple "\tTests completed/skipped:  \t${test_output}\n"
        msg bold green " ========================================================= \n"
    } | tee -a "$TEST_SUMMARY"

    # | >&2 cat | mapfile -t TEST_SUMMARY -O "${#TEST_SUMMARY[@]}"
    export TEST_SUMMARY
    msg green " >> Deactivating virtualenv ..."
    set +eu
    force_deactivate
    set -eu
    msg "\n\n"
}
