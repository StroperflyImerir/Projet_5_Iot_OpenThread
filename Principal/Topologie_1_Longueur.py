from Class_TeeLogger import TeeLogger
from Utils import send_cmd, get_node_ipaddr, ping_async, extract_node_id
import math
import os
import pexpect
import re
import time


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
    fed_ids = {'left_bottom': None, 'right_top': None}
    for i in range(num_routers):
        center_x = start_x + i * delta_x  # Position x de départ (500 ici)
        center_y = row_y
        send_cmd(proc, f"add router x {center_x} y {center_y}")
        if i == 0:
            fed_positions = pattern_first
        elif i == num_routers - 1:
            fed_positions = pattern_last
        else:
            fed_positions = pattern_intermediate

        if fed_positions is None:
            continue

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
    return fed_ids



def main():
    os.chdir(os.path.expanduser("~/otns"))
    
    # Créer un TeeLogger avec nom de fichier automatique incluant la date et heure
    tee_logger = TeeLogger()
    
    print("Starting OTNS...")
    # Lancer OTNS en mode debug et rediriger la sortie vers le TeeLogger
    proc = pexpect.spawn('otns -log debug', encoding='utf-8', timeout=30)
    proc.logfile = tee_logger
    proc.expect('>')
    
    num_routers = 3
    fed_total = 6
    delta_x = 150
    base_y = 250
    initial_fed_ids = generate_row_topology(
        proc,
        row_y=base_y,
        num_routers=num_routers,
        fed_total=fed_total,
        delta_x=delta_x,
        pattern_first=[1,2,3,4,5],
        pattern_intermediate=[1,5],
        pattern_last=[0,1,5]
    )
    
    print("Topologie générée.")
    time.sleep(2)
  
    left_bottom_id = initial_fed_ids['left_bottom']
    left_bottom_addr = get_node_ipaddr(proc, left_bottom_id)
    for i in range(1, 6):  # 5 extensions
        start_x = 500 + i * num_routers * delta_x
        extension_fed_ids = generate_row_topology(
            proc,
            row_y=base_y,
            num_routers=num_routers,
            fed_total=fed_total,
            delta_x=delta_x,
            start_x=start_x,
            pattern_first=[1,2,3,4,5],
            pattern_intermediate=[1,5],
            pattern_last=[0,1,5]
        )
        print(f"Attente pour que les nouveaux nœuds rejoignent le réseau...")
        time.sleep(15)
        right_top_id = extension_fed_ids['right_top']
        if right_top_id and left_bottom_id:
            print(f"\nTentative de ping du nœud {right_top_id} (droite-haut) vers {left_bottom_id} (gauche-bas)")
            if not left_bottom_addr:
                left_bottom_addr = get_node_ipaddr(proc, left_bottom_id)
            if left_bottom_addr:
                send_cmd(proc, f"node {right_top_id}")
                print(f"Ping de {right_top_id} vers {left_bottom_id} ({left_bottom_addr})")
                ping_async(proc, left_bottom_addr, 32, 5, 1)
                time.sleep(8)
            else:
                print(f"Impossible de récupérer l'adresse du nœud {left_bottom_id}")
        else:
            print("FEDs source ou destination non disponibles pour le ping")
    
    try:
        proc.interact()
    finally:
        # Fermer proprement le logger à la fin
        tee_logger.close()

if __name__ == "__main__":
    main()