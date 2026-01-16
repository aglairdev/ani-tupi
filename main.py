import loader
import argparse
from menu import menu
from repository import rep
from loader import PluginInterface
from sys import exit
from video_player import play_video
from json import load, dump
from manga_tupi import main as manga_tupi
from os import name
from pathlib import Path
import shutil
import subprocess
import requests
import ui_system


HISTORY_PATH = Path.home().as_posix() + "/.local/state/ani-tupi/" if name != 'nt' else "C:\\Program Files\\ani-tupi\\"

def main(args):
    loader.load_plugins({"pt-br"}, None if not args.debug else ["animefire"])

    if not args.continue_watching:
        query = (ui_system.create_prompt("Nome do anime", "Digite o nome do anime e pressione Enter.") if args.anime == None else args.anime) if not args.debug else "eva"    
        rep.search_anime(query)
        titles = rep.get_anime_titles()
        selected_anime = ui_system.create_fzf_menu(titles, msg="Escolha o Anime: ")

        selected_anime = selected_anime.split(" - ")[0]

        rep.search_episodes(selected_anime)
        episode_list = rep.get_episode_list(selected_anime)
        
        if not args.download:
            selected_episode = ui_system.create_fzf_menu(episode_list, msg="Escolha o episódio: ")
            episode_idx = episode_list.index(selected_episode) 
    else:
        selected_anime, episode_idx = load_history()
    
    num_episodes = len(rep.anime_episodes_urls[selected_anime][0][0])
    
    if args.download:
        return download_anime(selected_anime, rep.anime_episodes_urls[selected_anime][0][0], args.range)
    while True:
        episode = episode_idx + 1
        player_url = rep.search_player(selected_anime, episode)
        if args.debug: print(player_url)
        play_video(player_url, args.debug)
        save_history(selected_anime, episode_idx)

        opts = []
        if episode_idx < num_episodes - 1:
            opts.append("Próximo")
        if episode_idx > 0:
            opts.append("Anterior")

        selected_opt = menu(opts, msg="O que quer fazer agora?")

        if selected_opt == "Próximo":
            episode_idx += 1 
        elif selected_opt == "Anterior":
            episode_idx -= 1
def download_anime(selected_anime,episode_list,download_range):
    print(episode_list)
    if download_range != None:
        episode_list = filter_list_based_in_rangetype(to_rangetype(download_range),episode_list)
    print(episode_list)

    videos_path = input("Determine diretório de destino para o anime (padrão: ~/Videos/): ")
    videos_path = Path(videos_path).expanduser() if not videos_path != "" else Path("~/Videos/").expanduser()
    if not videos_path.is_dir():
        print("Não é uma pasta, usando diretório padrão")
        videos_path = Path.home() / "Videos"
    print(f"Criando pasta '{selected_anime}'")

    anime_path = videos_path / selected_anime
    anime_path.mkdir()
    
    for i,episode in enumerate(episode_list,start=1):
        print(f"baixando episódio {i}")
        player_url = rep.search_player(selected_anime, i)

        download_episode(player_url, anime_path, f"Episódio {i}")

def download_episode(player_url, anime_path, name):
    episode_path = anime_path / (name + ".mp4")
    # verificar o tipo do link (stream ou vídeo)
  
    response = requests.get(player_url)
    content_type = response.headers.get("content-type")
    if not content_type =="video/mp4":
        subprocess.run([
            "yt-dlp", 
            "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]", 
            player_url, 
            "--output", episode_path.as_posix()
            ])
    else:
        subprocess.run([
            "ffmpeg",
            "-i", player_url,
            "-c", "copy",
            episode_path.as_posix()
            ])


def load_history():
    file_path = HISTORY_PATH + "history.json"
    try:
        with open(file_path, "r") as f:
            data = load(f)
            titles = dict()
            for entry, info in data.items():
                ep_info = f" (Ultimo episódio assistido {info[1] + 1})"
                titles[entry + ep_info] = len(ep_info)
            selected = menu(list(titles.keys()), msg="Continue assistindo.")
            anime = selected[:-titles[selected]]
            episode_idx = data[anime][1]
            rep.anime_episodes_urls[anime] = data[anime][0]
        return anime, episode_idx
    except FileNotFoundError:
        print("Sem histórico de animes")
        exit()
    except PermissionError:
        print("Sem permissão para ler arquivos.")
        return

def save_history(anime, episode):
    file_path = HISTORY_PATH + "history.json"
    try:
        with open(file_path, "r+") as f:
            data = load(f)
            data[anime] = [rep.anime_episodes_urls[anime],
                           episode]
        with open(file_path , "w") as f:
            dump(data, f)

    except FileNotFoundError:
        Path(file_path).mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            data = dict()
            data[anime] = [rep.anime_episodes_urls[anime],
                            episode]
            dump(data, f)

    except PermissionError:
        print("Não há permissão para criar arquivos.")
        return

def recognize_rangetype(rangestr):
    range_list = rangestr.split("-")
    try:
        min_val = int(range_list[0])
        max_val = int(range_list[1])
        if min_val > max_val:
            raise Exception("Valor mínimo maior que o máximo!")
    except Exception:
        raise argparse.ArgumentTypeError("Range está incorreto. O certo é 'começo-fim' (exemplo: '10-20', '1-12', etc)")

def to_rangetype(rangestr):
    range_list = rangestr.split("-")
    return [int(range_list[0]),int(rangelist[1])]

def filter_list_based_in_rangetype(rangetype,x_list):
    return [x for x in x_list if rangetype[0] <= x <= rangetype[1]]

def recognize_rangetype(rangestr):
    range_list = rangestr.split("-")
    try:
        min_val = int(range_list[0])
        max_val = int(range_list[1])
        if min_val > max_val:
            raise Exception("Valor mínimo maior que o máximo!")
    except Exception:
        raise argparse.ArgumentTypeError("Range está incorreto. O certo é 'começo-fim' (exemplo: '10-20', '1-12', etc)")

def to_rangetype(rangestr):
    range_list = rangestr.split("-")
    return [int(range_list[0]),int(rangelist[1])]

def filter_list_based_in_rangetype(rangetype,x_list):
    return [x for x in x_list if rangetype[0] <= x <= rangetype[1]]

if __name__=="__main__":
    parser = argparse.ArgumentParser(
                prog = "ani-tupi",
                description="Veja anime sem sair do terminal.",
            )
    parser.add_argument("--debug", action="store_true", help="Modo de desenvolvedores")
    parser.add_argument("--continue_watching", "-c", action="store_true", help="Continuar assistindo")
    parser.add_argument("--manga", "-m", action="store_true", help="Usa o manga_tupi para abrir mangás")
    parser.add_argument("anime", type=str, nargs="?", help="nome do anime com aspas")
    parser.add_argument("--download", "-d", action="store_true", help="Ativa modo de download")
    parser.add_argument("--range", "-r", type=recognize_rangetype, help="Intervalos de episódios a serem baixados ('1-10', '5-12', etc)")
    args = parser.parse_args()
    
    try: 
        if args.manga:
            manga_tupi()
        else:
            main(args)
    except KeyboardInterrupt:
        ui_system.print_log("Interrompido pelo usuário. Abortando...", "ABORT", "red")
        exit(0)
     
