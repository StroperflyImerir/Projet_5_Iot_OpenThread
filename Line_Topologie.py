#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/jbonn/ot-ns/pylibs')

import os
os.environ["PATH"] += os.pathsep + "/home/imerir/go/bin"
from otns.cli import OTNS  # ou from otns.OTNS selon votre version
import time
import matplotlib.pyplot as plt
from datetime import datetime


RADIO_RANGE = 150


def scenario_incremental_ping():
    ns = OTNS()                        # Démarre OTNS en arrière-plan


    ns.web()                           # Lance la visualisation web (si disponible)
    ns.go(1, speed=4)                  # Avance le temps de simulation pour assurer le démarrage

    num_routers = 16                 # Nombre total de routeurs à générer
    num_fed = 20
    spacing = 150                      # Espacement horizontal entre les routeurs et décalage vertical pour FEDs
    base_y = 400                       # Coordonnée Y pour les routeurs
    ping_delays = []                   # Liste pour stocker les délais de ping (en secondes)
    router_counts = []                 # Liste pour stocker le nombre de routeurs correspondant

    first_router_bottom_fed = None     # Source pour les tests ping (FED inférieur du premier routeur)
    last_router_top_fed = None         # Destination pour les tests ping (FED supérieur du routeur actuel)


    # def ping(src: int, dst: int, duration: float):
    #     while duration > 0:
    #         ns.ping(src, dst)
    #         ns.go(1)
    #         duration -= 1
    
    def ping(src: int, dst: int, count: int = 10, interval: float = 1):
        """Envoie 'count' pings depuis src vers dst avec un intervalle donné."""
        for _ in range(count):
            ns.ping(src, dst)
            ns.go(interval)

    for i in range(num_routers):
        # Calcule la position pour le routeur actuel
        router_x = (i + 1) * spacing
        router_y = base_y

        # Ajoute le nœud routeur
        router_id = ns.add("router", x=router_x, y=router_y, radio_range=RADIO_RANGE)

        # Génère plusieurs nœuds FED en haut du routeur.
        # Par exemple, on va créer num_fed_top nœuds avec un décalage vertical de 5 unités entre chacun.
        fed_top_ids = []
        for j in range(num_fed):
            # Le premier FED est placé à (router_y - spacing)
            offset = j  
            fed_id = ns.add("fed", x=router_x, y=router_y - spacing + offset, radio_range=RADIO_RANGE)
            fed_top_ids.append(fed_id)

        # Pour le FED inférieur, on en ajoute un seul
        fed_bottom_id = ns.add("fed", x=router_x, y=router_y + spacing, radio_range=RADIO_RANGE)

        # Pour le premier routeur, on stocke son FED inférieur comme source de ping
        if i == 0:
            first_router_bottom_fed = fed_bottom_id

        # Pour le routeur actuel, on utilise par exemple le dernier FED du haut comme destination de ping
        last_router_top_fed = fed_bottom_id

        # Démarre le protocole Thread sur le routeur, tous les FED du haut et le FED inférieur
        ns.node_cmd(router_id, "thread start")
        for fed_top_id in fed_top_ids:
            ns.node_cmd(fed_top_id, "thread start")
        ns.node_cmd(fed_bottom_id, "thread start")


        # Avance le temps de simulation pour permettre au réseau de converger
        ns.go(duration=40, speed=1000)

        if i == 0:
            print (f"ici on ping({first_router_bottom_fed}, {fed_top_ids[0]})")
            ping(first_router_bottom_fed, last_router_top_fed)
            TabPing = ns.pings()
        
        else:
                                       # Effectue un test ping: 1 ping avec un intervalle de 1 seconde
            print (f"ici on ping({first_router_bottom_fed}, {last_router_top_fed})")
            ping(first_router_bottom_fed, last_router_top_fed)
            TabPing = ns.pings()
            # print(f"Résultats des pings: {TabPing}")

                                       # Récupère les résultats de ping mis à jour
        
        new_count = len(TabPing)
        if new_count == 0:
                                       # Aucun résultat de ping disponible pour l'instant
            continue
        # else:
        #     ItemPing = TabPing[new_count - 1]
        #     node, Adresse, ect, delay = ItemPing
        #     print(f"ItemPing: {ItemPing}")
        #     print(f"Le délai est: {delay}")

        #     router_counts.append(i + 1)
        #     ping_delays.append(delay)

        else:
            # Exclure le premier résultat (index 0) et calculer la moyenne des délais des autres
            delays = [item[3] for item in TabPing[1:]]
            if delays:
                avg_delay = sum(delays) / len(delays)
            else:
                avg_delay = 0
            print(f"Délai moyen (excluant le premier ping): {avg_delay}")

            router_counts.append(i + 1)
            ping_delays.append(avg_delay)



    ns.close()  

    return ping_delays
   

    

if __name__ == "__main__":
    # Exécute la simulation une seule fois et récupère les délais
    ping_delays = scenario_incremental_ping()
    
    if not ping_delays:
        print("Aucune donnée de simulation n'a été collectée")
        exit(1)
        
    # Affiche les délais mesurés pour chaque nombre de routeurs
    for i, delay in enumerate(ping_delays, start=1):
        print(f"Délai pour {i} routeurs: {delay:.2f} ms")
    
    # Trace le graphique: axe x = nombre de routeurs, axe y = délai moyen de ping
    plt.figure(figsize=(8, 5))
    router_counts = list(range(1, len(ping_delays) + 1))
    plt.plot(router_counts, ping_delays, marker='o', linestyle='-', color='blue')
    plt.xlabel("Nombre de Routeurs")
    plt.ylabel("Délai de Ping (ms)")
    plt.title("Délai de Ping en fonction du Nombre de Routeurs")
    plt.grid(True)
    plt.tight_layout()

    # Génère un timestamp au format HH_MM_SS et sauvegarde le graphique
    timestamp = datetime.now().strftime("%H_%M_%S")
    base_filename = f"ping_routers_with50fed_withradio1000"
    save_path = f"/home/imerir/ot-ns/Graphes_radio/{base_filename}_{timestamp}.png"
    plt.savefig(save_path)
    plt.show()
