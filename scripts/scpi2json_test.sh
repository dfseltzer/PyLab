#!/usr/bin/env bash
#
# Enhanced test script for scpi2json_cli.py
#
# Usage:
#   ./test_scpi2json.sh <test-number> [<pdf-file>]
#
# Examples:
#   ./test_scpi2json.sh 1                   # Run only Test 1 on default test manual
#   ./test_scpi2json.sh all manual.pdf      # Run all tests on specified manual
#

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/scpi2json.py"

if [ $# -lt 1 ]; then
    echo "Usage: $0 [<pdf-file> optional] <test-number>"
    echo "Example: $0 manual.pdf 2"
    exit 1
fi

TEST="$1"
PDF_FILE="${2:-./"$(dirname "$0")"/ProgrammingManual_BK8616.pdf}"

run_test_1() {
    echo "==================================================="
    echo " Test 1: Basic conversion with interactive page input"
    echo "==================================================="
    python3 "$PYTHON_SCRIPT" "$PDF_FILE"
}

run_test_2() {
    echo "==================================================="
    echo " Test 2: Non-interactive run with explicit pages"
    echo "==================================================="
    python3 "$PYTHON_SCRIPT" "$PDF_FILE" -p "26-74" -o output_commands.json --no-review
}

run_test_3() {
    echo "==================================================="
    echo " Test 3: Using a smaller chunk size to force more LLM requests"
    echo "==================================================="
    python3 "$PYTHON_SCRIPT" "$PDF_FILE" -p "26-74" --max-chars-per-chunk 1000
}

run_test_4() {
    echo "==================================================="
    echo " Test 4: Full run with review disabled (batch mode)"
    echo "==================================================="
    python3 "$PYTHON_SCRIPT" "$PDF_FILE" -p "26-74" --no-review -o batch_commands.json
}

# --- Test selection logic ---

if [[ "$TEST" == "1" ]]; then
    run_test_1
elif [[ "$TEST" == "2" ]]; then
    run_test_2
elif [[ "$TEST" == "3" ]]; then
    run_test_3
elif [[ "$TEST" == "4" ]]; then
    run_test_4
elif [[ "$TEST" == "all" ]]; then
    run_test_1
    run_test_2
    run_test_3
    run_test_4

    echo ""
    echo "==================================================="
    echo " All tests complete."
    echo "==================================================="
else
    echo "Unknown test number: $TEST"
    echo "Valid options: 1, 2, 3, 4, all"
    exit 1
fi
