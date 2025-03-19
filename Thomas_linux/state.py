import pexpect
import time
import subprocess
import concurrent.futures
import os
from dotenv import load_dotenv

# Charge les variables du fichier .env
load_dotenv()
nb_nodes = int(os.getenv("NB_NODES", 5))  # Utilise 5 par défaut si NB_NODES n'est pas défini

def get_state(container_name, prompt=">"):
    """
    Récupère l'état d'un nœud en se connectant via docker attach et en envoyant la commande "state".
    On suppose que la sortie est au format :
      state
      router
      Done
    On renvoie donc la ligne juste avant "Done" (par exemple "router").
    """
    # print(f"🔍 Vérification de l'état de {container_name}...")
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

    proc.sendline("state")
    try:
        proc.expect(prompt, timeout=10)
        output = proc.before.decode('utf-8', errors='ignore')
    except pexpect.TIMEOUT:
        print(f"⚠️ Timeout : Pas de sortie pour la commande 'state' sur {container_name}.")
        output = proc.before.decode('utf-8', errors='ignore')
    proc.close()

    lines = output.strip().splitlines()
    state_val = ""
    if len(lines) >= 2:
        state_val = lines[-2].strip()
    elif lines:
        state_val = lines[0].strip()
    # print(f"🔹 {container_name} état: {state_val}")
    return state_val

def main():
    # Générer la liste des conteneurs (exemple : ot-node1 à ot-node10)
    containers = [f"ot-node{i}" for i in range(1, nb_nodes+1)]
    state_dict = {}
    
    # Récupérer les états en parallèle
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_container = {executor.submit(get_state, container): container for container in containers}
        for future in concurrent.futures.as_completed(future_to_container):
            container = future_to_container[future]
            try:
                state = future.result()
                state_dict[container] = state
            except Exception as exc:
                state_dict[container] = f"Erreur: {exc}"
    
    print("\n🎉 État simplifié de tous les nœuds :")
    for container, state in state_dict.items():
        print(f"{container}: {state}")

if __name__ == "__main__":
    main()
