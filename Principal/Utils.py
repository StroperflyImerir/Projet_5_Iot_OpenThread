#Class initialization

import time
import re
import pexpect
import sys

#==============================================================================================
# Envoi de commandes à OTNS

def send_cmd(proc, cmd, timeout=5, retries=2):
    """
    Send a command to the OTNS process and return the output.
    Includes retry logic and better error handling.
    """
    for attempt in range(retries + 1):
        try:
            print(f"\n[Envoi] aaaaaaaaaaaaa : {cmd}")
            sys.stdout.flush()
            proc.sendline(cmd)
            print("dexuieme ligne")
            sys.stdout.flush()
            proc.expect('>', timeout=timeout)
            print("troisieme ligne")
            sys.stdout.flush()
            output = proc.before.strip()
            print("[Réponse] bbbbbbbbbbbbb : " + output)
            sys.stdout.flush()
            
            # Debug: afficher la longueur et le contenu brut de proc.before
            print("DEBUG: proc.before repr =", repr(proc.before))
            sys.stdout.flush()
            
            # If we're expecting a node ID, add extra validation
            if cmd.startswith("add"):
                time.sleep(0.5)  # Give a bit more time for the complete response
                proc.sendline("")  # Send an empty line to get a fresh prompt
                proc.expect('>', timeout=1)
                additional_output = proc.before.strip()
                print("DEBUG: additional_output =", additional_output)
                sys.stdout.flush()
                if additional_output and re.search(r'\d+', additional_output):
                    output += "\n" + additional_output
            
            return output
        except pexpect.TIMEOUT:
            print(f"Command timed out (attempt {attempt+1}/{retries+1}): {cmd}")
            sys.stdout.flush()
            if attempt == retries:
                return "TIMEOUT"
        except pexpect.EOF:
            print(f"EOF encountered while executing command: {cmd}")
            sys.stdout.flush()
            return "EOF"
        except Exception as e:
            print(f"Error executing command '{cmd}': {e}")
            sys.stdout.flush()
            return "ERROR"

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
    """
    Extract node ID from OTNS output.
    The output format from OTNS seems to be sometimes inconsistent.
    """
    if not output:
        return None
    
    # Debug print to see exactly what we're getting
    print(f"DEBUG - Raw output: '{output}'")
    
    # Clean the output by removing any control characters
    cleaned_output = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', output)
    
    # Look for a pattern where a number appears alone on a line
    lines = cleaned_output.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and line.isdigit():
            print(f"Found ID: {line}")
            return int(line)
    
    # If not found that way, try with regex to find any digit sequence
    match = re.search(r'(?:^|\n)\s*(\d+)\s*(?:\n|$)', cleaned_output)
    if match:
        print(f"Found ID via regex: {match.group(1)}")
        return int(match.group(1))
        
    # Try one more pattern - sometimes the ID might be after specific text
    match = re.search(r'Done\s*(\d+)', cleaned_output)
    if match:
        print(f"Found ID after 'Done': {match.group(1)}")
        return int(match.group(1))
    
    print(f"WARNING: Failed to extract node ID from output: '{output}'")
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