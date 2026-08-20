#!/bin/bash
set -e

print_banner() {
    cat <<'BANNER'
  __  __      _ ____              _
 |  \/  | ___| | ___   _ _ __ ___| |__   ___ _ __ ___
 | |\/| |/ _ \ | | | | | | '__/ __| '_ \ / _ \ '__/ __|
 | |  | |  __/ | | |_| | | | | (__| | | |  __/ |  \__ \
 |_|  |_|\___|_|_|\__,_|_|_|  \___|_| |_|\___|_|  |___/

                    Uninstaller
BANNER
}

print_banner

if [ -n "$TERMUX_VERSION" ] || [ -d "/data/data/com.termux/files/usr" ]; then
    BIN_DIR="${PREFIX:-/data/data/com.termux/files/usr}/bin"
    SHARE_DIR="${PREFIX:-/data/data/com.termux/files/usr}/share/metaclean"
else
    BIN_DIR="$HOME/.local/bin"
    SHARE_DIR="$HOME/.local/share/metaclean"
fi

REMOVED=0

if [ -f "$BIN_DIR/metaclean" ]; then
    rm -f "$BIN_DIR/metaclean"
    echo "[+] Removed $BIN_DIR/metaclean"
    REMOVED=1
fi

if [ -d "$SHARE_DIR" ]; then
    rm -rf "$SHARE_DIR"
    echo "[+] Removed $SHARE_DIR"
    REMOVED=1
fi

for rc_file in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile" "$HOME/.bash_profile" "$HOME/.config/fish/config.fish"; do
    if [ -f "$rc_file" ] && grep -qF "MetaClean installer" "$rc_file"; then
        if command -v sed >/dev/null 2>&1; then
            sed -i '/# Added by MetaClean installer/d; /\/.local\/bin:$PATH/d; /set -gx PATH.*\.local\/bin/d' "$rc_file" 2>/dev/null || true
            echo "[+] Cleaned MetaClean entries from $rc_file"
        fi
    fi
done

if [ "$REMOVED" -eq 0 ]; then
    echo "[!] No MetaClean installation found in $BIN_DIR or $SHARE_DIR"
    exit 1
fi

echo
echo "=============================================="
echo "  MetaClean uninstalled."
echo "=============================================="
echo
echo "Open a new terminal to refresh your PATH."
