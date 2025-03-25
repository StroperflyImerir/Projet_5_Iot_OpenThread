from Class_TeeLogger import TeeLogger
from Utils import send_cmd
import math
import os
import pexpect
import re
import time


#------------------------------------------------------------------------------------------
# Permet de générer une ligne de routeurs avec des end_devices

def generate_row_topology(proc, row_y, num_routers, fed_total, delta_x,
                          pattern_first=None, pattern_intermediate=None, pattern_last=None):
    """
    Génère une ligne de routeurs à la coordonnée y donnée.
    Pour chaque router, selon sa position (premier, intermédiaire ou dernier),
    ajoute des end_devices selon le pattern fourni (None = pas d'end_devices).
    Chaque end_device est placé sur un cercle de rayon fixe (radius = 150)
    autour du routeur, avec un angle = 2π * position / fed_total.
    """
    radius = 150
    for i in range(num_routers):
        center_x = 500 + i * delta_x  # Position x de départ (500 ici)
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
            send_cmd(proc, f"add fed x {fed_x} y {fed_y}")


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
    generate_row_topology(proc,
                          row_y=base_y,
                          num_routers=num_routers,
                          fed_total=fed_total,
                          delta_x=delta_x,
                          pattern_first=[1,2,3,4,5],
                          pattern_intermediate=[1,5],
                          pattern_last=[0,1,5])
    
    print("Topologie générée.")
    time.sleep(2)
  
    try:
        proc.interact()
    finally:
        # Fermer proprement le logger à la fin
        tee_logger.close()

if __name__ == "__main__":
    main()