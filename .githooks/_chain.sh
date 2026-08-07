# Sourced by the hooks in this directory. Not a hook itself.
#
# This repository points core.hooksPath at .githooks so that pre-commit can be
# wired up. That override is repository-wide: it also hides any hooks the
# developer configured globally. Each hook here therefore delegates to the
# global hook of the same name first, so nothing set up outside this repo is
# silently lost.

run_global_hook() {
    name="$1"
    shift

    global_dir=$(git config --global core.hooksPath 2>/dev/null || true)
    [ -n "$global_dir" ] || return 0

    # git stores "~/..." literally; the shell will not expand it for us.
    case "$global_dir" in
        "~"*) global_dir="$HOME${global_dir#\~}" ;;
    esac

    # On Windows git reports a native path ("C:\Users\me\.githooks"). The shell
    # running this hook is Git Bash, where a backslash path fails every file
    # test, so the global hook would be skipped in silence.
    global_dir=$(printf '%s' "$global_dir" | sed 's/\\/\//g')

    hook="$global_dir/$name"
    [ -f "$hook" ] || return 0

    # Exit code is deliberately not swallowed: a global pre-push that blocks
    # must still block here.
    sh "$hook" "$@"
}
