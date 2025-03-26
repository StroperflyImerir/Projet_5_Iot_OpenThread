#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/jbonn/ot-ns/pylibs')

from otns.cli import OTNS              # ou depuis otns.OTNS selon votre version
import time
import logging
import matplotlib.pyplot as plt


def scenario_incremental_ping():
    ns = OTNS()                        # Démarre OTNS en arrière-plan


    ns.web()                           # Lance la visualisation web (si disponible)
    ns.go(1, speed=4)                  # Avance le temps de simulation pour assurer le démarrage

    num_routers = 16                   # Nombre total de routeurs à générer
    spacing = 150                      # Espacement horizontal entre les routeurs et décalage vertical pour FEDs
    base_y = 500                       # Coordonnée Y pour les routeurs
    ping_delays = []                   # Liste pour stocker les délais de ping (en secondes)
    router_counts = []                 # Liste pour stocker le nombre de routeurs correspondant

    first_router_bottom_fed = None     # Source pour les tests ping (FED inférieur du premier routeur)
    last_router_top_fed = None         # Destination pour les tests ping (FED supérieur du routeur actuel)


    def ping(src: int, dst: int, duration: float):
        while duration > 0:
            ns.ping(src, dst)
            ns.go(1)
            duration -= 1
            

    for i in range(num_routers):
                                       # Calcule la position pour le routeur actuel
        router_x = (i + 1) * spacing
        router_y = base_y

                                       # Ajoute le nœud routeur
        router_id = ns.add("router", x=router_x, y=router_y)
    

                                       # Ajoute deux nœuds FED pour ce routeur:
                                       # - Le FED supérieur est placé au-dessus du routeur
        fed_top_id = ns.add("fed", x=router_x, y=router_y - spacing)
                                       # - Le FED inférieur est placé en dessous du routeur
        fed_bottom_id = ns.add("fed", x=router_x, y=router_y + spacing)
        

                                       # Pour le premier routeur, stocke son FED inférieur comme source de ping
        if i == 0:
            first_router_bottom_fed = fed_bottom_id

                                       # Pour le routeur actuel, utilise son FED supérieur comme destination de ping
        last_router_top_fed = fed_top_id

                                       # Démarre le protocole Thread sur les nouveaux nœuds
        ns.node_cmd(router_id, "thread start")
        ns.node_cmd(fed_top_id, "thread start")
        ns.node_cmd(fed_bottom_id, "thread start")

                                       # Avance le temps de simulation pour permettre au réseau de converger
        ns.go(duration=40, speed=1000)


                                       # Effectue un test ping: 1 ping avec un intervalle de 1 seconde
        print (f"ici on ping({first_router_bottom_fed}, {last_router_top_fed}, 10)")
        ping(first_router_bottom_fed, last_router_top_fed, 10)
        TabPing = ns.pings()
        print(f"Résultats des pings: {TabPing}")

                                       # Récupère les résultats de ping mis à jour
        
        new_count = len(TabPing)
        if new_count == 0:
                                       # Aucun résultat de ping disponible pour l'instant
            continue
        else:
            ItemPing = TabPing[new_count - 1]
            node, Adresse, ect, delay = ItemPing
            print(f"ItemPing: {ItemPing}")
            print(f"Le délai est: {delay}")

            router_counts.append(i + 1)
            ping_delays.append(delay)
    ns.close()  

    return ping_delays
   

    

if __name__ == "__main__":
    Tab2Delays = []
    for i in range(2):
        ping_delays = scenario_incremental_ping()
        if ping_delays:
            Tab2Delays.append(ping_delays)
        time.sleep(5)
    
                                       # Vérifie si nous avons des résultats de simulation
    if not Tab2Delays:
        print("Aucune donnée de simulation n'a été collectée")
        exit(1)
        
                                       # Trouve la longueur maximale de tout tableau de délais
    max_length = max(len(delays) for delays in Tab2Delays)
    
                                       # Crée une liste pour stocker les moyennes
    average_delays = [0] * max_length
    count_per_index = [0] * max_length
    
                                       # Additionne toutes les valeurs à chaque index
    for delays in Tab2Delays:
        for i, delay in enumerate(delays):
            average_delays[i] += delay
            count_per_index[i] += 1
    
                                       # Divise par le nombre pour obtenir la moyenne
    for i in range(max_length):
        if count_per_index[i] > 0:
            average_delays[i] = average_delays[i] / count_per_index[i]
        else:
            average_delays[i] = 0      # Gère le cas où aucune donnée n'existe pour cet index
    
                                       # Affiche les délais moyens pour chaque nombre de routeurs
    for i, avg_delay in enumerate(average_delays, start=1):
        print(f"Délai moyen pour {i} routeurs: {avg_delay:.2f} secondes")
    
                                       # Trace le graphique: axe x = nombre de routeurs, axe y = délai moyen de ping
    plt.figure(figsize=(8, 5))
    router_counts = list(range(1, len(average_delays) + 1))
    plt.plot(router_counts, average_delays, marker='o', linestyle='-', color='blue')
    plt.xlabel("Nombre de Routeurs")
    plt.ylabel("Délai Moyen de Ping (secondes)")
    plt.title("Délai Moyen de Ping en fonction du Nombre de Routeurs")
    plt.grid(True)
    plt.tight_layout()
    
                                       # Sauvegarde la figure
    save_path = "/mnt/c/Users/jbonn/Documents/Projet_5_Iot_Thread/Grpahe/average_ping_delay_vs_routers.png"
    plt.savefig(save_path)
    
                                       # Optionnellement, affiche le graphique si un serveur X est disponible
    plt.show()

