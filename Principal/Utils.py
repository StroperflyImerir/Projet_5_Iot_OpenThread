#Class initialization

import time
import re

#==============================================================================================
# Envoi de commandes à OTNS

def send_cmd(proc, cmd, wait=0.5):
    """Envoie une commande à OTNS, affiche la commande, attend le prompt '>' et renvoie la sortie."""
    print(f"\n[Envoi] {cmd}")
    proc.sendline(cmd)
    proc.expect('>')
    time.sleep(wait)
    output = proc.before
    print(f"[Réponse] {output}")
    return output

#==============================================================================================
# Récupération de l'adresse IP d'un noeud

def get_node_ipaddr(proc, node_id):
    """Récupère l'adresse IPv6 d'un nœud"""
    send_cmd(proc, f"node {node_id}")
    output = send_cmd(proc, "ipaddr", wait=1)
    addrs = re.findall(r"([0-9a-fA-F:]{20,})", output)
    if addrs:
        for addr in addrs:
            if addr.startswith("fd"):
                return addr.strip()
        return addrs[0].strip()
    return None
    
#==============================================================================================
# Envoi de commandes ping async

def ping_async(proc, addr, size, count, interval):
    """
    Envoie une commande ping async avec les paramètres donnés.
    La syntaxe est : ping async <addr> <size> <count> <interval>
    """
    cmd = f"ping async {addr} {size} {count} {interval}"
    return send_cmd

#==============================================================================================
# Extraction de l'ID d'un noeud

def extract_node_id(output):
    """Extrait l'ID du nœud créé à partir de la sortie de la commande add"""
    match = re.search(r"Added (?:router|fed) with nodeid=(\d+)", output)
    if match:
        return int(match.group(1))
    return None