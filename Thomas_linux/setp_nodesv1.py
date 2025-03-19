import pexpect
import time
import sys
import subprocess
import concurrent.futures
import os
from dotenv import load_dotenv

# Charge les variables du fichier .env
load_dotenv()
nb_nodes = int(os.getenv("NB_NODES", 5))  # Utilise 5 par défaut si NB_NODES n'est pas défini

def send_cmd(proc, cmd, wait=1, prompt=">"):
    """Envoie une commande à un processus interactif et attend le prompt."""
    print(f"\n🟢 Envoi de la commande : {cmd}")
    proc.sendline(cmd)
    try:
        proc.expect(prompt, timeout=5)
        output = proc.before.decode('utf-8', errors='ignore')
    except pexpect.TIMEOUT:
        print(f"⚠️ Timeout sur la commande '{cmd}', envoi d'une ligne vide.")
        proc.sendline("")
        try:
            proc.expect(prompt, timeout=5)
            output = proc.before.decode('utf-8', errors='ignore')
        except pexpect.TIMEOUT:
            output = proc.before.decode('utf-8', errors='ignore')
    print(f"🔹 Résultat de '{cmd}':\n{output}\n")
    time.sleep(wait)
    return output

def configure_leader():
    print("🚀 Configuration du leader (ot-node1)...")
    leader = pexpect.spawn("docker attach ot-node1", timeout=30)
    leader.sendline("")  # Déclenchement du prompt
    try:
        leader.expect(">", timeout=10)
    except pexpect.TIMEOUT:
        print("⚠️ Leader: Aucune réponse, vérifie le conteneur ot-node1.")
        sys.exit(1)
    send_cmd(leader, "factoryreset", wait=1)
    send_cmd(leader, "dataset init new", wait=1)
    send_cmd(leader, "dataset commit active", wait=1)
    send_cmd(leader, "ifconfig up", wait=1)
    send_cmd(leader, "thread start", wait=5)
    time.sleep(5)
    send_cmd(leader, "state", wait=1)
    send_cmd(leader, "commissioner start", wait=1)
    print("✅ ot-node1 est configuré comme leader et commissioner démarré.")
    return leader

def get_eui64(container_name, prompt=">"):
    """
    Récupère l'EUI64 du nœud en attachant au conteneur et en envoyant la commande "eui64".
    On suppose que la sortie est au format :
      > eui64
      18b4300000000008
      Done
    On renvoie donc la ligne juste avant "Done".
    """
    # print(f"\n📌 Récupération de l'EUI64 pour {container_name}...")
    try:
        proc = pexpect.spawn(f"docker attach {container_name}", timeout=30)
    except Exception as e:
        print(f"Erreur lors de l'attachement à {container_name}: {e}")
        return None
    proc.sendline("")
    try:
        proc.expect(prompt, timeout=10)
    except pexpect.TIMEOUT:
        print(f"⚠️ Timeout : Aucune réponse du prompt pour {container_name}.")
        proc.close()
        return None
    proc.sendline("eui64")
    try:
        proc.expect(prompt, timeout=10)
        output = proc.before.decode('utf-8', errors='ignore')
    except pexpect.TIMEOUT:
        print(f"⚠️ Timeout : Pas de sortie de la commande 'eui64' pour {container_name}.")
        output = proc.before.decode('utf-8', errors='ignore')
    proc.close()
    lines = output.strip().splitlines()
    if len(lines) >= 2:
        eui = lines[-2].strip()
    elif len(lines) == 1:
        eui = lines[0].strip()
    else:
        eui = ""
    # print(f"🔹 {container_name} EUI64: {eui}")
    return eui

def add_joiner(leader, joiner_eui, retries=3):
    """Ajoute un joiner depuis le leader, avec retry en cas d'erreur de type NoBufs."""
    for attempt in range(retries):
        time.sleep(3)
        print(f"🛠 Tentative {attempt+1} pour ajouter le joiner {joiner_eui} depuis ot-node1...")
        output = send_cmd(leader, f"commissioner joiner add {joiner_eui} THREAD 60", wait=3)
        if "NoBufs" in output:
            print(f"❌ Buffer saturé pour {joiner_eui} à la tentative {attempt+1}. Attente et réessai.")
        else:
            print(f"✅ Joiner {joiner_eui} ajouté avec succès.")
            return True
    print(f"❌ Échec : Impossible d'ajouter le joiner {joiner_eui} après {retries} tentatives.")
    sys.exit(1)

def configure_joiner(leader, node_name, joiner_eui, retries=3):
    """
    Configure un joiner en envoyant 'joiner start THREAD' et en attendant 'Join success'
    puis en lançant 'thread start' et en vérifiant que l'état passe en 'child'.
    Si l'état ne passe pas à 'child' après 5 vérifications espacées de 2 secondes,
    relance le commissioner sur le leader et retente l'ajout.
    """
    print(f"🚀 Configuration du joiner ({node_name})...")
    joiner = pexpect.spawn(f"docker attach {node_name}", timeout=30)
    joiner.sendline("")
    try:
        joiner.expect(">", timeout=10)
    except pexpect.TIMEOUT:
        print(f"⚠️ {node_name} ne répond pas lors de l'obtention du prompt.")
        joiner.close()
        sys.exit(1)
    
    send_cmd(joiner, "factoryreset", wait=1)
    send_cmd(joiner, "ifconfig up", wait=1)
    
    success = False
    for attempt in range(retries):
        print(f"🟢 Tentative {attempt+1} pour 'joiner start THREAD' sur {node_name}...")
        send_cmd(joiner, "joiner start THREAD", wait=5)
        try:
            joiner.expect("Join success", timeout=30)
            print(f"✅ {node_name} a renvoyé 'Join success'.")
            success = True
            break
        except pexpect.TIMEOUT:
            print(f"❌ Timeout sur 'joiner start THREAD' pour {node_name} à la tentative {attempt+1}.")
            time.sleep(3)
    if not success:
        print(f"❌ Échec pour {node_name} après {retries} tentatives de join.")
        joiner.close()
        sys.exit(1)
    
    send_cmd(joiner, "thread start", wait=1)
    
    # Vérification répétée de l'état jusqu'à obtenir "child"
    max_checks = 5
    state_ok = False
    for i in range(max_checks):
        time.sleep(2)
        output = send_cmd(joiner, "state", wait=1)
        if "child" in output.lower():
            print(f"✅ {node_name} est bien configuré en child (vérification {i+1}/{max_checks}).")
            state_ok = True
            break
        else:
            print(f"🔄 {node_name} n'est pas encore en 'child' (vérification {i+1}/{max_checks}), attente 2 secondes...")
    joiner.close()
    if not state_ok:
        print(f"❌ Erreur : {node_name} n'est toujours pas en 'child' après {max_checks} vérifications.")
        print("Relancement du commissioner sur le leader et tentative de joiner add...")
        send_cmd(leader, "commissioner start", wait=1)
        add_joiner(leader, joiner_eui)
        time.sleep(5)
        # Optionnellement, on pourrait réessayer de configurer le joiner ici.
        sys.exit(1)

def main():
    # Lancer docker-compose pour démarrer les conteneurs
    print("🚀 Lancement de docker-compose up -d...")
    subprocess.run(["docker-compose", "up", "-d"], check=True)
    
    print("⏳ Attente de 10 secondes pour que les conteneurs démarrent...")
    time.sleep(10)
    
    # Configurer le leader (ot-node1)
    leader = configure_leader()
    
    # Générer la liste des joiners de ot-node2 à ot-node10
    joiner_nodes = [f"ot-node{i}" for i in range(2, nb_nodes+1)]
    joiner_euis = {}
    
    # Phase 1 : Récupérer les EUI64 pour chaque joiner (en parallèle)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_node = {executor.submit(get_eui64, node): node for node in joiner_nodes}
        for future in concurrent.futures.as_completed(future_to_node):
            node = future_to_node[future]
            try:
                eui = future.result()
                joiner_euis[node] = eui
            except Exception as exc:
                print(f"{node} a généré une exception: {exc}")
    
    print("\n🎉 Liste des EUI64 récupérés :")
    for node, eui in joiner_euis.items():
        print(f"{node}: {eui}")
    
    # Phase 2 : Ajouter et configurer chaque joiner séquentiellement
    for node in joiner_nodes:
        eui = joiner_euis[node]
        add_joiner(leader, eui)
        configure_joiner(leader, node, eui)
    
    print("🎉 Configuration complète du réseau Thread.")

if __name__ == "__main__":
    main()
