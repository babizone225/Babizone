"""Babizone - réseau : sockets TCP non bloquants, messages JSON, codes d'invitation.

Modèle : l'hôte fait tourner toute la simulation, les amis lui envoient leurs
commandes (déplacement, tir, visée) et reçoivent des instantanés ~30 fois / s.
"""
import json
import select
import socket
import struct
import threading
import urllib.request

PORT = 50505
MAX_FRIENDS = 3
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"      # sans 0/O/1/I pour éviter les confusions


# ---------------------------------------------------------------------------
#  Codes d'invitation  (IP + port  <->  "XXXXX-XXXXX")
# ---------------------------------------------------------------------------
def encode_code(ip, port=PORT):
    n = 0
    for part in ip.split("."):
        n = n * 256 + int(part)
    n = n * 65536 + port
    chars = []
    for _ in range(10):
        chars.append(_ALPHABET[n & 31])
        n >>= 5
    code = "".join(reversed(chars))
    return code[:5] + "-" + code[5:]


def decode_code(code):
    c = "".join(ch for ch in code.upper() if ch in _ALPHABET)
    if len(c) != 10:
        return None
    n = 0
    for ch in c:
        n = n * 32 + _ALPHABET.index(ch)
    port = n & 0xFFFF
    n >>= 16
    return ".".join(str((n >> s) & 255) for s in (24, 16, 8, 0)), port


def parse_target(text):
    """Accepte un code 'XXXXX-XXXXX', une IP 'a.b.c.d' ou 'a.b.c.d:port'."""
    text = text.strip()
    if not text:
        return None
    if "." in text:
        host, _, p = text.partition(":")
        return host.strip(), int(p) if p.strip().isdigit() else PORT
    return decode_code(text)


def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))          # aucun paquet n'est envoyé
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def all_local_ips():
    """Toutes les adresses IPv4 de ce PC (Wi-Fi, mais aussi VPN : Radmin 26.x, Tailscale 100.x...)."""
    ips = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith("127.") and not ip.startswith("169.254.") and ip not in ips:
                ips.append(ip)
    except OSError:
        pass
    return ips


class PublicIP:
    """Récupère l'IP publique en arrière-plan (sans bloquer le jeu)."""

    def __init__(self):
        self.ip = None
        self.done = False
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            with urllib.request.urlopen("https://api.ipify.org", timeout=3) as r:
                txt = r.read().decode().strip()
            socket.inet_aton(txt)
            self.ip = txt
        except Exception:
            self.ip = None
        self.done = True


# ---------------------------------------------------------------------------
#  Connexion avec messages "longueur + JSON"
# ---------------------------------------------------------------------------
class Conn:
    def __init__(self, sock):
        self.sock = sock
        self.sock.settimeout(0.5)
        try:
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError:
            pass
        self.buf = b""
        self.closed = False

    def send(self, obj):
        if self.closed:
            return
        data = json.dumps(obj, separators=(",", ":")).encode("utf-8")
        try:
            self.sock.sendall(struct.pack(">I", len(data)) + data)
        except OSError:
            self.closed = True

    def poll(self):
        """Retourne la liste des messages reçus depuis le dernier appel."""
        msgs = []
        if self.closed:
            return msgs
        try:
            for _ in range(32):
                ready, _, _ = select.select([self.sock], [], [], 0)
                if not ready:
                    break
                chunk = self.sock.recv(65536)
                if not chunk:
                    self.closed = True
                    break
                self.buf += chunk
        except OSError:
            self.closed = True
        while len(self.buf) >= 4:
            n = struct.unpack(">I", self.buf[:4])[0]
            if n > 5_000_000:
                self.closed = True
                break
            if len(self.buf) < 4 + n:
                break
            payload, self.buf = self.buf[4:4 + n], self.buf[4 + n:]
            try:
                msgs.append(json.loads(payload))
            except ValueError:
                pass
        return msgs

    def close(self):
        self.closed = True
        try:
            self.sock.close()
        except OSError:
            pass


class Host:
    def __init__(self, port=PORT):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", port))
        self.sock.listen(8)
        self.sock.setblocking(False)
        self.port = port

    def accept(self):
        new = []
        while True:
            ready, _, _ = select.select([self.sock], [], [], 0)
            if not ready:
                break
            try:
                s, _addr = self.sock.accept()
            except OSError:
                break
            new.append(Conn(s))
        return new

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


def connect(ip, port, timeout=4.0):
    s = socket.create_connection((ip, port), timeout=timeout)
    return Conn(s)
