#!/usr/bin/env bash

# cores e ícones
green='\033[0;32m'
red='\033[0;31m'
nc='\033[0m'
success="✓"
error="✗"
tool="⚒"

echo
echo "|------------------------------------|"
echo "        INSTALAÇÃO AniTupi ${tool}        "
echo "|------------------------------------|"
echo

install_dir="$HOME/.local/share/ani-tupi"
bin_dir="$HOME/.local/bin"

# detectar gerenciador
if command -v pacman &> /dev/null; then
    pkg_mgr="sudo pacman -S --noconfirm"
    deps=("git" "python" "fzf" "mpv" "curl")
elif command -v dnf &> /dev/null; then
    pkg_mgr="sudo dnf install -y"
    deps=("git" "python3" "fzf" "mpv" "curl")
elif command -v apt &> /dev/null; then
    pkg_mgr="sudo apt update && sudo apt install -y"
    deps=("git" "python3" "python3-venv" "fzf" "mpv" "curl")
fi

missing_deps=()
for d in "${deps[@]}"; do
    if [[ "$d" == "python3-venv" ]]; then
        if ! dpkg -l | grep -q "python3-venv"; then missing_deps+=("$d"); fi
    elif ! command -v "$d" &> /dev/null; then
        missing_deps+=("$d")
    fi
done

if [ ${#missing_deps[@]} -ne 0 ]; then
    echo -e "faltam dependências de sistema: ${missing_deps[*]}"
    read -p "deseja instalar agora? (s/n): " choice
    if [[ "$choice" =~ ^[Ss]$ ]]; then
        if [ -n "$pkg_mgr" ]; then
            $pkg_mgr "${missing_deps[@]}"
        else
            echo -e "${red}${error} instale manualmente: ${missing_deps[*]}${nc}"
        fi
    fi
fi

mkdir -p "$bin_dir"

if [ -d "$install_dir" ]; then
    echo "atualizando repositório..."
    cd "$install_dir" && git pull origin python-3.14 &> /dev/null
else
    echo "clonando arquivos (branch python-3.14)..."
    git clone -b python-3.14 https://github.com/aglairdev/ani-tupi.git "$install_dir" &> /dev/null
fi

cd "$install_dir"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt &> /dev/null

chmod +x run.sh
ln -sf "$install_dir/run.sh" "$bin_dir/ani-tupi"

echo
if [[ ":$PATH:" != *":$bin_dir:"* ]]; then
    echo -e "${red}${error} atenção: $bin_dir não está no seu PATH.${nc}"
    echo -e "adicione 'export PATH=\"\$HOME/.local/bin:\$PATH\"' ao seu .bashrc ou .zshrc"
else
    echo -e "${green}${success} Instalação/Atualização concluída! Use: ani-tupi${nc}"
fi
