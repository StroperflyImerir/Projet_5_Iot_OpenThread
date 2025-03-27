#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/jbonn/ot-ns/pylibs')

import os
os.environ["PATH"] += os.pathsep + "/home/imerir/go/bin"
from otns.cli import OTNS  # ou from otns.OTNS selon votre version
import time
import matplotlib.pyplot as plt
from datetime import datetime
import math

RADIO_RANGE = 500

def scenario_grid_ping():
    ns = OTNS()                        # Démarre OTNS en arrière-plan
    ns.web()                           # Lance la visualisation web (si disponible)
    ns.go(1, speed=4)                  # Avance le temps de simulation pour assurer le démarrage

    num_routers = 16                   # Nombre total de routeurs
    num_fed_top = 50                   # Nombre de nœuds FED au-dessus du routeur
    spacing = 500                      # Espacement de base entre les routeurs (pour la grille)
    margin = 700                       # Marge augmentée pour éviter des coordonnées négatives
    
    # Calcul du nombre de lignes et colonnes pour la grille
    n_cols = int(math.sqrt(num_routers))
    n_rows = math.ceil(num_routers / n_cols)
    
    ping_delays = []                   # Liste pour stocker les délais de ping (en secondes)
    router_counts = []                 # Liste pour stocker le nombre de routeurs correspondant
    
    # On va stocker le FED bottom de chaque routeur pour réaliser les tests de ping
    routers_bottom_feds = []

    first_router_bottom_fed = None     # FED bottom du premier routeur (source du ping)
    
    router_index = 0
    # Parcours en grille (lignes x colonnes)
    for row in range(n_rows):
        for col in range(n_cols):
            if router_index >= num_routers:
                break
            # Calcul des coordonnées du routeur dans la grille
            router_x = margin + col * spacing
            router_y = margin + row * spacing
            
            # Ajout du routeur
            router_id = ns.add("router", x=router_x, y=router_y, radio_range=RADIO_RANGE)
            
            # Création des nœuds FED "top" (positionnés au-dessus du routeur)
            fed_top_ids = []
            fed_top_spacing = spacing / (num_fed_top*10)
            for j in range(num_fed_top):
                fed_x = int(router_x + (j - num_fed_top/2) * fed_top_spacing * 0.3)
                fed_y = int(router_y - spacing + j * (spacing / num_fed_top))
                fed_id = ns.add("fed", x=fed_x, y=fed_y, radio_range=RADIO_RANGE)
                fed_top_ids.append(fed_id)
            
            # Création d'un nœud FED "bottom" (positionné sous le routeur) qui sera utilisé pour les pings
            fed_bottom_id = ns.add("fed", x=router_x, y=router_y + spacing, radio_range=RADIO_RANGE)
            
            routers_bottom_feds.append(fed_bottom_id)
            
            if router_index == 0:
                first_router_bottom_fed = fed_bottom_id
                ns.node_cmd(router_id, "thread start")
                for fed in fed_top_ids:
                    ns.node_cmd(fed, "thread start")
                ns.node_cmd(fed_bottom_id, "thread start")
                
                ns.go(duration=40, speed=1000)
                print(f"Ping initial du premier routeur: ping({first_router_bottom_fed}, {fed_top_ids[0]})")
                ping(first_router_bottom_fed, fed_top_ids[0], ns)
                TabPing = ns.pings()
            else:
                ns.node_cmd(router_id, "thread start")
                for fed in fed_top_ids:
                    ns.node_cmd(fed, "thread start")
                ns.node_cmd(fed_bottom_id, "thread start")
                
                ns.go(duration=40, speed=1000)
                print(f"Ping: ping({first_router_bottom_fed}, {fed_bottom_id})")
                ping(first_router_bottom_fed, fed_bottom_id, ns)
                TabPing = ns.pings()
            
            new_count = len(TabPing)
            if new_count == 0:
                continue
            else:
                delays = [item[3] for item in TabPing[1:]]
                avg_delay = sum(delays) / len(delays) if delays else 0
                print(f"Délai moyen (excluant le premier ping): {avg_delay}")
                router_counts.append(router_index + 1)
                ping_delays.append(avg_delay)
            
            router_index += 1

    ns.close()  
    return ping_delays

def ping(src: int, dst: int, ns, count: int = 10, interval: float = 1):
    """Envoie 'count' pings depuis src vers dst avec un intervalle donné."""
    for _ in range(count):
        ns.ping(src, dst)
        ns.go(interval)

if __name__ == "__main__":
    ping_delays = scenario_grid_ping()
    
    if not ping_delays:
        print("Aucune donnée de simulation n'a été collectée")
        exit(1)
    
    for i, delay in enumerate(ping_delays, start=1):
        print(f"Délai pour {i} routeurs: {delay:.2f} ms")
    
    plt.figure(figsize=(8, 5))
    router_counts = list(range(1, len(ping_delays) + 1))
    plt.plot(router_counts, ping_delays, marker='o', linestyle='-', color='blue')
    plt.xlabel("Nombre de Routeurs")
    plt.ylabel("Délai de Ping (ms)")
    plt.title("Délai de Ping en fonction du Nombre de Routeurs (topologie en grille)")
    plt.grid(True)
    plt.tight_layout()
    
    timestamp = datetime.now().strftime("%H_%M_%S")
    base_filename = "grid_ping_routers_with50fed_withradio150"
    save_path = f"/home/imerir/ot-ns/Graphes_radio/{base_filename}_{timestamp}.png"
    plt.savefig(save_path)
    plt.show()
