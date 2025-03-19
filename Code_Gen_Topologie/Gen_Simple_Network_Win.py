import wexpect
import time
import sys

def send_cmd(proc, cmd, wait=2, prompt=">"):
    """
    Fonction qui envoie une commande à un nœud et récupère la sortie.
    Elle gère les éventuels timeouts.
    """
    print(f"\n🟢 Envoi de la commande : {cmd}")
    proc.sendline(cmd)
    try:
        proc.expect(prompt, timeout=5)
        output = proc.before
        if isinstance(output, bytes):  # Décoder si nécessaire
            output = output.decode('utf-8', errors='ignore')
    except wexpect.TIMEOUT:
        print(f"⚠️ Timeout sur la commande '{cmd}', envoi d'une ligne vide.")
        proc.sendline("")
        try:
            proc.expect(prompt, timeout=5)
            output = proc.before
            if isinstance(output, bytes):
                output = output.decode('utf-8', errors='ignore')
        except wexpect.TIMEOUT:
            output = proc.before
            if isinstance(output, bytes):
                output = output.decode('utf-8', errors='ignore')
    print(f"🔹 Résultat de '{cmd}':\n{output}\n")
    time.sleep(wait)
    return output

def parse_eui(output):
    """
    Extrait uniquement l’EUI64 d'un nœud à partir de la sortie brute de la commande 'eui64'.
    - Recherche une ligne contenant exactement 16 caractères hexadécimaux.
    """
    lines = output.splitlines()
    for line in lines:
        line = line.strip()  # Supprime les espaces et retours à la ligne
        if len(line) == 16 and all(c in "0123456789abcdefABCDEF" for c in line):
            return line
    return None  # Si aucun EUI valide n’est trouvé

def configure_leader():
    """
    Configure ot-node1 en tant que leader du réseau Thread.
    """
    print("🚀 Configuration du leader (ot-node1)...")
    leader = wexpect.spawn("docker attach ot-node1", timeout=30)
    send_cmd(leader, "factoryreset")
    send_cmd(leader, "dataset init new")
    send_cmd(leader, "dataset commit active")
    send_cmd(leader, "ifconfig up")
    send_cmd(leader, "thread start", wait=10)
    time.sleep(10)  # Attendre que le thread démarre
    send_cmd(leader, "state")
    send_cmd(leader, "commissioner start")
    print("✅ ot-node1 est configuré comme leader et commissioner démarré.")
    return leader

def retrieve_joiner_eui(node_name):
    """
    Récupère l'EUI64 d'un nœud enfant avant de l'ajouter au réseau.
    """
    print(f"🚀 Récupération de l'EUI64 pour {node_name}...")
    joiner = wexpect.spawn(f"docker attach {node_name}", timeout=30)
    send_cmd(joiner, "factoryreset")
    send_cmd(joiner, "ifconfig up")
    eui_output = send_cmd(joiner, "eui64", wait=1)
    joiner_eui = parse_eui(eui_output)
    
    if joiner_eui:
        print(f"🔹 EUI récupéré pour {node_name} : {joiner_eui}")
    else:
        print(f"❌ Impossible d'extraire l'EUI pour {node_name}. Sortie :\n{eui_output}")
    
    joiner.close()
    return joiner_eui

def add_joiner(leader, joiner_eui):
    """
    Ajoute un nœud joiner au réseau en envoyant son EUI au leader.
    """
    print(f"🛠 Ajout du joiner avec EUI {joiner_eui} depuis ot-node1...")
    send_cmd(leader, f"commissioner joiner add {joiner_eui} THREAD 120", wait=3)
    print(f"✅ Commande d'ajout envoyée pour l'EUI {joiner_eui}.")

def configure_joiner_post(node_name, expected_state="child"):
    """
    Configure le nœud enfant après l’ajout au réseau.
    """
    print(f"🚀 Démarrage du processus de join sur {node_name}...")
    joiner = wexpect.spawn(f"docker attach {node_name}", timeout=30)
    send_cmd(joiner, "joiner start THREAD", wait=10)
    send_cmd(joiner, "thread start")
    output = send_cmd(joiner, "state")
    
    if expected_state in output.lower():
        print(f"✅ {node_name} est bien configuré en {expected_state}.")
    else:
        print(f"❌ Erreur sur {node_name}. Sortie de 'state':\n{output}")
    
    joiner.close()

def main():
    # Configuration du leader (ot-node1)
    leader = configure_leader()
    
    # Pour chaque nœud enfant (ot-node2 à ot-node10)
    for i in range(2, 3):
        node_name = f"ot-node{i}"
        
        # Récupération de l’EUI64
        joiner_eui = retrieve_joiner_eui(node_name)
        if joiner_eui:
            # Ajout du joiner au réseau
            add_joiner(leader, joiner_eui)
            time.sleep(2)
            # Configuration finale du joiner
            configure_joiner_post(node_name, expected_state="child")
            time.sleep(2)
        else:
            print(f"❌ Ignoré : Impossible d’ajouter {node_name} car l’EUI est invalide.")
    
    print("🎉 Configuration complète du réseau Thread.")

if __name__ == "__main__":
    main()
