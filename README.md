# Ani-Tupi: Veja animes sem sair do terminal 🇧🇷

## Demo

[demo-anitupi](https://github.com/user-attachments/assets/56ddf231-4974-41ff-9b3d-425aaed5ca72)

## Sobre

Alternativa ao [ani-cli](https://github.com/pystardust/ani-cli) e [goanime](https://github.com/alvarorichard/GoAnime), com foco em conteúdo pt-BR.

## Updates

- **Gestão de histórico**:  Permite deletar entradas específicas por ID ou resetar todo o histórico
- **Feedbacks**: Mensagens claras para cada ação realizada (sucesso, erro ou avisos)
- **Instalação simplificada**: Script que configura o ambiente, instala dependências e cria o comando global automaticamente


## Dependências

git python3 mpv firefox yt-dlp ffmpeg fzf curl


## Instalação

```bash
curl -sSL https://raw.githubusercontent.com/aglairdev/ani-tupi/python-3.14/install.sh | bash
```

## Execução

```bash
ani-tupi
```

### Atalhos

`-c` ou `--continue_watching`: Abre o menu para retomar o anime de onde você parou (carrega o episódio e o tempo exato).

`--clean [ID]` ou `-l [ID]`: Remove um anime específico do seu histórico pelo número do ID.

`--clean all` ou `-l all`: Apaga todo o seu histórico de uma vez.

`"nome do anime" -d` ou `"nome do anime" --download`: Inicia o modo de download para o anime pesquisado.

`-d -r 1-10` ou `--download --range 1-10`: Baixa apenas o intervalo de episódios escolhido (ex: do 1 ao 10).

`-m` ou `--manga` : Ativa o modo manga-tupi para leitura de mangás no terminal e realiza download.

`--debug`: Ativa os logs de desenvolvedor para ver detalhes técnicos e erros ocultos.

`-h` ou `--help`: Exibe todos os comandos.

## Créditos

- Baseado no trabalho original de: [eduardonery1](https://github.com/eduardonery1)
- Melhorias de infraestrutura por: [luisAntony103](https://github.com/luisAntony103)
