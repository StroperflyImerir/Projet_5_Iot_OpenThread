#!/usr/bin/env python3
import pexpect
import time
import os
import math

def send_cmd(proc, cmd, wait=0.5):
    """Envoie une commande à OTNS et attend le prompt '>'."""
    print(f"Envoi de la commande : {cmd}")
    proc.sendline(cmd)
    proc.expect('>')
    time.sleep(wait)

def generate_row_topology(proc, row_y, num_routers, fed_total, delta_x,
                          pattern_first=None, pattern_intermediate=None, pattern_last=None):
    """
    Génère une ligne de routeurs à la coordonnée y donnée.
    Pour chaque router, en fonction de sa position (premier, intermédiaire ou dernier),
    on utilise le pattern correspondant pour ajouter des end_devices.
    
    Si le pattern choisi (pattern_first, pattern_intermediate ou pattern_last) est None,
    aucun end_device n'est ajouté pour ce router.
    
    Chaque end_device est positionné sur un cercle de rayon fixe (radius = 150)
    autour du routeur, avec un angle calculé par : angle = 2π * position / fed_total.
    """
    radius = 150
    for i in range(num_routers):
        center_x = 500 + i * delta_x  # Position x de départ = 250
        center_y = row_y
        send_cmd(proc, f"add router x {center_x} y {center_y}")
        
        # Déterminer le pattern selon la position dans la ligne
        if i == 0:
            fed_positions = pattern_first
        elif i == num_routers - 1:
            fed_positions = pattern_last
        else:
            fed_positions = pattern_intermediate
        
        # Si aucun pattern n'est fourni pour ce router, on ne crée pas d'end_devices.
        if fed_positions is None:
            continue
        
        # Ajouter les end_devices pour ce router
        for pos in fed_positions:
            angle = 2 * math.pi * pos / fed_total
            fed_x = int(center_x + radius * math.cos(angle))
            fed_y = int(center_y + radius * math.sin(angle))
            send_cmd(proc, f"add fed x {fed_x} y {fed_y}")

def main():
    os.chdir(os.path.expanduser("~/otns"))
    print("Starting OTNS...")
    proc = pexpect.spawn('otns', encoding='utf-8', timeout=20)
    proc.logfile = None
    proc.expect('>')
    
    num_routers = 5
    fed_total = 6
    delta_x = 150
    base_y = 250

    # Ligne 1 : y = 250, avec end_devices selon le pattern suivant
    #   - Premier router : [1, 2, 3, 4, 5]
    #   - Routers intermédiaires : [1, 5]
    #   - Dernier router : [0, 1, 5]
    generate_row_topology(proc,
                          row_y=base_y,
                          num_routers=num_routers,
                          fed_total=fed_total,
                          delta_x=delta_x,
                          pattern_first=[3,4,5],
                          pattern_intermediate=[5],
                          pattern_last=[0,5])
    
    # Ligne 2 : y = 250 + 150 = 400, uniquement des routeurs (pas d'end_devices)
    generate_row_topology(proc,
                          row_y=base_y+150,
                          num_routers=num_routers,
                          fed_total=fed_total,
                          delta_x=delta_x,
                          pattern_first=[3],    # Aucun end_device pour le premier router de cette ligne
                          pattern_intermediate=None,  # Aucun pour les intermédiaires
                          pattern_last=[0])      # Aucun pour le dernier router
    
    # Ligne 2 : y = 250 + 150 = 400, uniquement des routeurs (pas d'end_devices)
    generate_row_topology(proc,
                          row_y=base_y+300,
                          num_routers=num_routers,
                          fed_total=fed_total,
                          delta_x=delta_x,
                          pattern_first=[3],    # Aucun end_device pour le premier router de cette ligne
                          pattern_intermediate=None,  # Aucun pour les intermédiaires
                          pattern_last=[0])      # Aucun pour le dernier router
    
    # Ligne 3 : y = 250 + 300 = 550, avec end_devices selon le pattern suivant
    #   - Premier router : [0, 1]
    #   - Routers intermédiaires : [1]
    #   - Dernier router : [1, 2, 3]
    generate_row_topology(proc,
                          row_y=base_y+450,
                          num_routers=num_routers,
                          fed_total=fed_total,
                          delta_x=delta_x,
                          pattern_first=[1,2,3],
                          pattern_intermediate=[1],
                          pattern_last=[0,1])
    
    print("Topologie générée :")
    print("- Ligne 1 : Routers avec end_devices")
    print("- Ligne 2 : Routers seuls")
    print("- Ligne 3 : Routers avec end_devices")
    print("Vous pouvez maintenant interagir avec OTNS (ex: state, ping, etc.).")
    print("Pour quitter, tapez 'exit' dans OTNS.")
    proc.interact()

if __name__ == '__main__':
    main()
