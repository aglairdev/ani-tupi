# Ani-Tupi: Veja animes sem sair do terminal

Assista e baixe animes diretamente pelo terminal utilizando ani-tupi, uma solução brasileira para resolver o problema de legendas em inglês propostos pelo `ani-cli` e os anúncios frequêntes em sites gratuitos de anime.

## Observações:
- Esse repositório é um fork
- Os tutoriais inferem que você está usando **linux** e que tem uma pasta chamada **repos** na pasta raíz do seu usuário, em futuras atualizações trarei suporte para **windows**

## Compilando o programa

### Pacotes necessários
- Arch linux e derivados:
```sh
sudo pacman -S git python mpv firefox --needed
```

- Debian e derivados:
```sh
sudo apt install git python3 mpv firefox
```

### Comando completo de compilação:

Muita atenção aqui, pois isso vai depender do shell que está usando

- bash/zsh:
```sh
cd ~/repos/
git clone https://github.com/luisantony103/ani-tupi
cd ani-tupi
python -m venv .venv
source ./venv/bin/activate
pip install -r requirements.txt
./build.sh
```
- fish:
```sh
cd ~/repos/
git clone https://github.com/luisantony103/ani-tupi
cd ani-tupi
python -m venv .venv
source ./venv/bin/activate.fish
pip install -r requirements.txt
./build.sh
```

você vai encontrar o executável em `./dist/ani-tupi`, caso ache pertinente pode deixar nos diretórios que estão listados no `$PATH`, como por exemplo:

```sh
sudo mv ./dist/ani-tupi /usr/local/bin
```



## Repositório fork de:
[eduardonery1/ani-tupi](https://github.com/eduardonery1/ani-tupi)

