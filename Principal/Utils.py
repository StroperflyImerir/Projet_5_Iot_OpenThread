#Class initialization

import time


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

def get_node_ipaddr(proc):
    """
    Exécute la commande ipaddr et renvoie la sortie.
    On extrait ici l'adresse souhaitée (par exemple, l'EID).
    """
    output = send_cmd(proc, "ipaddr", wait=1)
    addrs = re.findall(r"([0-9a-fA-F:]{20,})", output)
    if addrs:
        for addr in addrs:
            if "ff:fe00" not in addr:
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
    return send_cmd(proc, cmd, wait=2)