import socket, json, subprocess, time
from pathlib import Path
import ui_system

class MPV:
    def __init__(self, debug=False):
        self.socket = Path("/tmp/mpv.sock")
        self.debug = debug

        self.mpv_idle_command = [
            "mpv",
            "--idle=yes",
            "--no-terminal",
            f"--input-ipc-server={self.socket.as_posix()}"
        ]

        if not self._mpv_alive():
            if debug: ui_system.print_log("Iniciando mpv em modo idle", "DEBUG", "gray")
            
            try:
                subprocess.Popen(self.mpv_idle_command)
            except FileNotFoundError:
                ui_system.print_log("MPV: MPV não encontrado em $PATH", "CRITICAL", "black on red")
                exit(1)
            
            self._wait_for_socket()

    def wait_until_loaded(self):
        while True:
            resp = self.get_property("filename")
            resp2 = self.get_property("time-pos")
            ui_system.print_log("MPV: Esperando propriedades filename e time-pos existirem", "DEBUG", "gray")
            if resp is not None and resp2 is not None:
                break
            time.sleep(.5)


    def _wait_for_socket(self, timeout=10):
        start = time.time()
        while time.time() - start < timeout:
            if self._mpv_alive():
                return
            time.sleep(0.1)
        raise RuntimeError("mpv não respondeu via IPC")

    def _mpv_alive(self):
        try:
            s = socket.socket(socket.AF_UNIX)
            s.connect(str(self.socket))
            s.sendall(json.dumps({"command": ["get_property", "idle-active"]}).encode() + b"\n")
            s.close()
            return True
        except ConnectionRefusedError:
            return False

    def _send(self, cmd):
        try:
            s = socket.socket(socket.AF_UNIX)
            s.connect(str(self.socket))
            s.sendall(json.dumps(cmd).encode() + b"\n")
            s.close()
        except ConnectionRefusedError:
            ui_system.print_log("MPV: Conexão de IPC recusada, o MPV parou de rodar?", "ERROR", "red")
            

    def command(self, cmd):
        self._send(cmd)

    def play(self, path, timestamp=0):
        try:
            self.command({
            "command": ["loadfile", path, "replace"]
            })

            if timestamp > 0:
                self.wait_until_loaded()

            self.command({
                    "command": ["seek", timestamp, "absolute"]
            })
            self.command({
            "command": ["set_property", "pause", False]
            })
        except ConnectionRefusedError:
            ui_system.print_log("MPV: Conexão de IPC recusada, o MPV parou de rodar?", "ERROR", "red")
        
    
    def force_quit(self):
        try:
            self.command({"command": ["quit"]})
            return
        except Exception:
            pass

        # fallback brutal
        subprocess.run(
            ["pkill", "-TERM", "-f", "mpv --input-ipc-server=/tmp/mpv.sock"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def get_property(self, prop):
        try:
            s = socket.socket(socket.AF_UNIX)
            s.connect(self.socket.as_posix())
            s.sendall(json.dumps({
                "command": ["get_property", prop]
            }).encode() + b"\n")
            data = s.recv(4096)
            s.close()
            # pega só a primeira linha JSON
            first_line = data.decode().splitlines()[0]
            return json.loads(first_line).get("data")
        except ConnectionRefusedError:
            ui_system.print_log("MPV: Conexão de IPC recusada, o MPV parou de rodar?", "ERROR", "red")
        except Exception as err:
            if self.debug: ui_system.print_log(str(err.args), "CRITICAL", "black on red")
            exit(1)

    def next(self):
        self.command({"command": ["playlist-next"]})

    def previous(self):
        self.command({"command": ["playlist-prev"]})

    def pause(self):
        self.command({"command": ["cycle", "pause"]})
