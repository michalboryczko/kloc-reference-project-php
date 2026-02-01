#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

show_help() {
    echo -e "${CYAN}Contract Tests Runner${NC}"
    echo ""
    echo "Usage: bin/run.sh <command> [options]"
    echo ""
    echo "Commands:"
    echo "  test                    Run all tests (generates fresh index)"
    echo "  test --filter <name>    Run specific test by name/pattern"
    echo "  test --suite <name>     Run specific test suite"
    echo "  docs                    Generate markdown documentation"
    echo "  docs --format=json      Generate JSON documentation"
    echo "  docs --format=csv       Generate CSV documentation"
    echo "  docs --output=FILE      Write documentation to file"
    echo ""
    echo "Test suites: smoke, integrity, reference, chain, argument"
    echo ""
    echo "Examples:"
    echo "  bin/run.sh test"
    echo "  bin/run.sh test --filter testOrderRepository"
    echo "  bin/run.sh test --suite smoke"
    echo "  bin/run.sh docs"
    echo "  bin/run.sh docs --format=json --output=tests.json"
}

generate_index() {
    # Check for scip-php binary
    SCIP_PHP="${SCIP_PHP_BINARY:-../../scip-php/build/scip-php}"
    if [[ ! -x "$SCIP_PHP" ]]; then
        echo -e "${RED}Error: scip-php binary not found at: $SCIP_PHP${NC}"
        echo "Set SCIP_PHP_BINARY environment variable or build scip-php first."
        exit 1
    fi

    echo -e "${YELLOW}Generating index with scip-php...${NC}"
    mkdir -p output

    # Run scip-php on the parent project
    "$SCIP_PHP" -d ..

    # Move calls.json to output directory
    if [[ -f "calls.json" ]]; then
        mv calls.json output/
        echo -e "${GREEN}  calls.json generated${NC}"
    else
        echo -e "${RED}Error: scip-php did not generate calls.json${NC}"
        exit 1
    fi

    # Clean up other generated files
    rm -f index.scip index.kloc
}

build_docker() {
    echo -e "${YELLOW}Building Docker image...${NC}"
    docker compose build --quiet
    echo -e "${GREEN}  Docker image ready${NC}"
}

run_tests() {
    local filter="$1"
    local suite="$2"

    echo -e "${GREEN}=== Contract Tests ===${NC}"
    echo ""

    generate_index
    build_docker

    echo -e "${YELLOW}Running tests...${NC}"
    echo ""

    local cmd="vendor/bin/phpunit"
    if [[ -n "$filter" ]]; then
        cmd="$cmd --filter $filter"
    fi
    if [[ -n "$suite" ]]; then
        cmd="$cmd --testsuite=$suite"
    fi

    docker compose run --rm -e SKIP_INDEX_GENERATION=1 contract-tests $cmd

    echo ""
    echo -e "${GREEN}=== Done ===${NC}"
}

run_docs() {
    local format="$1"
    local output="$2"

    echo -e "${GREEN}=== Generate Documentation ===${NC}"
    echo ""

    generate_index
    build_docker

    echo -e "${YELLOW}Generating documentation...${NC}"
    echo ""

    local cmd="php bin/generate-docs.php"
    if [[ -n "$format" ]]; then
        cmd="$cmd --format=$format"
    fi
    if [[ -n "$output" ]]; then
        cmd="$cmd --output=$output"
    fi

    docker compose run --rm -e SKIP_INDEX_GENERATION=1 contract-tests $cmd

    echo ""
    echo -e "${GREEN}=== Done ===${NC}"
}

# Parse command
COMMAND="${1:-}"

case "$COMMAND" in
    test)
        shift
        FILTER=""
        SUITE=""
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --filter)
                    FILTER="$2"
                    shift 2
                    ;;
                --suite)
                    SUITE="$2"
                    shift 2
                    ;;
                *)
                    echo -e "${RED}Unknown option: $1${NC}"
                    show_help
                    exit 1
                    ;;
            esac
        done
        run_tests "$FILTER" "$SUITE"
        ;;
    docs)
        shift
        FORMAT=""
        OUTPUT=""
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --format=*)
                    FORMAT="${1#*=}"
                    shift
                    ;;
                --output=*)
                    OUTPUT="${1#*=}"
                    shift
                    ;;
                *)
                    echo -e "${RED}Unknown option: $1${NC}"
                    show_help
                    exit 1
                    ;;
            esac
        done
        run_docs "$FORMAT" "$OUTPUT"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        if [[ -n "$COMMAND" ]]; then
            echo -e "${RED}Unknown command: $COMMAND${NC}"
            echo ""
        fi
        show_help
        exit 1
        ;;
esac
