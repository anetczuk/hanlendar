#!/bin/bash

set -eu
#set -u


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


FIX_ERROR=0

while [[ $# -gt 0 ]]; do
    case $1 in
      --fix)    FIX_ERROR=1
                shift # past argument
                ;;
      -*)       echo "Unknown option $1"
                exit 1
                ;;
      *)    shift # past argument
            ;;
    esac
done


check_dirs=()
src_dir="$SCRIPT_DIR/../src"
check_dirs+=("$src_dir")
examples_dir="$SCRIPT_DIR/../example"
if [ -d "$examples_dir" ]; then
    check_dirs+=("$examples_dir")
fi
check_dirs+=("$SCRIPT_DIR")


echo "running black"
black --line-length=120 "${check_dirs[@]}"
exit_code=$?

if [ $exit_code -ne 0 ]; then
    exit $exit_code
fi

echo "black -- no warnings found"


## E115 intend of comment
## E126 continuation line over-indented for hanging indent
## E201 whitespace after '('
## E202 whitespace before ')'
## E203 whitespace before ':' - black formatter adds space before
## E221 multiple spaces before equal operator
## E241 multiple spaces after ':'
## E262 inline comment should start with '# '
## E265 block comment should start with '# '
## E266 too many leading '#' for block comment
## E402 module level import not at top of file
## E501 line too long (80 > 79 characters)
## W391 blank line at end of file
## D    all docstyle checks
ignore_errors=E115,E126,E201,E202,E203,E221,E241,E262,E265,E266,E402,E501,W391,D


echo
echo "running pycodestyle"
echo "to ignore warning inline add comment at the end of line: # noqa: <warning-code>"
pycodestyle --show-source --statistics --count --ignore="$ignore_errors" "${check_dirs[@]}"
exit_code=$?

if [ $exit_code -ne 0 ]; then
    exit $exit_code
fi

echo "pycodestyle -- no warnings found"


## F401 'PyQt5.QtCore' imported but unused
ignore_errors=$ignore_errors,F401


echo
echo "running flake8"
echo "to ignore warning for one line put following comment in end of line: # noqa: <warning-code>"
python3 -m flake8 --show-source --statistics --count --ignore="$ignore_errors" "${check_dirs[@]}"
exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo -e "\nflake8 errors found"
    exit $exit_code
fi

echo "flake8 -- no warnings found"


check_files=""
src_files=$(find "$src_dir" -type f -name "*.py")
check_files="${check_files} ${src_files}"
example_files=$(find "$examples_dir" -type f -name "*.py") || true
if [[ "${example_files}" != "" ]]; then
    check_files="${check_files} ${example_files}"
fi
tools_files=$(find "$SCRIPT_DIR" -type f -name "*.py")
check_files="${check_files} ${tools_files}"


## for unknown reason pylint works better from root directory
pushd "${SCRIPT_DIR}/.." > /dev/null
echo
echo "running pylint3"
echo "to ignore warning for module put following line on top of file: # pylint: disable=<check_id>"
echo "to ignore warning for one line put following comment in end of line: # pylint: disable=<check_id>"
# shellcheck disable=SC2086
pylint --rcfile="$SCRIPT_DIR/pylint3.config" $check_files
exit_code=$?
if [ $exit_code -ne 0 ]; then
    exit $exit_code
fi
echo "pylint3 -- no warnings found"
popd > /dev/null


echo
echo "running ruff"
echo "to ignore warning for module put following line on top of file: # ruff: noqa: <check_id>"
echo "to ignore warning for one line put following comment in line before: # ruff: noqa: <check_id>"
run_ruff() {
    local check_dir="${1}"
    echo "checking ${check_dir}"
    pushd "${check_dir}" > /dev/null

    local RUFF_ARGS=()
    if [[ ${FIX_ERROR} -ne 0 ]]; then
        RUFF_ARGS+=(--fix)
    fi
    #RUFF_ARGS+=(--statistics)

    ignore_errors=()
    ignore_errors+=(ANN001)     ## ANN001 Missing type annotation for function argument
    ignore_errors+=(ANN201)     ## ANN201 Missing return type annotation for public function
    ignore_errors+=(ANN202)     ## ANN202 Missing return type annotation for private function
    ignore_errors+=(ANN204)     ## ANN204 Missing return type annotation for special method
    ignore_errors+=(D100)       ## D100 Missing docstring in public module
    ignore_errors+=(D101)       ## D101 Missing docstring in public class
    ignore_errors+=(D102)       ## D102 Missing docstring in public method
    ignore_errors+=(D103)       ## D103 Missing docstring in public function
    ignore_errors+=(D104)       ## D104 Missing docstring in public package
    ignore_errors+=(D107)       ## D107 Missing docstring in `__init__`
    ignore_errors+=(D203)       ## incorrect-blank-line-before-class
    ignore_errors+=(D213)       ## multi-line-summary-second-line
    ignore_errors+=(E501)       ## E501 Line too long (111 > 88)
    ignore_errors+=(ERA001)     ## ERA001 Found commented-out code
    ignore_errors+=(PLR2004)    ## PLR2004 Magic value used in comparison, consider replacing `2` with a constant variable
    ignore_errors+=(PT009)      ## PT009 Use a regular `assert` instead of unittest-style `assertEqual`
    ignore_errors+=(RUF013)     ## RUF013 PEP 484 prohibits implicit `Optional`
    ignore_errors+=(RUF100)     ## RUF100 [*] Unused `noqa` directive (unused: `F811`)
    ignore_errors+=(TRY400)     ## TRY400 Use `logging.exception` instead of `logging.error`

    ## TODO: fix
    ignore_errors+=(DTZ007)     ## DTZ007 Naive datetime constructed using `datetime.datetime.strptime()` without %z
    ignore_errors+=(DTZ011)     ## DTZ011 `datetime.date.today()` used
    ignore_errors+=(I001)       ## I001 [*] Import block is un-sorted or un-formatted
    ignore_errors+=(PTH100)     ## PTH100 `os.path.abspath()` should be replaced by `Path.resolve()`
    ignore_errors+=(PTH103)     ## PTH103 `os.makedirs()` should be replaced by `Path.mkdir(parents=True)`
    ignore_errors+=(PTH109)     ## PTH109 `os.getcwd()` should be replaced by `Path.cwd()`
    ignore_errors+=(PTH112)     ## PTH112 `os.path.isdir()` should be replaced by `Path.is_dir()`
    ignore_errors+=(PTH113)     ## PTH113 `os.path.isfile()` should be replaced by `Path.is_file()`
    ignore_errors+=(PTH117)     ## PTH117 `os.path.isabs()` should be replaced by `Path.is_absolute()`
    ignore_errors+=(PTH118)     ## PTH118 `os.path.join()` should be replaced by `Path` with `/` operator
    ignore_errors+=(PTH120)     ## PTH120 `os.path.dirname()` should be replaced by `Path.parent`
    ignore_errors+=(PTH122)     ## PTH122 `os.path.splitext()` should be replaced by `Path.suffix`, `Path.stem`, and `Path.parent`
    ignore_errors+=(PTH123)     ## PTH123 `open()` should be replaced by `Path.open()
    ignore_errors+=(PTH208)     ## PTH208 Use `pathlib.Path.iterdir()` instead.

    ## TODO: fix
    ignore_errors+=(N802)       ## N802 Function name `test_findName_object` should be lowercase
    ignore_errors+=(N803)       ## N803 Argument name `rePattern` should be lowercase
    ignore_errors+=(N804)       ## N804 First argument of a class method should be named `cls`
    ignore_errors+=(N806)       ## N806 Variable `testObject` in function should be lowercase
    ignore_errors+=(N815)       ## N815    [ ] mixed-case-variable-in-class-scope
    ignore_errors+=(N816)       ## N816 Variable `revCrcTmpDir` in global scope should not be mixedCase
    ignore_errors+=(LOG001)     ## LOG001 Use `logging.getLogger()` to instantiate loggers
    ignore_errors+=(DTZ001)     ## DTZ001 `datetime.datetime()` called without a `tzinfo` argument
    ignore_errors+=(DTZ002)     ## DTZ002 `datetime.datetime.today()` used
    ignore_errors+=(T201)       ## T201 `print` found
    ignore_errors+=(PTH110)     ## PTH110 `os.path.exists()` should be replaced by `Path.exists()`
    ignore_errors+=(S603)       ## S603 `subprocess` call: check for execution of untrusted input
    ignore_errors+=(S607)       ## S607 Starting a process with a partial executable path
    ignore_errors+=(COM812)     ## COM812 [*] Trailing comma missing
    ignore_errors+=(SLF001)     ## SLF001 Private member accessed: `_testMethodName`
    ignore_errors+=(FLY002)     ## FLY002 Consider f-string instead of string join
    ignore_errors+=(RET504)     ## RET504 Unnecessary assignment to `MockedDatetime` before `return` statement
    ignore_errors+=(ANN206)     ## ANN206 Missing return type annotation for classmethod `utcnow`
    ignore_errors+=(FIX002)     ## FIX002 Line contains TODO, consider resolving the issue
    ignore_errors+=(TD002)      ## TD002 Missing author in TODO; try: `# TODO(<author_name>): ...` or `# TODO @<author_name>: ...`
    ignore_errors+=(TD003)      ## TD003 Missing issue link for this TODO
    ignore_errors+=(TD004)      ## TD004 Missing colon in TODO
    ignore_errors+=(TD006)      ## TD006 [*] Invalid TODO capitalization: `todo` should be `TODO`
    ignore_errors+=(F401)       ## F401 `__init__` imported but unused; consider using `importlib.util.find_spec` to test for availability
    ignore_errors+=(SIM105)     ## SIM105 Use `contextlib.suppress(ImportError)` instead of `try`-`except`-`pass`
    ignore_errors+=(S108)       ## S108 Probable insecure usage of temporary file or directory: "/tmp/taskdialog-big.png"
    ignore_errors+=(PLR0915)    ## PLR0915 Too many statements (70 > 50)
    ignore_errors+=(TC001)      ## TC001 Move application import `hanlendar.domainmodel.local.task.LocalTask` into a type-checking block
    ignore_errors+=(RUF005)     ## RUF005 Consider `[task, *items]` instead of concatenation
    ignore_errors+=(UP006)      ## UP006 Use `list` instead of `List` for type annotation
    ignore_errors+=(EM101)      ## EM101    [ ] raw-string-in-exception
    ignore_errors+=(D105)       ## D105     [ ] undocumented-magic-method
    ignore_errors+=(PIE808)     ## PIE808   [*] unnecessary-range-start
    ignore_errors+=(FBT002)     ## FBT002   [ ] boolean-default-value-positional-argument
    ignore_errors+=(ANN205)     ## ANN205   [ ] missing-return-type-static-method
    ignore_errors+=(SIM103)     ## SIM103   [ ] needless-bool
    ignore_errors+=(TID252)     ## TID252   [ ] relative-imports
    ignore_errors+=(PGH003)     ## PGH003   [ ] blanket-type-ignore
    ignore_errors+=(UP035)      ## UP035    [ ] deprecated-import
    ignore_errors+=(BLE001)     ## BLE001   [ ] blind-except
    ignore_errors+=(PLR0911)    ## PLR0911  [ ] too-many-return-statements
    ignore_errors+=(PTH104)     ## PTH104   [ ] os-rename
    ignore_errors+=(ANN002)     ## ANN002   [ ] missing-type-args
    ignore_errors+=(C901)       ## C901     [ ] complex-structure
    ignore_errors+=(FBT003)     ## FBT003   [ ] boolean-positional-value-in-call
    ignore_errors+=(SIM108)     ## SIM108   [ ] if-else-block-instead-of-if-exp
    ignore_errors+=(D212)       ## D212     [*] multi-line-summary-first-line
    ignore_errors+=(PTH107)     ## PTH107   [ ] os-remove
    ignore_errors+=(PTH119)     ## PTH119 `os.path.basename()` should be replaced by `Path.name`
    ignore_errors+=(TRY003)     ## TRY003   [ ] raise-vanilla-args
    ignore_errors+=(D401)       ## D401     [ ] non-imperative-mood
    ignore_errors+=(EXE002)     ## EXE002   [ ] shebang-missing-executable-file
    ignore_errors+=(LOG015)     ## LOG015   [ ] root-logger-call
    ignore_errors+=(PLR0912)    ## PLR0912  [ ] too-many-branches
    ignore_errors+=(S301)       ## S301 `pickle` and modules that wrap it can be unsafe when used to deserialize untrusted data, possible security issue
    ignore_errors+=(PLW0603)    ## PLW0603 Using the global statement to update `log_file` is discouraged
    ignore_errors+=(RUF012)     ## RUF012 Mutable class attributes should be annotated with `typing.ClassVar`
    ignore_errors+=(S101)       ## S101 Use of `assert` detected
    ignore_errors+=(UP031)      ## UP031 Use format specifiers instead of percent format
    ignore_errors+=(B008)       ## B008 Do not perform function call `QColor` in argument defaults; instead, perform the call within the function, or read the default from a module-level singleton variable
    ignore_errors+=(ANN003)     ## ANN003 Missing type annotation for `**kwargs`
    ignore_errors+=(PLR1722)    ## PLR1722 Use `sys.exit()` instead of `exit`
    ignore_errors+=(TC003)      ## TC003 Move standard library import `datetime` into a type-checking block
    ignore_errors+=(UP015)      ## UP015 [*] Unnecessary mode argument
    ignore_errors+=(PTH111)     ## PTH111 `os.path.expanduser()` should be replaced by `Path.expanduser()`
    ignore_errors+=(UP015)      ## UP015 [*] Unnecessary mode argument`
    ignore_errors+=(RUF010)     ## RUF010 [*] Use explicit conversion flag
    ignore_errors+=(PGH004)     ## PGH004 Use specific rule codes when using `noqa`
    ignore_errors+=(PLR1730)    ## PLR1730 [*] Replace `if` statement with `retOffset = max(retOffset, currOffset)`
    ignore_errors+=(TRY300)     ## TRY300 Consider moving this statement to an `else` block
    ignore_errors+=(UP037)      ## UP037 [*] Remove quotes from type annotation
    ignore_errors+=(PLW1641)    ## PLW1641 Object does not implement `__hash__` method
    ignore_errors+=(SIM102)     ## SIM102 Use a single `if` statement instead of nested `if` statements
    ignore_errors+=(SIM114)     ## SIM114 [*] Combine `if` branches using logical `or` operator
    ignore_errors+=(SIM300)     ## SIM300 [*] Yoda condition detected
    ignore_errors+=(D415)       ## D415 First line should end with a period, question mark, or exclamation point
    ignore_errors+=(D403)       ## D403 [*] First word of the docstring should be capitalized: `retrun` -> `Retrun`
    ignore_errors+=(D400)       ## D400 First line should end with a period
    ignore_errors+=(PTH207)     ## PTH207 Replace `glob` with `Path.glob` or `Path.rglob`
    ignore_errors+=(SIM110)     ## SIM110 Use `return all(sub.isCompleted() is not False for sub in subitems)` instead of `for` loop
    ignore_errors+=(S110)       ## S110 `try`-`except`-`pass` detected, consider logging the exception

    ignore_string="${ignore_errors[*]}"
    ignore_string="${ignore_string//${IFS:0:1}/,}"

    if [ ${#RUFF_ARGS[@]} -ne 0 ]; then
        ruff check --select ALL --ignore "${ignore_string}" "${RUFF_ARGS[*]}"
    else
        ruff check --select ALL --ignore "${ignore_string}"
    fi

    exit_code=$?
    popd > /dev/null
    if [ $exit_code -ne 0 ]; then
        exit $exit_code
    fi
}

for dir in "${check_dirs[@]}"; do
   run_ruff "${dir}"
done

echo "ruff -- no warnings found"


echo
echo "running complexipy"
complexipy -d low -mx 70 "${check_dirs[@]}"
echo "complexipy -- no warnings found"


echo
echo "running bandit"
echo "to ignore warning for one line put following comment in end of line: # nosec"

## [B301:blacklist] Pickle and modules that wrap it can be unsafe when used to deserialize untrusted data, possible security issue.
## [B403:blacklist] Consider possible security implications associated with pickle module.
skip_list="B301,B403"

#echo "to ignore warning for one line put following comment in end of line: # nosec
# shellcheck disable=SC2086
bandit --skip "${skip_list}" -r "${check_dirs[@]}" -x "$src_dir/test*"
exit_code=$?
if [ $exit_code -ne 0 ]; then
    exit $exit_code
fi
echo "bandit -- no warnings found"


echo
req_path="$src_dir/requirements.txt"
if [ -f "$req_path" ]; then
    echo "running safety"
    safety check -r "$req_path"
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        exit $exit_code
    fi
    echo "safety -- no warnings found"
else
    echo "skipping safety - no requirements file found"
fi


## check shell scripts
echo
found_files=$(find "$src_dir/../" -not -path "*/venv/*" -not -path "*/tmp/*" -type f -name '*.sh' -o -name '*.bash')
echo "found sh files to check: $found_files"

## SC2002 (style): Useless cat. Consider 'cmd < file | ..' or 'cmd file | ..' instead.
## SC2129: Consider using { cmd1; cmd2; } >> file instead of individual redirects.
## SC2155 (warning): Declare and assign separately to avoid masking return values.
EXCLUDE_LIST="SC2002,SC2129,SC2155"

echo
echo "to suppress line warning add before the line: # shellcheck disable=<code>"
# shellcheck disable=SC2068
shellcheck -a -x --exclude "$EXCLUDE_LIST" ${found_files[@]}
echo "shellcheck -- no warnings found"

echo -e "\nall checks completed"
