#!/usr/bin/env python3
from Class_TeeLogger import TeeLogger
from Utils import send_cmd, get_node_ipaddr, ping_async, extract_node_id, wait_for_network_stability, check_node_state
import os
import pexpect
import time
import math

def main():
    os.chdir(os.path.expanduser("~/otns"))
    
    # Créer un TeeLogger avec nom de fichier automatique
    tee_logger = TeeLogger()
    
    print("Starting OTNS...")
    print("Lancement d'OTNS en mode debug...")
    proc = pexpect.spawn('otns -log debug', encoding='utf-8', timeout=30)
    proc.logfile = tee_logger
    proc.expect('>')
    
    # Création d'un réseau simple avec 3 routeurs et 2 end devices
    print("\n=== Création d'un réseau simple ===")
    
    time.sleep(20)

    # Ajouter le routeur central (qui deviendra leader)
    router1_output = send_cmd(proc, "add router x 500 y 300")
    print("éééééééééééééééééééééééééééééééééééééééééééééééééééééé : ",router1_output)
    router1_id = extract_node_id(router1_output)
    
    # Ajouter les routeurs supplémentaires
    router2_output = send_cmd(proc, "add router x 350 y 300")
    router2_id = extract_node_id(router2_output)
    
    router3_output = send_cmd(proc, "add router x 650 y 300")
    router3_id = extract_node_id(router3_output)
    
    # Ajouter des end devices
    fed1_output = send_cmd(proc, "add fed x 350 y 200")
    fed1_id = extract_node_id(fed1_output)
    
    fed2_output = send_cmd(proc, "add fed x 650 y 200")
    fed2_id = extract_node_id(fed2_output)
    
    router_ids = [router1_id, router2_id, router3_id]
    fed_ids = [fed1_id, fed2_id]
    
    print("éééééééééééééééééééééééééééééééééééééééééééééééééééééé : ",router1_output)

    all_nodes = router_ids + fed_ids
    
    # Attendre que le réseau se forme avec les paramètres par défaut
    print("\n=== Test 1: Formation du réseau à vitesse normale ===")
    print("Attente de 20 secondes à vitesse normale...")
    time.sleep(20)
    
    # Vérifier les états des nœuds
    for node_id in all_nodes:
        state = check_node_state(proc, node_id)
        print(f"Nœud {node_id}: {state}")
    
    # Vérifier les adresses
    for node_id in all_nodes:
        addr = get_node_ipaddr(proc, node_id)
        print(f"Nœud {node_id} adresse: {addr}")
    
    # Test 2: Utiliser l'accélération pour la formation du réseau
    print("\n=== Test 2: Réinitialisation et formation avec accélération ===")
    send_cmd(proc, "clear")
    
    # Recréer le même réseau
    router1_output = send_cmd(proc, "add router x 500 y 300")
    router1_id = extract_node_id(router1_output)
    
    router2_output = send_cmd(proc, "add router x 350 y 300")
    router2_id = extract_node_id(router2_output)
    
    router3_output = send_cmd(proc, "add router x 650 y 300")
    router3_id = extract_node_id(router3_output)
    
    fed1_output = send_cmd(proc, "add fed x 350 y 200")
    fed1_id = extract_node_id(fed1_output)
    
    fed2_output = send_cmd(proc, "add fed x 650 y 200")
    fed2_id = extract_node_id(fed2_output)
    
    router_ids = [router1_id, router2_id, router3_id]
    fed_ids = [fed1_id, fed2_id]
    
    all_nodes = router_ids + fed_ids
    
    # Utiliser la fonction wait_for_network_stability pour accélérer la simulation
    wait_for_network_stability(proc, duration=60, speedup_factor=32)
    
    # Vérifier les états des nœuds après l'accélération
    print("\nÉtats des nœuds après l'accélération:")
    for node_id in all_nodes:
        state = check_node_state(proc, node_id)
        print(f"Nœud {node_id}: {state}")
    
    # Tester la connectivité par ping
    print("\n=== Test 3: Connectivité entre les nœuds ===")
    
    # Trouver un nœud qui a une adresse
    source_id = None
    target_id = None
    target_addr = None
    
    for node_id in all_nodes:
        addr = get_node_ipaddr(proc, node_id)
        if addr:
            if not source_id:
                source_id = node_id
            elif not target_id:
                target_id = node_id
                target_addr = addr
                break
    
    if source_id and target_id and target_addr:
        print(f"Test de ping entre le nœud {source_id} et le nœud {target_id} ({target_addr})")
        send_cmd(proc, f"node {source_id}")
        ping_async(proc, target_addr, 32, 5, 1)
        
        # Attendre les résultats du ping
        print("Attente des résultats du ping...")
        time.sleep(10)
    else:
        print("Impossible de réaliser le ping: adresses non disponibles")
    
    print("\nFin des tests. La session OTNS reste interactive.")
    print("Vous pouvez maintenant interagir avec le réseau.")
    
    try:
        proc.interact()
    finally:
        tee_logger.close()

if __name__ == "__main__":
    main()
