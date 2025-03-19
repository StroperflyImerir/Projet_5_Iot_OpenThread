import pexpect
import time
import subprocess
import concurrent.futures
import os
from dotenv import load_dotenv


# Charge les variables du fichier .env
load_dotenv()
nb_nodes = int(os.getenv("NB_NODES", 5))  # Utilise 5 par défaut si NB_NODES n'est pas défini


def get_ipv6(container_name, prompt=">"):
    """
    Récupère les adresses IPv6 du conteneur en se connectant via docker attach et en envoyant la commande "ipaddr".
    On retourne uniquement les adresses qui commencent par "fe80:".
    """
    # print(f"\n📌 Récupération des adresses IPv6 pour {container_name}...")
    try:
        proc = pexpect.spawn(f"docker attach {container_name}", timeout=30)
    except Exception as e:
        print(f"Erreur lors de l'attachement à {container_name}: {e}")
        return None

    # Déclenchement du prompt
    proc.sendline("")
    try:
        proc.expect(prompt, timeout=10)
    except pexpect.TIMEOUT:
        print(f"⚠️ Timeout : Aucune réponse du prompt pour {container_name}.")
        proc.close()
        return None

    # Envoyer la commande "ipaddr"
    proc.sendline("ipaddr")
    try:
        proc.expect(prompt, timeout=10)
        output = proc.before.decode('utf-8', errors='ignore')
    except pexpect.TIMEOUT:
        print(f"⚠️ Timeout : Pas de sortie de la commande 'ipaddr' pour {container_name}.")
        output = proc.before.decode('utf-8', errors='ignore')
    proc.close()

    # Découper la sortie en lignes et filtrer les adresses IPv6 qui commencent par "fe80:"
    lines = output.strip().splitlines()
    ipv6_list = [line.strip() for line in lines if line.strip().startswith("fe80:")]
    # print(f"🔹 {container_name} adresses IPv6: {ipv6_list}")
    return ipv6_list

def main():
    # Générer la liste des conteneurs (exemple : ot-node1 à ot-node10)
    containers = [f"ot-node{i}" for i in range(1, nb_nodes+1)]
    ipv6_dict = {}
    
    # Récupérer les adresses IPv6 en parallèle
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_container = {executor.submit(get_ipv6, container): container for container in containers}
        for future in concurrent.futures.as_completed(future_to_container):
            container = future_to_container[future]
            try:
                ipv6 = future.result()
                ipv6_dict[container] = ipv6
            except Exception as exc:
                ipv6_dict[container] = f"Erreur: {exc}"
    
    print("\n🎉 Liste des adresses IPv6 récupérées :")
    for container, ipv6 in ipv6_dict.items():
        print(f"{container}: {ipv6}")
    
    return ipv6_dict

if __name__ == "__main__":    
    main()
