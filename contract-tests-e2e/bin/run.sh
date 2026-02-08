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
    echo -e "${CYAN}E2E Integration Tests Runner${NC}"
    echo ""
    echo "Usage: bin/run.sh <command> [options]"
    echo ""
    echo "Commands:"
    echo "  test                    Run all E2E tests"
    echo "  test --filter <name>    Run specific test by name/pattern"
    echo "  test --suite <name>     Run specific test suite/category"
    echo "  docs                    Generate markdown documentation"
    echo "  docs --format=json      Generate JSON documentation"
    echo "  docs --output=FILE      Write documentation to file"
    echo "  help                    Show this help"
    echo ""
    echo "Test suites: pipeline, usages, deps, inheritance, context"
    echo ""
    echo "Examples:"
    echo "  bin/run.sh test"
    echo "  bin/run.sh test --filter test_pipeline"
    echo "  bin/run.sh test --suite usages"
    echo "  bin/run.sh docs"
    echo ""
    echo "Prerequisites:"
    echo "  - Docker must be running"
    echo "  - scip-php Docker image must be built (cd scip-php && ./build/build.sh)"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is required but not installed.${NC}"
        echo "Install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! docker info &> /dev/null 2>&1; then
        echo -e "${RED}Error: Docker is not running.${NC}"
        echo "Start Docker and try again."
        exit 1
    fi
}

check_scip_php_image() {
    if ! docker image inspect scip-php >/dev/null 2>&1; then
        echo -e "${RED}Error: scip-php Docker image not found.${NC}"
        echo "Build it first: cd scip-php && ./build/build.sh"
        exit 1
    fi
}

build_docker() {
    echo -e "${YELLOW}Building Docker image...${NC}"
    docker compose build --quiet 2>/dev/null || docker-compose build --quiet
    echo -e "${GREEN}  Docker image ready${NC}"
}

run_tests() {
    local filter="$1"
    local suite="$2"

    echo -e "${GREEN}=== E2E Integration Tests ===${NC}"
    echo ""

    check_docker
    check_scip_php_image
    build_docker

    echo -e "${YELLOW}Running tests...${NC}"
    echo ""

    local cmd="pytest -v --tb=short"
    if [[ -n "$filter" ]]; then
        cmd="$cmd -k $filter"
    fi
    if [[ -n "$suite" ]]; then
        cmd="$cmd -m $suite"
    fi

    # Add JUnit XML output
    cmd="$cmd --junitxml=output/junit.xml"

    docker compose run --rm contract-tests-e2e $cmd 2>/dev/null \
        || docker-compose run --rm contract-tests-e2e $cmd

    echo ""
    echo -e "${GREEN}=== Done ===${NC}"
}

run_docs() {
    local format="$1"
    local output="$2"

    echo -e "${GREEN}=== Generate Documentation ===${NC}"
    echo ""

    check_docker
    build_docker

    echo -e "${YELLOW}Generating documentation...${NC}"
    echo ""

    local cmd="python bin/generate-docs.py"
    if [[ -n "$format" ]]; then
        cmd="$cmd --format=$format"
    fi
    if [[ -n "$output" ]]; then
        cmd="$cmd --output=$output"
    fi

    docker compose run --rm contract-tests-e2e $cmd 2>/dev/null \
        || docker-compose run --rm contract-tests-e2e $cmd

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
        shift || true
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
