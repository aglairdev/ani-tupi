import loader, argparse
from repository import rep
from loader import PluginInterface
from sys import exit
from json import load, dump, JSONDecodeError
from manga_tupi import main as manga_tupi
from os import name
from pathlib import Path
import shutil, requests
import subprocess, time
import ui_system
from python_mpv_jsonipc import MPV, MPVError
from rich.live import Live
from rich.panel import Panel

def seconds_to_hms(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"



HISTORY_PATH = Path.home().as_posix() + "/.local/state/ani-tupi/" if name != 'nt' else "C:\\Program Files\\ani-tupi\\"

def player_log_handler(text : str) -> None:
    ui_system.print_log(args, "DEBUG", "gray")

def main(args : argparse.Namespace) -> None:
    loader.load_plugins({"pt-br"}, None)

    # Busca anime / Procura do histórico
    if not args.continue_watching:
        query = ui_system.create_prompt("Pesquisar animes", "coloque o nome do anime e pressione Enter") if not args.anime else args.anime
        rep.search_anime(query)
        titles = rep.get_anime_titles()
        selected_anime = ui_system.create_fzf_menu(titles, msg="Escolha o Anime.")

        selected_anime = selected_anime.split(" - ")[0]

        rep.search_episodes(selected_anime)
        episode_list = rep.get_episode_list(selected_anime)


        if not args.download:
            selected_episode : str = ui_system.create_fzf_menu(episode_list, msg="Escolha o episódio: ") if not args.continue_watching else None
            episode_idx : int = episode_list.index(selected_episode)
            timestamp = 0  
    else:
        selected_anime, episode_idx, timestamp = load_history(args.debug)
    
    num_episodes = len(rep.anime_episodes_urls[selected_anime][0][0])

    num_episodes : int = len(rep.anime_episodes_urls[selected_anime][0][0])
    

    # Começa processo de download se usuário pedir

    if args.download:
        return download_anime(selected_anime, rep.anime_episodes_urls[selected_anime][0][0], args.range, args.debug)



    # Loop para tocar os videos
    
    while True:
        video_player = MPV()

        episode : int = episode_idx + 1
        player_url : str = rep.search_player(selected_anime, episode)

        if args.debug: ui_system.print_log(f"URL encontrada: {player_url}", "DEBUG", "gray")        

        video_player.play(player_url)
        video_player.wait_for_property("time-pos")
        
        if timestamp >= 1:
            video_player.seek(timestamp, "absolute")

        with Live(refresh_per_second=4) as live:
            pool_observer = 0
            while video_player.eof_reached == False:
                try:
                    # Atualizando status
                    timestamp = video_player.time_pos if video_player.time_pos is not None else timestamp
                    duration = video_player.duration if video_player.duration is not None else 0

                    conteúdo = f"Episódio {episode} tocando: [bold cyan]{seconds_to_hms(timestamp)}/{seconds_to_hms(duration)}s[/]"
                    pool_observer += 1
                    if pool_observer >= 100:
                        live.update(Panel(conteúdo, title="Status do Player"))
                        pool_observer = 0
                except Exception as err:
                    if args.debug: ui_system.print_log(str(err.args), "DEBUG", "gray")
                    break


        opts = ["Marcar como assistido e sair"]
        if episode_idx < num_episodes - 1:
            opts.append("Próximo")
        if episode_idx > 0:
            opts.append("Anterior")

        selected_opt : str = ui_system.create_fzf_menu(opts, msg="O que quer fazer agora? > ", return_null_when_stopped=True)

        save_history(selected_anime, episode_idx, args.debug, timestamp)
        timestamp = 0

        if selected_opt == "Próximo":
            episode_idx += 1 
        elif selected_opt == "Anterior":
            episode_idx -= 1
        elif selected_opt == "Marcar como assistido e sair":
            save_history(selected_anime, episode_idx + (1 if "Proximo" in opts else 0), args.debug)
            break
        else:
            break


def download_anime(selected_anime : str,episode_list : list[str],download_range : list[int] | None, debug : bool) -> None:
    if debug: ui_system.print_log(f"Verificando uso de Range: {download_range}", "DEBUG", "gray")
    if download_range:
        if debug: ui_system.print_log(f"Aplicando range {download_range}", "DEBUG", "gray")
        episode_list = filter_list_based_in_rangetype(download_range,episode_list)
        if debug: ui_system.print_log(f"nova lista de episódios: {episode_list}", "DEBUG", "gray")
    
    root_path : str = ui_system.create_prompt("Diretório do episódio", "Determine o diretório raíz para o episódio (padrão: ~/Videos/)")
    videos_path : Path = Path(root_path).expanduser() if root_path != ""  else Path("~/Videos/").expanduser()

    if debug: ui_system.print_log(f"Arquivo raíz: {videos_path.as_posix()}", "DEBUG", "gray")

    if not videos_path.is_dir():
        ui_system.print_log("Não é uma pasta, usando diretório padrão", "WARN", "yellow")
        videos_path = Path.home() / "Videos"

    anime_path : Path = videos_path / selected_anime
    if debug: ui_system.print_log(f"Criando pasta '{anime_path.as_posix()}'", "DEBUG", "gray")

    if anime_path.is_dir():
        choice : str = ui_system.create_prompt("Anime já baixado", "O anime possívelmente já foi baixado, deseja *excluir* a pasta ou *parar* o processo?")

        if choice.lower() == "excluir":
            shutil.rmtree(anime_path.as_posix())
        elif choice.lower() == "parar":
            raise KeyboardInterrupt()
        else:
            raise KeyboardInterrupt()

    anime_path.mkdir()

    for i,episode in enumerate(episode_list,start=1):
        ui_system.print_log(f"baixando episódio {i}", "INFO", "white")
        player_url : str = rep.search_player(selected_anime, i)
        download_episode(player_url, anime_path, f"Episódio {i}", debug)

def download_episode(player_url : str, anime_path : Path, name : str, debug : bool) -> None:
    episode_path : Path = anime_path / (name + ".mp4")
    # verificar o tipo do link (stream ou vídeo)
    if debug: ui_system.print_log(f"Fazendo request em {player_url}", "DEBUG", "gray")
    response : requests.Response = requests.get(player_url)
    content_type : str = response.headers.get("content-type")
    if debug: ui_system.print_log(f"Content-Type: {content_type.split(';')}", "DEBUG", "gray")
    try:
        if not content_type.split(";")[0] == "video/mp4":
            if debug: ui_system.print_log(f"Processando com yt_dlp", "DEBUG", "gray")
            process : subprocess.CompletedProcess = subprocess.run([
            "yt-dlp", 
            "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]", 
            player_url, 
            "--output", episode_path.as_posix()
            ])
            process.check_returncode()
        else:
            if debug: ui_system.print_log(f"Processando com FFmpeg", "DEBUG", "gray")
            process : subprocess.CompletedProcess =subprocess.run([
            "ffmpeg",
            "-i", player_url,
            "-c", "copy",
            episode_path.as_posix()
            ])
            process.check_returncode()
    except FileNotFoundError:
        ui_system.print_log("FFmpeg e yt_dlp não encontrados no $PATH, você baixou eles?", "ERRO", "red")
        exit(1)
    except subprocess.CalledProcessError:
        ui_system.print_log("Houve um erro durante o processo de download do episódio", "ERRO", "red")
        exit(1)
        decide : str = input("Deseja abortar o programa? (S/n)")
        if not decide.lower() == "n":
            raise KeyboardInterrupt() 

from json import load, JSONDecodeError
from pathlib import Path

def load_history(debug: bool):
    file_path = Path(HISTORY_PATH) / "history.json"

    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = load(f)
    except FileNotFoundError:
        ui_system.print_log(
            "Sem histórico de animes, assista ao menos um para criar histórico.",
            "ERRO",
            "red"
        )
        return None, None, None
    except JSONDecodeError as e:
        if debug:
            ui_system.print_log(f"JSON inválido: {e}", "DEBUG", "gray")
        ui_system.print_log(
            f"Histórico corrompido: {file_path.as_posix()}",
            "ERRO",
            "red"
        )
        return None, None, None
    except PermissionError:
        ui_system.print_log(
            f"Sem permissão para ler {file_path.as_posix()}",
            "ERRO",
            "red"
        )
        return None, None, None

    if not isinstance(data, dict):
        ui_system.print_log(
            "Histórico inválido: formato raiz não é dict",
            "ERRO",
            "red"
        )
        return None, None, None

    titles = {}
    index_map = {}

    for anime, info in data.items():
        try:
            ep_number = info["episode"]["number"]
            timestamp = info["episode"]["timestamp"]
            urls = info["urls"]
        except (KeyError, TypeError):
            ui_system.print_log(
                    f"Entrada inválida ignorada no histórico: {anime}",
                    "ERRO",
                    "red"
                )
            continue

        ep_info = f" - Último episódio assistido {ep_number + 1} ({seconds_to_hms(timestamp)})"
        label = anime + ep_info

        titles[label] = len(ep_info)
        index_map[label] = (anime, ep_number, timestamp, urls)

    if not titles:
        ui_system.print_log(
            "Histórico vazio ou sem entradas válidas.",
            "ERRO",
            "red"
        )
        return None, None, None

    selected = ui_system.create_fzf_menu(
        list(titles.keys()),
        msg="Continue assistindo."
    )

    anime, episode_idx, timestamp, urls = index_map[selected]

    rep.anime_episodes_urls[anime] = urls

    return anime, episode_idx, timestamp

def save_history(anime : str, episode : int, debug : bool, timestamp=0) -> None:
    file_path = Path(HISTORY_PATH) / "history.json"

    if not file_path.is_file():
       file_path.parent.mkdir(parents=True, exist_ok=True)
       file_path.touch()

    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = load(f)
    except JSONDecodeError as error:
        if debug: ui_system.print_log(f"Houve um erro de Decodificação de JSON: {error.msg}", "DEBUG", "gray")
        
        data = {}
    except PermissionError:
        ui_system.print_log(f"Não foi possível salvar o histórico: Sem permissão para ler {file_path.as_posix()}", "ERROR", "red")
        return

    data[anime] = {"episode": {"number": episode, "timestamp": timestamp}, "urls": rep.anime_episodes_urls[anime]}

    try:
        with file_path.open("w", encoding="utf-8") as f:
            dump(data,f, indent=4)
    except PermissionError:
        print(f"Não foi possível salvar o histórico: Sem permissão para escrever {file_path.as_posix()}")


def to_rangetype(rangestr : str) -> list[int]:
    range_list = rangestr.split("-")
    return [int(range_list[0]),int(range_list[1])]

def filter_list_based_in_rangetype(rangetype : list[int],x_list : list) -> list:
    return [episode for x, episode in enumerate(x_list,start=0) if rangetype[0]-1 <= x <= rangetype[1]-1]

def recognize_rangetype(rangestr : str) -> list[int]:
    range_list = rangestr.split("-")
    try:
        min_val = int(range_list[0])
        max_val = int(range_list[1])
        if min_val > max_val:
            raise Exception("Valor mínimo maior que o máximo!")
    except Exception:
        raise argparse.ArgumentTypeError("Range está incorreto. O certo é 'começo-fim' (exemplo: '10-20', '1-12', etc)")

    return to_rangetype(rangestr)

def filter_non_dubbed_anime_list(anime_list : list[str]) -> list[str]:
    pass

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
    parser.add_argument("--dubbed", "-dub", action="store_true")
    args = parser.parse_args()
    
    if args.debug:ui_system.print_log(f"Argumentos: {str(args)}", "DEBUG", "gray")

    try: 
        if args.manga:
            manga_tupi()
        else:
            main(args)
    except KeyboardInterrupt:
        ui_system.console.print()
        ui_system.print_log("Interrompido pelo usuário. Abortando...", "ABORT", "red")
        exit(0)
     
