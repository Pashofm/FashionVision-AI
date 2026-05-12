#!/bin/bash
# FashionVision-AI - Common Version Management Functions
# Handles Python and Node.js version detection and installation

set -euo pipefail

REQUIRED_PYTHON_MAJOR=3
REQUIRED_PYTHON_MINOR_MIN=10
REQUIRED_PYTHON_MINOR_MAX=12
REQUIRED_NODE_MAJOR=18

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

check_python_ctypes() {
    local pybin="$1"
    local GREEN='\033[0;32m'
    local YELLOW='\033[1;33m'
    local RED='\033[0;31m'
    local NC='\033[0m'

    if [ -z "$pybin" ] || [ ! -f "$pybin" ]; then
        echo -e "${RED}ERROR: Invalid Python binary: $pybin${NC}"
        return 1
    fi

    if "$pybin" -c "import _ctypes" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

show_system_deps_warning() {
    local GREEN='\033[0;32m'
    local YELLOW='\033[1;33m'
    local RED='\033[0;31m'
    local NC='\033[0m'

    echo ""
    echo -e "${RED}=============================================="
    echo -e "  ERROR: Missing System Dependencies"
    echo -e "==============================================${NC}"
    echo ""
    echo -e "${YELLOW}Your Python installation is missing the '_ctypes' module, which is required"
    echo -e "for packages like torch, cryptography, and other compiled extensions.${NC}"
    echo ""
    echo "This usually happens when Python was compiled without libffi-dev installed."
    echo ""
    echo -e "${GREEN}To fix this, run the following commands:${NC}"
    echo ""
    echo "  # Step 1: Install system dependencies (requires sudo password)"
    echo -e "  ${YELLOW}sudo apt-get update && sudo apt-get install -y libffi-dev python3-dev build-essential libjpeg-dev${NC}"
    echo ""
    echo "  # Step 2: Remove the broken Python 3.12 installation"
    echo -e "  ${YELLOW}rm -rf ~/.pyenv/versions/3.12.0${NC}"
    echo ""
    echo "  # Step 3: Reinstall Python 3.12 (pyenv will now compile with libffi)"
    echo -e "  ${YELLOW}~/.pyenv/bin/pyenv install 3.12.0${NC}"
    echo ""
    echo "  # Step 4: Remove old venv and rerun setup"
    echo -e "  ${YELLOW}rm -rf <PROJECT_ROOT>/backend/venv${NC}"
    echo -e "  ${YELLOW}./scripts/setup.sh${NC}"
    echo ""
    echo -e "${RED}After completing these steps, run './scripts/setup.sh' again.${NC}"
    echo ""
}

check_python_version() {
    if ! command_exists python3 && ! command_exists python; then
        return 1
    fi

    local pycmd=""
    if command_exists python3; then
        pycmd="python3"
    else
        pycmd="python"
    fi

    local version=$("$pycmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
    if [ -z "$version" ]; then
        return 1
    fi

    local major=$(echo "$version" | cut -d. -f1)
    local minor=$(echo "$version" | cut -d. -f2)

    if [ "$major" -eq "$REQUIRED_PYTHON_MAJOR" ] && \
       [ "$minor" -ge "$REQUIRED_PYTHON_MINOR_MIN" ] && \
       [ "$minor" -le "$REQUIRED_PYTHON_MINOR_MAX" ]; then
        echo "$pycmd"
        return 0
    fi

    return 1
}

get_python_binary() {
    local pybin=""

    if [ -f "/usr/bin/python3.12" ]; then
        pybin="/usr/bin/python3.12"
    elif [ -f "/usr/bin/python3.11" ]; then
        pybin="/usr/bin/python3.11"
    elif [ -f "/usr/bin/python3.10" ]; then
        pybin="/usr/bin/python3.10"
    elif command_exists python3; then
        pybin="python3"
    elif command_exists python; then
        pybin="python"
    fi

    echo "$pybin"
}

get_system_python_info() {
    local pycmd=""
    if command_exists python3; then
        pycmd="python3"
    elif command_exists python; then
        pycmd="python"
    else
        echo "none"
        return
    fi

    local version=$("$pycmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
    local major=$(echo "$version" | cut -d. -f1)
    local minor=$(echo "$version" | cut -d. -f2)

    echo "${major}.${minor}|$(which "$pycmd")"
}

install_pyenv() {
    echo "Installing pyenv..."

    if [ -d "$HOME/.pyenv" ]; then
        echo "pyenv already installed at ~/.pyenv"
        return 0
    fi

    if command_exists git; then
        git clone https://github.com/pyenv/pyenv.git "$HOME/.pyenv" 2>/dev/null
    elif command_exists curl; then
        curl -s https://pyenv.run | bash
    else
        echo "ERROR: git or curl required to install pyenv"
        return 1
    fi

    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"

    if [ -f "$HOME/.pyenv/bin/pyenv" ]; then
        eval "$(pyenv init - bash 2>/dev/null)" || true
        echo "pyenv installed successfully"
        return 0
    fi

    echo "ERROR: pyenv installation failed"
    return 1
}

install_python_via_pyenv() {
    local version="${1:-3.12.0}"

    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"

    eval "$(pyenv init - bash 2>/dev/null)" || true

    if pyenv versions 2>/dev/null | grep -q "^  $version"; then
        echo "Python $version already installed"
    else
        echo "Installing Python $version via pyenv (this may take a few minutes)..."
        CONFIGURE_OPTS="--enable-shared" pyenv install "$version" 2>/dev/null || {
            echo "ERROR: Failed to install Python $version"
            return 1
        }
    fi

    pyenv global "$version" 2>/dev/null || true

    local pyenv_python="$PYENV_ROOT/versions/$version/bin/python"
    if [ -f "$pyenv_python" ]; then
        echo "Python $version installed at $pyenv_python"
        return 0
    fi

    echo "ERROR: Python installation verification failed"
    return 1
}

setup_python_environment() {
    local GREEN='\033[0;32m'
    local YELLOW='\033[1;33m'
    local RED='\033[0;31m'
    local NC='\033[0m'

    echo -e "${GREEN}Checking Python environment...${NC}"

    local existing_py=$(check_python_version)
    if [ -n "$existing_py" ]; then
        echo -e "${GREEN}Found compatible Python at: $(which "$existing_py")${NC}"
        return 0
    fi

    local sys_info=$(get_system_python_info)
    local sys_python=$(echo "$sys_info" | cut -d'|' -f2)
    local sys_version=$(echo "$sys_info" | cut -d'|' -f1)

    if [ "$sys_version" != "none" ]; then
        echo -e "${YELLOW}System Python $sys_version at $sys_python is too new (max supported: 3.12)${NC}"
        echo -e "${YELLOW}Installing Python 3.12 via pyenv...${NC}"
    else
        echo -e "${YELLOW}No compatible Python found (need 3.10-3.12).${NC}"
    fi

    if [ ! -d "$HOME/.pyenv" ]; then
        install_pyenv || {
            echo -e "${RED}ERROR: Failed to install pyenv${NC}"
            return 1
        }
    fi

    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init - bash 2>/dev/null)" || true

    install_python_via_pyenv "3.12.0" || {
        echo "Trying Python 3.11..."
        install_python_via_pyenv "3.11.0" || {
            echo "Trying Python 3.10..."
            install_python_via_pyenv "3.10.0" || {
                echo -e "${RED}ERROR: Could not install any compatible Python version${NC}"
                return 1
            }
        }
    }

    export PYENV_ROOT="$HOME/.pyenv"
    if [ -d "$PYENV_ROOT/versions/3.12.0" ]; then
        local pyenv_python="$PYENV_ROOT/versions/3.12.0/bin/python3"
        if ! check_python_ctypes "$pyenv_python"; then
            show_system_deps_warning
            return 1
        fi
    elif [ -d "$PYENV_ROOT/versions/3.11.0" ]; then
        local pyenv_python="$PYENV_ROOT/versions/3.11.0/bin/python3"
        if ! check_python_ctypes "$pyenv_python"; then
            show_system_deps_warning
            return 1
        fi
    elif [ -d "$PYENV_ROOT/versions/3.10.0" ]; then
        local pyenv_python="$PYENV_ROOT/versions/3.10.0/bin/python3"
        if ! check_python_ctypes "$pyenv_python"; then
            show_system_deps_warning
            return 1
        fi
    fi

    return 0
}

check_node_version() {
    if ! command_exists node; then
        return 1
    fi

    local version=$(node -v 2>/dev/null | tr -d 'v')
    if [ -z "$version" ]; then
        return 1
    fi

    local major=$(echo "$version" | cut -d. -f1)

    if [ "$major" -ge "$REQUIRED_NODE_MAJOR" ]; then
        echo "node"
        return 0
    fi

    return 1
}

install_nvm() {
    echo "Installing nvm..."

    if [ -d "$HOME/.nvm" ]; then
        echo "nvm already installed at ~/.nvm"
        return 0
    fi

    if command_exists curl; then
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash 2>/dev/null
    elif command_exists wget; then
        wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash 2>/dev/null
    else
        echo "ERROR: curl or wget required to install nvm"
        return 1
    fi

    export NVM_DIR="$HOME/.nvm"
    if [ -s "$NVM_DIR/nvm.sh" ]; then
        echo "nvm installed successfully"
        return 0
    fi

    echo "ERROR: nvm installation failed"
    return 1
}

install_node_via_nvm() {
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

    if nvm ls-remote 2>/dev/null | grep -q "v${REQUIRED_NODE_MAJOR}"; then
        echo "Installing Node.js ${REQUIRED_NODE_MAJOR}.x LTS via nvm..."
        nvm install "${REQUIRED_NODE_MAJOR}" --lts 2>/dev/null || {
            echo "ERROR: Failed to install Node.js"
            return 1
        }
        nvm use "${REQUIRED_NODE_MAJOR}" 2>/dev/null || nvm alias default "${REQUIRED_NODE_MAJOR}" 2>/dev/null || true
        return 0
    fi

    echo "ERROR: Could not find Node.js ${REQUIRED_NODE_MAJOR} for installation"
    return 1
}

setup_node_environment() {
    local GREEN='\033[0;32m'
    local YELLOW='\033[1;33m'
    local RED='\033[0;31m'
    local NC='\033[0m'

    echo -e "${GREEN}Checking Node.js environment...${NC}"

    local existing_node=$(check_node_version)
    if [ -n "$existing_node" ]; then
        echo -e "${GREEN}Found compatible Node.js at: $(which "$existing_node")${NC}"
        return 0
    fi

    echo -e "${YELLOW}No compatible Node.js found (need 18+).${NC}"

    if [ ! -d "$HOME/.nvm" ]; then
        install_nvm || {
            echo -e "${RED}ERROR: Failed to install nvm${NC}"
            return 1
        }
    fi

    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

    install_node_via_nvm
}

ensure_python_venv() {
    local project_root="$1"
    local backend_dir="$project_root/backend"
    local GREEN='\033[0;32m'
    local YELLOW='\033[1;33m'
    local RED='\033[0;31m'
    local NC='\033[0m'

    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init - bash 2>/dev/null)" || true

    local venv_python=""
    local needs_recreate=false

    if [ -d "$PYENV_ROOT/versions/3.12.0" ]; then
        venv_python="$PYENV_ROOT/versions/3.12.0/bin/python3"
    elif [ -d "$PYENV_ROOT/versions/3.11.0" ]; then
        venv_python="$PYENV_ROOT/versions/3.11.0/bin/python3"
    elif [ -d "$PYENV_ROOT/versions/3.10.0" ]; then
        venv_python="$PYENV_ROOT/versions/3.10.0/bin/python3"
    fi

    if [ -z "$venv_python" ] && command_exists python3; then
        local sys_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
        local sys_major=$(echo "$sys_version" | cut -d. -f1)
        local sys_minor=$(echo "$sys_version" | cut -d. -f2)

        if [ "$sys_major" -eq 3 ] && [ "$sys_minor" -gt "$REQUIRED_PYTHON_MINOR_MAX" ]; then
            echo -e "${YELLOW}System Python $sys_version is too new for this project.${NC}"
            echo -e "${YELLOW}Recreating venv with Python 3.12 from pyenv...${NC}"
            needs_recreate=true

            if [ ! -d "$PYENV_ROOT/versions/3.12.0" ]; then
                echo "Installing Python 3.12 via pyenv..."
                install_python_via_pyenv "3.12.0" || {
                    echo -e "${RED}ERROR: Failed to install Python 3.12${NC}"
                    return 1
                }
            fi
            venv_python="$PYENV_ROOT/versions/3.12.0/bin/python3"
        elif command_exists python3; then
            venv_python="python3"
        fi
    fi

    if [ -z "$venv_python" ]; then
        echo -e "${RED}ERROR: No Python found to create venv${NC}"
        return 1
    fi

    if [ -n "$venv_python" ] && [ -f "$venv_python" ]; then
        if ! check_python_ctypes "$venv_python"; then
            show_system_deps_warning
            return 1
        fi
    fi

    echo -e "${GREEN}Using Python: $("$venv_python" --version 2>&1)${NC}"

    if [ -d "$backend_dir/venv" ]; then
        local venv_version=$("$backend_dir/venv/bin/python" --version 2>&1 | awk '{print $2}')
        local venv_major=$(echo "$venv_version" | cut -d. -f1)
        local venv_minor=$(echo "$venv_version" | cut -d. -f2)

        if [ "$venv_major" -eq 3 ] && [ "$venv_minor" -gt "$REQUIRED_PYTHON_MINOR_MAX" ]; then
            echo -e "${YELLOW}Existing venv uses Python $venv_version (too new). Recreating...${NC}"
            needs_recreate=true
        fi
    fi

    if [ "$needs_recreate" = true ] || [ ! -d "$backend_dir/venv" ]; then
        if [ -d "$backend_dir/venv" ]; then
            rm -rf "$backend_dir/venv"
        fi
        echo "Creating Python virtual environment..."
        "$venv_python" -m venv "$backend_dir/venv" 2>&1 || {
            echo -e "${RED}ERROR: Failed to create venv${NC}"
            return 1
        }
    fi

    if [ ! -f "$backend_dir/venv/bin/pip" ]; then
        echo -e "${YELLOW}Recreating venv (pip not found)...${NC}"
        rm -rf "$backend_dir/venv"
        "$venv_python" -m venv "$backend_dir/venv" 2>&1 || {
            echo -e "${RED}ERROR: Failed to create venv${NC}"
            return 1
        }
    fi

    echo -e "${GREEN}Python virtual environment ready${NC}"
    return 0
}

ensure_node_deps() {
    local project_root="$1"
    local GREEN='\033[0;32m'
    local YELLOW='\033[1;33m'
    local RED='\033[0;31m'
    local NC='\033[0m'

    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

    if [ ! -d "$project_root/frontend/node_modules" ]; then
        echo -e "${YELLOW}Installing frontend dependencies...${NC}"
        cd "$project_root/frontend"
        npm install 2>&1 || {
            echo -e "${RED}ERROR: npm install failed${NC}"
            return 1
        }
        cd "$project_root"
    fi

    echo -e "${GREEN}Frontend dependencies ready${NC}"
    return 0
}