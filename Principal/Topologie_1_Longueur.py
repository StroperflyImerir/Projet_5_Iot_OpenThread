from Class_TeeLogger import TeeLogger
from Utils import send_cmd, get_node_ipaddr, ping_async, extract_node_id, wait_for_network_stability, check_node_state
import math
import os
import pexpect
import re
import time
import threading
import sys


#------------------------------------------------------------------------------------------
# Permet de générer une ligne de routeurs avec des end_devices

def generate_row_topology(proc, row_y, num_routers, fed_total, delta_x, start_x=500,
                          pattern_first=None, pattern_intermediate=None, pattern_last=None):
    """
    Génère une ligne de routeurs à la coordonnée y donnée.
    Pour chaque router, selon sa position (premier, intermédiaire ou dernier),
    ajoute des end_devices selon le pattern fourni (None = pas d'end_devices).
    Chaque end_device est placé sur un cercle de rayon fixe (radius = 150)
    autour du routeur, avec un angle = 2π * position / fed_total.
    """
    radius = 150
    router_ids = []
    fed_ids = {'left_bottom': None, 'right_top': None}
    
    # Mémoriser l'ID du premier routeur pour vérifier son état plus tard
    first_router_id = None
    
    for i in range(num_routers):
        center_x = start_x + i * delta_x  # Position x de départ (500 ici)
        center_y = row_y
        
        # Ajouter un routeur
        router_output = send_cmd(proc, f"add router x {center_x} y {center_y}")
        router_id = extract_node_id(router_output)
        if router_id:
            router_ids.append(router_id)
            if i == 0:
                first_router_id = router_id
        
        # Attente brève entre les ajouts de routeurs
        time.sleep(1)
        
        if i == 0:
            fed_positions = pattern_first
        elif i == num_routers - 1:
            fed_positions = pattern_last
        else:
            fed_positions = pattern_intermediate

        if fed_positions is None:
            continue

        # Ajouter des end devices autour du routeur
        for pos in fed_positions:
            angle = 2 * math.pi * pos / fed_total
            fed_x = int(center_x + radius * math.cos(angle))
            fed_y = int(center_y + radius * math.sin(angle))
            fed_output = send_cmd(proc, f"add fed x {fed_x} y {fed_y}")
            fed_id = extract_node_id(fed_output)
            if i == 0 and pos == 4:
                fed_ids['left_bottom'] = fed_id
            elif i == num_routers - 1 and pos == 0:
                fed_ids['right_top'] = fed_id
    
    # Attendre la stabilité du réseau après avoir ajouté une ligne complète
    if first_router_id:
        wait_for_network_stability(proc, duration=30, speedup_factor=32)
        # Vérifier l'état du premier routeur pour s'assurer que le réseau fonctionne
        state = check_node_state(proc, first_router_id)
        print(f"[Réseau] État du premier routeur après stabilisation: {state}")
    
    return fed_ids, router_ids

def reader_thread(proc):
    """Function to continuously read process output in a separate thread."""
    while True:
        try:
            data = proc.read_nonblocking(size=1024, timeout=1)
            if data:
                sys.__stdout__.write(data)
                sys.__stdout__.flush()
        except pexpect.TIMEOUT:
            continue
        except pexpect.EOF:
            break

def main():
    os.chdir(os.path.expanduser("~/otns"))
    
    # Créer un TeeLogger avec nom de fichier automatique incluant la date et heure
    tee_logger = TeeLogger()
    
    print("Starting OTNS...")
    # Lancer OTNS en mode debug et rediriger la sortie vers le TeeLogger
    proc = pexpect.spawn('otns -log debug', encoding='utf-8', timeout=30)
    proc.logfile = tee_logger
    proc.expect('>')
    
    # Start a thread to read process output in real-time
    rt = threading.Thread(target=reader_thread, args=(proc,), daemon=True)
    rt.start()
    
    num_routers = 3
    fed_total = 6
    delta_x = 150
    base_y = 250
    
    print("Génération de la ligne initiale...")
    # Modification des patterns pour ne garder que les devices en haut et en bas
    initial_fed_ids, initial_router_ids = generate_row_topology(
        proc,
        row_y=base_y,
        num_routers=num_routers,
        fed_total=fed_total,
        delta_x=delta_x,
        pattern_first=[2,4],        # Seulement haut et bas pour le premier
        pattern_intermediate=[2,4], # Seulement haut et bas pour les intermédiaires
        pattern_last=[2,4]          # Seulement haut et bas pour le dernier
    )
    
    print("Topologie de base générée, attente pour stabilisation complète...")
    # Attendre que le réseau initial soit complètement formé
    wait_for_network_stability(proc, duration=60, speedup_factor=32)
    
    left_bottom_id = initial_fed_ids['left_bottom']
    left_bottom_addr = None
    if left_bottom_id:
        left_bottom_addr = get_node_ipaddr(proc, left_bottom_id)
        print(f"Adresse du nœud gauche-bas (ID {left_bottom_id}): {left_bottom_addr}")
    
    # Vérifier l'état des routeurs initiaux
    print("\nÉtat des routeurs initiaux:")
    for router_id in initial_router_ids:
        state = check_node_state(proc, router_id)
        print(f"  - Routeur {router_id}: {state}")
    
    # Ralentir la simulation pour les opérations interactives
    send_cmd(proc, "speed 1")
    
    for i in range(1, 2):  # 1 extension
        print(f"\n=== Ajout de la section {i+1} de la topologie ===")
        start_x = 500 + i * num_routers * delta_x
        extension_fed_ids, extension_router_ids = generate_row_topology(
            proc,
            row_y=base_y,
            num_routers=num_routers,
            fed_total=fed_total,
            delta_x=delta_x,
            start_x=start_x,
            pattern_first=[2,4],        # Seulement haut et bas
            pattern_intermediate=[2,4], # Seulement haut et bas
            pattern_last=[2,4]          # Seulement haut et bas
        )
        
        # Attendre que l'extension rejoigne le réseau principal
        print(f"Attente pour que les nouveaux nœuds rejoignent le réseau...")
        wait_for_network_stability(proc, duration=60, speedup_factor=32)
        
        # Vérifier l'état des nouveaux routeurs
        print("\nÉtat des routeurs de l'extension:")
        for router_id in extension_router_ids:
            state = check_node_state(proc, router_id)
            print(f"  - Routeur {router_id}: {state}")
        
        # Ralentir la simulation pour tester les pings
        send_cmd(proc, "speed 1")
        
        # Tester la connectivité par ping
        right_top_id = extension_fed_ids['right_top']
        if right_top_id and left_bottom_id and left_bottom_addr:
            print(f"\nTest de connectivité: Ping du nœud {right_top_id} (droite-haut) vers {left_bottom_id} (gauche-bas)")
            send_cmd(proc, f"node {right_top_id}")
            print(f"Ping de {right_top_id} vers {left_bottom_id} ({left_bottom_addr})")
            ping_async(proc, left_bottom_addr, 32, 5, 1)
            
            # Attendre les résultats du ping
            print("Attente des résultats du ping...")
            time.sleep(10)
        else:
            print("FEDs source ou destination non disponibles pour le ping")
    
    print("\nFin du programme. La session OTNS reste interactive.")
    print("Vous pouvez maintenant interagir avec le réseau (faire des pings, vérifier les états, etc.)")
    
    try:
        proc.interact()
    finally:
        # Fermer proprement le logger à la fin
        tee_logger.close()

if __name__ == "__main__":
    main()