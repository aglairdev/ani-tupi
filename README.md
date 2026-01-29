# Ani-Tupi: Veja animes sem sair do terminal 🇧🇷
Esse repositório é um fork de: [luisAntony103/ani-tupi](https://github.com/luisAntony103/ani-tupi)

## Dependências
- Arch linux e derivados:
```sh
sudo pacman -S git python mpv firefox yt-dlp ffmpeg fzf --needed
```
- Debian e derivados:
```sh
sudo apt install git python3 mpv firefox yt-dlp ffmpeg fzf
```

## Compilação
bash/zsh:
```sh
git clone https://github.com/luisAntony103/ani-tupi
cd ani-tupi
python -m venv .venv
source ./venv/bin/activate  # fish: source ./venv/bin/activate.fish 
pip install -r requirements.txt
./build.sh
```

O executável fica em `./dist/ani-tupi`. Para rodar de qualquer lugar, coloque-o em um diretório do `$PATH`, por exemplo:

```sh 
sudo mv ./dist/ani-tupi /usr/local/bin
```

Depois, reinicie o terminal.

## Execução

```sh 
ani-tupi
```
