#!/usr/bin/env python3
import pexpect
import time
import os
import math
import re
import sys
import datetime
import threading

# Créer un nom de fichier log avec suffixe HH_MM
LOG_FILENAME = f"2otns_log_{datetime.datetime.now().strftime('%H_%M')}.txt"

class TeeLogger:
    def __init__(self, file_obj, filter_patterns=None):
        self.file_obj = file_obj
        # Vous pouvez ajouter ici des motifs regex pour filtrer certaines lignes.
        # Par exemple, pour ignorer les lignes contenant "[Envoi]" ou "[Réponse]", utilisez :
        # filter_patterns = [r"\[Envoi\]", r"\[Réponse\]"]
        self.filter_patterns = filter_patterns or []

    def write(self, data):
        # Si data est en bytes, le décoder en utf-8
        if isinstance(data, bytes):
            data = data.decode("utf-8", errors="replace")
        # Préfixer chaque ligne avec un timestamp
        lines = data.splitlines(keepends=True)
        for line in lines:
            # Filtrage optionnel : si la ligne correspond à l'un des motifs à filtrer, on la saute
            skip = False
            for pattern in self.filter_patterns:
                if re.search(pattern, line):
                    skip = True
                    break
            if skip:
                continue
            ts = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
            sys.__stdout__.write(ts + line)
            self.file_obj.write(ts + line)

    def flush(self):
        sys.__stdout__.flush()
        self.file_obj.flush()

def send_cmd(proc, cmd, wait=0.5):
    """Envoie une commande à OTNS, affiche la commande, attend le prompt '>' et renvoie la sortie."""
    print(f"\n[Envoi] {cmd}")
    proc.sendline(cmd)
    proc.expect('>')
    time.sleep(wait)
    output = proc.before
    print(f"[Réponse] {output}")
    return output

def generate_row_topology(proc, row_y, num_routers, fed_total, delta_x,
                          pattern_first=None, pattern_intermediate=None, pattern_last=None):
    """
    Génère une ligne de routeurs à la coordonnée y donnée.
    Pour chaque router, selon sa position (premier, intermédiaire ou dernier),
    ajoute des end_devices selon le pattern fourni (None = pas d'end_devices).
    Chaque end_device est placé sur un cercle de rayon fixe (radius = 150)
    autour du routeur, avec un angle = 2π * position / fed_total.
    """
    radius = 150
    for i in range(num_routers):
        center_x = 500 + i * delta_x
        center_y = row_y
        send_cmd(proc, f"add router x {center_x} y {center_y}")
        if i == 0:
            fed_positions = pattern_first
        elif i == num_routers - 1:
            fed_positions = pattern_last
        else:
            fed_positions = pattern_intermediate
        if fed_positions is None:
            continue
        for pos in fed_positions:
            angle = 2 * math.pi * pos / fed_total
            fed_x = int(center_x + radius * math.cos(angle))
            fed_y = int(center_y + radius * math.sin(angle))
            send_cmd(proc, f"add fed x {fed_x} y {fed_y}")

def get_node_ipaddr(proc):
    """
    Exécute la commande ipaddr et renvoie la liste des adresses IPv6 extraites.
    Ici, nous récupérons uniquement les adresses commençant par "fdde:ad00:beef:0:" suivies de 4 groupes de 1 à 4 chiffres hexadécimaux.
    """
    output = send_cmd(proc, "ipaddr", wait=1)
    pattern = r"(fdde:ad00:beef:0:(?:[0-9A-Fa-f]{1,4}:){3}[0-9A-Fa-f]{1,4})"
    addrs = re.findall(pattern, output)
    return addrs

def ping_async(proc, addr, size, count, interval):
    """
    Envoie une commande ping async avec les paramètres donnés.
    Syntaxe : ping async <addr> <size> <count> <interval>
    """
    cmd = f"ping async {addr} {size} {count} {interval}"
    return send_cmd(proc, cmd, wait=2)

def reader_thread(proc):
    """Fonction exécutée dans un thread pour lire en continu la sortie du processus."""
    while True:
        try:
            data = proc.read_nonblocking(size=1024, timeout=1)
            if data:
                sys.__stdout__.write(data)
                sys.__stdout__.flush()
        except pexpect.TIMEOUT:
            continue
        except pexpect.EOF:
            break

def main():
    os.chdir(os.path.expanduser("~/otns"))
    # Ouvrir le fichier de log en mode écrasement (ou "a" pour append)
    with open(LOG_FILENAME, "w") as log_file:
        # Optionnel : ajouter ici les motifs à filtrer dans le log. Exemple :
        # filter_patterns = [r"\[Envoi\]", r"\[Réponse\]"]
        filter_patterns = []  # Laissez vide si vous ne souhaitez pas filtrer
        tee = TeeLogger(log_file, filter_patterns)
        sys.stdout = tee  # Redirige les prints vers le TeeLogger

        print("Starting OTNS...")
        # Lancer OTNS en mode debug et rediriger la sortie vers notre TeeLogger
        proc = pexpect.spawn('otns -log debug', encoding='utf-8', timeout=30)
        proc.logfile = tee
        proc.expect('>')

        # Lancer un thread pour lire en continu la sortie du processus
        rt = threading.Thread(target=reader_thread, args=(proc,), daemon=True)
        rt.start()

        # Génération de la topologie (une seule ligne ici)
        num_routers = 3
        fed_total = 6
        delta_x = 150
        base_y = 250
        generate_row_topology(proc,
                              row_y=base_y,
                              num_routers=num_routers,
                              fed_total=fed_total,
                              delta_x=delta_x,
                              pattern_first=[1,2,3,4,5],
                              pattern_intermediate=[1,5],
                              pattern_last=[1,5])
        print("Topologie générée.")
        time.sleep(5)  # Laisser le temps aux nœuds d'être créés

        # Récupération et affichage des adresses IPv6 de chaque node
        node_ips = {}
        for i in range(1, 13):
            send_cmd(proc, f"node {i}", wait=1)
            addrs = get_node_ipaddr(proc)
            node_ips[i] = addrs
            print(f"--------------------------- Node {i} adresses IPv6 : {addrs}")

        for i in range(1, 13):
            print(f"____________________________ Node {i} adresses IPv6 : {node_ips[i]}")

        # Exemple d'envoi d'une commande ping asynchrone (à adapter selon vos besoins)
        if node_ips.get(2) and node_ips[2]:
            target_addr = node_ips[2][0]
            print(f"\nEnvoi d'un ping asynchrone depuis node 1 vers node 2 ({target_addr})")
            send_cmd(proc, "node 1", wait=1)
            ping_async(proc, target_addr, 32, 10, 1)
        else:
            print("Aucune adresse IPv6 trouvée pour node 2.")

        print("Fin du script. La session OTNS reste interactive.")
        proc.interact()

if __name__ == '__main__':
    main()