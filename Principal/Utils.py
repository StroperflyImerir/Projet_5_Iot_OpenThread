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
    return send_cmd(proc, cmd)  # Appelle la fonction send_cmd avec les paramètres

#==============================================================================================
# Extraction de l'ID d'un noeud

def extract_node_id(output):
    """Extrait l'ID du nœud créé à partir de la sortie de la commande add"""
    match = re.search(r"Added (?:router|fed) with nodeid=(\d+)", output)
    if match:
        return int(match.group(1))
    return None

#==============================================================================================
# Attente de stabilité du réseau

def wait_for_network_stability(proc, duration=15, speedup_factor=16):
    """
    Accélère la simulation pour permettre au réseau de se stabiliser, puis rétablit
    la vitesse normale. Cette fonction laisse OTNS traiter les événements réseau.
    
    Args:
        proc: Le processus OTNS
        duration: Durée d'attente en secondes (à vitesse normale)
        speedup_factor: Facteur d'accélération pendant l'attente
    """
    # Sauvegarde la vitesse actuelle
    original_speed = get_simulation_speed(proc)
    
    # Accélère la simulation
    print(f"\n[Réseau] Accélération de la simulation (facteur {speedup_factor}) pour {duration} secondes...")
    send_cmd(proc, f"speed {speedup_factor}")
    
    # Attente réelle = durée / facteur d'accélération
    real_wait = duration / speedup_factor
    time.sleep(real_wait)
    
    # Rétablit la vitesse d'origine
    print(f"[Réseau] Rétablissement de la vitesse normale (facteur {original_speed})...")
    send_cmd(proc, f"speed {original_speed}")
    
    print(f"[Réseau] Le réseau a eu l'équivalent de {duration} secondes pour se stabiliser.")

def get_simulation_speed(proc):
    """Récupère la vitesse actuelle de la simulation"""
    output = send_cmd(proc, "speed")
    match = re.search(r"speed=(\d+)", output)
    if match:
        return int(match.group(1))
    return 1  # Retourne la valeur par défaut si non trouvée

#==============================================================================================
# Vérification du statut réseau d'un nœud

def check_node_state(proc, node_id):
    """Vérifie l'état d'un nœud et retourne son rôle (router, child, leader, etc.)"""
    send_cmd(proc, f"node {node_id}")
    output = send_cmd(proc, "state", wait=1)
    state_lines = output.strip().splitlines()
    
    # Recherche la ligne contenant l'état (généralement la deuxième ligne après "state")
    for line in state_lines:
        line = line.strip()
        if line in ["router", "child", "leader", "detached"]:
            return line
    
    return "unknown"