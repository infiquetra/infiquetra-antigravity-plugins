#!/usr/bin/env bash
#
# install-plugin.sh - Install or uninstall VECU Antigravity plugins
#
# Usage: 
#   ./tools/install-plugin.sh list                  - List all available and installed plugins
#   ./tools/install-plugin.sh install <plugin-id>   - Install a specific plugin (via symlink)
#   ./tools/install-plugin.sh install-all           - Install all plugins from the repository
#   ./tools/install-plugin.sh uninstall <plugin-id> - Uninstall a specific plugin
#   ./tools/install-plugin.sh uninstall-all         - Uninstall all plugins in the repository
#

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
RESET='\033[0m'

# Helpers
print_success() {
    echo -e "${GREEN}✓${RESET} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${RESET} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${RESET} $1"
}

print_error() {
    echo -e "${RED}✗${RESET} $1"
}

print_header() {
    echo -e "\n${BOLD}$1${RESET}\n"
}

# Directories
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANTIGRAVITY_PLUGINS_DIR="$HOME/.gemini/config/plugins"

# Ensure antigravity plugin directory exists
mkdir -p "$ANTIGRAVITY_PLUGINS_DIR"

list_plugins() {
    print_header "🔌 VECU Antigravity Plugins Status"
    
    printf "%-25s %-12s %-12s %s\n" "Plugin ID" "Available" "Installed" "Type"
    printf "%-25s %-12s %-12s %s\n" "---------" "---------" "---------" "----"
    
    # Get sorted union of local plugins and installed plugins
    local -A all_plugins
    
    if [ -d "$REPO_ROOT/plugins" ]; then
        for p in "$REPO_ROOT/plugins"/*; do
            if [ -d "$p" ]; then
                local p_id
                p_id=$(basename "$p")
                all_plugins["$p_id"]=1
            fi
        done
    fi
    
    for p in "$ANTIGRAVITY_PLUGINS_DIR"/*; do
        if [ -d "$p" ] || [ -L "$p" ]; then
            local p_id
            p_id=$(basename "$p")
            all_plugins["$p_id"]=1
        fi
    done
    
    # Sort and print
    for p_id in $(echo "${!all_plugins[@]}" | tr ' ' '\n' | sort); do
        local available="No"
        local installed="No"
        local type="Unknown"
        
        # Check availability in repo
        if [ -d "$REPO_ROOT/plugins/$p_id" ]; then
            available="Yes"
            # Detect type
            if [ -d "$REPO_ROOT/plugins/$p_id/skills" ] && [ -d "$REPO_ROOT/plugins/$p_id/commands" ]; then
                type="CLI-based"
            elif [ -d "$REPO_ROOT/plugins/$p_id/skills" ]; then
                type="Skills-based"
            else
                type="Generic"
            fi
        fi
        
        # Check installation in Antigravity dir
        if [ -L "$ANTIGRAVITY_PLUGINS_DIR/$p_id" ]; then
            installed="${GREEN}Yes (Link)${RESET}"
        elif [ -d "$ANTIGRAVITY_PLUGINS_DIR/$p_id" ]; then
            installed="${YELLOW}Yes (Copy)${RESET}"
        fi
        
        if [ "$available" = "Yes" ] || [[ "$installed" =~ "Yes" ]]; then
            printf "%-25s %-12s %-12s %s\n" "$p_id" "$available" "$installed" "$type"
        fi
    done
    echo ""
}

install_plugin() {
    local p_id="$1"
    local src="$REPO_ROOT/plugins/$p_id"
    local dest="$ANTIGRAVITY_PLUGINS_DIR/$p_id"
    
    if [ ! -d "$src" ]; then
        print_error "Plugin '$p_id' not found in $REPO_ROOT/plugins"
        exit 1
    fi
    
    if [ -L "$dest" ]; then
        print_warning "Plugin '$p_id' is already symlinked. Re-linking..."
        rm "$dest"
    elif [ -d "$dest" ]; then
        print_warning "A directory exists at destination '$dest'. Backing up to '${dest}.bak'..."
        mv "$dest" "${dest}.bak"
    fi
    
    ln -s "$src" "$dest"
    print_success "Installed '$p_id' successfully as a symlink!"
    print_info "Next time you start an Antigravity session, '$p_id' will be loaded."
}

uninstall_plugin() {
    local p_id="$1"
    local dest="$ANTIGRAVITY_PLUGINS_DIR/$p_id"
    
    if [ -L "$dest" ]; then
        rm "$dest"
        print_success "Uninstalled symlinked plugin '$p_id'"
    elif [ -d "$dest" ]; then
        print_warning "Plugin '$p_id' is a directory copy, not a symlink. Removing directory..."
        rm -rf "$dest"
        print_success "Removed plugin folder '$p_id'"
    else
        print_error "Plugin '$p_id' is not installed in $ANTIGRAVITY_PLUGINS_DIR"
    fi
}

install_all() {
    print_header "📦 Installing all plugins from repo..."
    for p in "$REPO_ROOT/plugins"/*; do
        if [ -d "$p" ]; then
            local p_id
            p_id=$(basename "$p")
            install_plugin "$p_id"
        fi
    done
    print_success "All plugins installed successfully!"
}

uninstall_all() {
    print_header "🗑️ Uninstalling all repo plugins..."
    for p in "$REPO_ROOT/plugins"/*; do
        if [ -d "$p" ]; then
            local p_id
            p_id=$(basename "$p")
            local dest="$ANTIGRAVITY_PLUGINS_DIR/$p_id"
            if [ -L "$dest" ] || [ -d "$dest" ]; then
                uninstall_plugin "$p_id"
            fi
        fi
    done
    print_success "All plugins uninstalled successfully!"
}

# Main routing
CMD="${1:-list}"

case "$CMD" in
    list)
        list_plugins
        ;;
    install)
        if [ $# -lt 2 ]; then
            print_error "Missing plugin ID: ./tools/install-plugin.sh install <plugin-id>"
            exit 1
        fi
        install_plugin "$2"
        ;;
    install-all)
        install_all
        ;;
    uninstall)
        if [ $# -lt 2 ]; then
            print_error "Missing plugin ID: ./tools/install-plugin.sh uninstall <plugin-id>"
            exit 1
        fi
        uninstall_plugin "$2"
        ;;
    uninstall-all)
        uninstall_all
        ;;
    *)
        print_error "Unknown command: $CMD"
        echo "Usage:"
        echo "  $0 list"
        echo "  $0 install <plugin-id>"
        echo "  $0 install-all"
        echo "  $0 uninstall <plugin-id>"
        echo "  $0 uninstall-all"
        exit 1
        ;;
esac
