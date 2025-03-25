#!/usr/bin/env python3
import pexpect
import time
import os
import math
import re
import sys
import datetime

LOG_FILENAME = "otns_log.txt"

class TeeLogger:
    def __init__(self, file_obj):
        self.file_obj = file_obj

    def write(self, data):
        # Si data est en bytes, le décoder en utf-8 (avec remplacement en cas d'erreur)
        if isinstance(data, bytes):
            data = data.decode("utf-8", errors="replace")
        # Découper data en lignes et préfixer chaque ligne par un timestamp
        lines = data.splitlines(keepends=True)
        for line in lines:
            ts = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
            # Écrire dans la console et dans le fichier
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
        center_x = 500 + i * delta_x  # Position x de départ (500 ici)
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
    On extrait ici les adresses (par exemple, EID ou RLOC) via une regex.
    """
    output = send_cmd(proc, "ipaddr", wait=1)
    addrs = re.findall(r"([0-9a-fA-F:]{20,})", output)
    return addrs

def ping_async(proc, addr, size, count, interval):
    """
    Envoie une commande ping async avec les paramètres donnés.
    La syntaxe est : ping async <addr> <size> <count> <interval>
    """
    cmd = f"ping async {addr} {size} {count} {interval}"
    return send_cmd(proc, cmd, wait=2)

def main():
    os.chdir(os.path.expanduser("~/otns"))
    # Ouvrir le fichier de log en mode écrasement (ou "a" pour conserver les anciens logs)
    with open(LOG_FILENAME, "w") as log_file:
        tee = TeeLogger(log_file)
        # Rediriger sys.stdout pour capturer tous les prints dans le log
        sys.stdout = tee

        print("Starting OTNS...")
        # Lancer OTNS en mode debug et rediriger la sortie vers le TeeLogger
        proc = pexpect.spawn('otns -log debug', encoding='utf-8', timeout=30)
        proc.logfile = tee
        proc.expect('>')
        
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
                              pattern_last=[0,1,5])
        
        print("Topologie générée.")
        time.sleep(2)
        
        # Récupérer et afficher l'adresse IPv6 de chaque node
        # node_ips = {}
        # for i in range(1, num_routers + 1):
        #     send_cmd(proc, f"node {i}", wait=1)
        #     addrs = get_node_ipaddr(proc)
        #     node_ips[i] = addrs
        #     print(f"Node {i} adresses IPv6 : {addrs}")
        
        # for i in range(1, num_routers + 1):
        #     print(f"Node {i} adresses IPv6 : {node_ips[i]}")
        
        # # Exemple : envoyer un ping asynchrone du node 1 vers node 2 en utilisant la première adresse de node 2
        # if 2 in node_ips and node_ips[2]:
        #     target_addr = node_ips[2][0]
        #     print(f"\nEnvoi d'un ping asynchrone depuis node 1 vers node 2 ({target_addr})")
        #     send_cmd(proc, "node 1", wait=1)
        #     ping_result = ping_async(proc, target_addr, 32, 10, 1)
        #     print(f"Résultat du ping async : {ping_result}")
        # else:
        #     print("Aucune adresse trouvée pour node 2.")
        
        print("Fin du script. La session OTNS reste interactive. Tapez 'exit' pour quitter.")
        proc.interact()

if __name__ == '__main__':
    main()
