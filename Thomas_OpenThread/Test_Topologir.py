#!/usr/bin/env python3
import pexpect
import time
import os
import math
import sys

def send_cmd(proc, cmd, wait=0.5):
    """Envoie une commande à OTNS et affiche la réponse."""
    sys.stdout.write(f"\n🟢 Envoi de la commande : {cmd}\n")
    proc.sendline(cmd)
    proc.expect('>')
    time.sleep(wait)
    output = proc.before
    sys.stdout.write(f"🔹 Résultat de '{cmd}':\n{output}\n")
    return output

def main():
    # Se positionner dans le dossier OTNS
    os.chdir(os.path.expanduser("~/otns"))
    
    sys.stdout.write("Starting OTNS...\n")
    # Démarrer OTNS et rediriger la sortie vers le terminal
    proc = pexpect.spawn('otns', encoding='utf-8', timeout=20)
    proc.logfile = sys.stdout  # Affiche toute la sortie dans le terminal
    
    # Attendre le prompt initial
    proc.expect('>')
    
    # Exemple de commandes préconfigurées pour générer une topologie
    num_router = 2
    num_feds = 6
    radius = 150

    for router_index in range(num_router):
        center_x = 250 + 150 * router_index
        center_y = 250

        # Créer le router
        router_cmd = f"add router x {center_x} y {center_y}"
        send_cmd(proc, router_cmd)
        time.sleep(1)

        sys.stdout.write(f"Creating FED nodes around router {router_index} at ({center_x}, {center_y}) with radius {radius}...\n")
        for fed_index in range(num_feds):
            # Appliquer des règles d'exclusion
            if router_index == 0 and fed_index == 0:
                continue
            if router_index == num_router - 1 and fed_index == 3:
                continue
            if router_index not in [0, num_router - 1] and fed_index in [0, 3]:
                continue

            angle = 2 * math.pi * fed_index / num_feds
            fed_x = int(center_x + radius * math.cos(angle))
            fed_y = int(center_y + radius * math.sin(angle))
            fed_cmd = f"add fed x {fed_x} y {fed_y}"
            send_cmd(proc, fed_cmd, wait=0.2)
            sys.stdout.write(f"Added FED node at ({fed_x}, {fed_y}) for router {router_index}\n")

    sys.stdout.write("OTNS simulation setup complete.\n")
    sys.stdout.write("Vous êtes maintenant en mode interactif. Tapez vos commandes OTNS directement.\n")
    sys.stdout.write("Pour quitter, tapez 'exit' dans OTNS.\n\n")

    # Transfert complet du contrôle de l'interaction à l'utilisateur
    proc.interact()

if __name__ == '__main__':
    main()
