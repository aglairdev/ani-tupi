import loader, argparse
from repository import rep
from loader import PluginInterface
from sys import exit
import sys, os
from json import load, dump, JSONDecodeError
from manga_tupi import main as manga_tupi
from os import name, remove
from pathlib import Path
import shutil, requests
import subprocess, time
import ui_system
from python_mpv_jsonipc import MPV, MPVError
from rich.live import Live
from rich.panel import Panel
import logging

### logs e caminhos
HISTORY_PATH = Path.home().as_posix() + "/.local/state/ani-tupi/" if name != 'nt' else "C:\\Program Files\\ani-tupi\\"
HISTORY_FILE = Path(HISTORY_PATH) / "history.json"
LOG_FILE = Path(HISTORY_PATH) / "ani-tupi.log"

def setup_silence(debug_mode: bool):
    logging.getLogger("selenium").setLevel(logging.CRITICAL)
    logging.getLogger("urllib3").setLevel(logging.CRITICAL)
    if not debug_mode:
        if not LOG_FILE.parent.exists():
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        sys.stderr = open(LOG_FILE, "a", encoding="utf-8")

def seconds_to_hms(seconds):
    if seconds is None: seconds = 0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def manage_history_clean(target: str):
    ### lógica de limpeza com saída imediata para evitar duplicação
    if not HISTORY_FILE.exists():
        ui_system.print_log("Histórico vazio", "ERROR", "red")
        os._exit(0)
    if target.lower() == "all":
        remove(HISTORY_FILE)
        ui_system.print_log("Você removeu todo histórico", "INFO", "green")
        os._exit(0)
    else:
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = load(f)
            keys = list(data.keys())
            idx = int(target) - 1
            if 0 <= idx < len(keys):
                removed_anime = keys[idx]
                del data[removed_anime]
                with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                    dump(data, f, indent=4)
                ui_system.print_log(f"Você removeu: {removed_anime}", "INFO", "green")
            else:
                ui_system.print_log("ID inválido", "ERROR", "red")
        except:
            ui_system.print_log("Use um ID numérico ou 'all'", "ERROR", "red")
    os._exit(0)

def main(args : argparse.Namespace) -> None:
    loader.load_plugins({"pt-br"}, None)

    if not args.continue_watching:
        query = ui_system.create_prompt("Pesquisar animes", "Coloque o nome do anime e pressione Enter") if not args.anime else args.anime
        ui_system.print_log("Buscando anime", "INFO", "green")

        rep.search_anime(query)
        titles = rep.get_anime_titles()
        selected_anime = ui_system.create_fzf_menu(titles, msg="Escolha o Anime: ")
        selected_anime = selected_anime.split(" - ")[0]

        rep.search_episodes(selected_anime)
        episode_list = rep.get_episode_list(selected_anime)

        if not args.download:
            selected_episode : str = ui_system.create_fzf_menu(episode_list, msg="Escolha o episódio: ")
            episode_idx : int = episode_list.index(selected_episode)
            timestamp = 0
    else:
        selected_anime, episode_idx, timestamp = load_history(args.debug)
        if selected_anime is None:
            return

    num_episodes = len(rep.anime_episodes_urls[selected_anime][0][0])

    if args.download:
        return download_anime(selected_anime, rep.anime_episodes_urls[selected_anime][0][0], args.range, args.debug)

    while True:
        try:
            episode : int = episode_idx + 1
            ui_system.print_log(f"Carregando EP{episode} | Pressione 'q' para fechar o player", "INFO", "green")

            player_url : str = rep.search_player(selected_anime, episode)
            if not player_url:
                ui_system.print_log(f"Erro ao obter link do EP{episode}", "ERROR", "red")
                break

            video_player = MPV()
            video_player.play(player_url)
            video_player.wait_for_property("time-pos")

            if timestamp >= 1:
                video_player.seek(timestamp, "absolute")

            with Live(refresh_per_second=4) as live:
                while video_player.eof_reached == False:
                    try:
                        current_pos = video_player.time_pos
                        if current_pos is not None:
                            timestamp = current_pos

                        duration = video_player.duration if video_player.duration is not None else 0
                        conteúdo = f"Episódio {episode}: [bold cyan]{seconds_to_hms(timestamp)}/{seconds_to_hms(duration)}[/]"
                        live.update(Panel(conteúdo, title="Status do Player"))
                        time.sleep(0.25)
                    except (MPVError, BrokenPipeError, IndexError):
                        break

            video_player.terminate()

        ### silenciado pra não poluir o terminal antes de você escolher o que fazer
        except (MPVError, BrokenPipeError, IndexError):
            pass
        except Exception as e:
            ui_system.print_log(f"Erro no player: {type(e).__name__}", "ERROR", "red")

        save_history(selected_anime, episode_idx, args.debug, timestamp)

        opts = ["Marcar como assistido e sair"]
        if episode_idx < num_episodes - 1: opts.append("Próximo")
        if episode_idx > 0: opts.append("Anterior")

        ### se o usuário fechar o fzf, o os._exit(0) lá no ui_system já mata tudo por aqui
        selected_opt = ui_system.create_fzf_menu(opts, msg="O que quer fazer agora? > ", return_null_when_stopped=True)
        timestamp = 0

        if selected_opt == "Próximo":
            episode_idx += 1
        elif selected_opt == "Anterior":
            episode_idx -= 1
        else:
            ### saída limpa pra marcar como assistido ou só fechar o loop
            ui_system.exit_program()

def download_anime(selected_anime, episode_list, download_range, debug):
    if download_range:
        episode_list = filter_list_based_in_rangetype(download_range, episode_list)
    root_path = ui_system.create_prompt("Diretório", "Caminho (padrão: ~/Videos/)")
    videos_path = Path(root_path).expanduser() if root_path != "" else Path("~/Videos/").expanduser()
    if not videos_path.is_dir(): videos_path = Path.home() / "Videos"
    anime_path = videos_path / selected_anime
    if anime_path.is_dir():
        choice = ui_system.create_prompt("Existe", "Excluir ou Parar?")
        if choice.lower() == "excluir": shutil.rmtree(anime_path)
        else: return
    anime_path.mkdir(parents=True, exist_ok=True)
    for i, _ in enumerate(episode_list, start=1):
        ui_system.print_log(f"Baixando EP{i}", "INFO", "white")
        url = rep.search_player(selected_anime, i)
        download_episode(url, anime_path, f"Episódio {i}", debug)

def download_episode(player_url, anime_path, name, debug):
    episode_path = anime_path / (name + ".mp4")
    try: subprocess.run(["yt-dlp", "-f", "mp4", player_url, "--output", episode_path], check=True)
    except: ui_system.print_log("Falha no download", "ERROR", "red")

def load_history(debug):
    if not HISTORY_FILE.exists():
        ui_system.print_log("Histórico vazio", "ERROR", "red")
        os._exit(0)
    try:
        with HISTORY_FILE.open("r", encoding="utf-8") as f: data = load(f)
        if not data:
            ui_system.print_log("Histórico vazio", "ERROR", "red")
            os._exit(0)

        titles = {}
        for i, (anime, info) in enumerate(data.items(), start=1):
            ep_n, ts, urls = info["episode"]["number"], info["episode"]["timestamp"], info["urls"]
            dub_tag = " (Dublado)" if "dublado" in anime.lower() else ""
            clean_name = anime.replace(" (Dublado)", "").replace(" (Legendado)", "")
            label = f"[{i}] {clean_name}{dub_tag} - EP {ep_n + 1:02d} - ({seconds_to_hms(ts)})"
            titles[label] = (anime, ep_n, ts, urls)

        selected = ui_system.create_fzf_menu(list(titles.keys()), msg="Continuar assistindo: ")
        if not selected: return None, None, None
        anime, ep_idx, ts, urls = titles[selected]
        rep.anime_episodes_urls[anime] = urls
        return anime, ep_idx, ts
    except:
        os._exit(0)

def save_history(anime, episode, debug, timestamp=0):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = load(open(HISTORY_FILE, "r")) if HISTORY_FILE.exists() else {}
        data[anime] = {"episode": {"number": episode, "timestamp": timestamp}, "urls": rep.anime_episodes_urls[anime]}
        dump(data, open(HISTORY_FILE, "w"), indent=4)
    except Exception as e:
        if debug: print(f"Erro ao salvar histórico: {e}")

def filter_list_based_in_rangetype(rangetype, x_list):
    return [ep for x, ep in enumerate(x_list) if rangetype[0]-1 <= x <= rangetype[1]-1]

def recognize_rangetype(rangestr):
    try:
        r = [int(i) for i in rangestr.split("-")]
        if r[0] <= r[1]: return r
    except: pass
    raise argparse.ArgumentTypeError("Use 'inicio-fim'")

### ponto de entrada do script
if __name__=="__main__":
    parser = argparse.ArgumentParser(prog="ani-tupi")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--continue_watching", "-c", action="store_true")
    parser.add_argument("--clean", "-l", type=str)
    parser.add_argument("--manga", "-m", action="store_true")
    parser.add_argument("anime", nargs="?")
    parser.add_argument("--download", "-d", action="store_true")
    parser.add_argument("--range", "-r", type=recognize_rangetype)
    args = parser.parse_args()
    setup_silence(args.debug)
    try:
        if args.clean: manage_history_clean(args.clean)
        elif args.manga: manga_tupi()
        else: main(args)
        ### garante a mensagem de saída
        ui_system.exit_program()
    except (KeyboardInterrupt, SystemExit):
        ui_system.exit_program()
