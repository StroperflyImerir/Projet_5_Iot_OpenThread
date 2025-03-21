#!/usr/bin/env python3
import pexpect
import time
import os

def send_cmd(proc, cmd, wait=0.5):
    """
    Envoie une commande à OTNS et attend le prompt '>'.
    Affiche la commande et sa sortie.
    """
    print(f"\n🟢 Envoi de la commande : {cmd}")
    proc.sendline(cmd)
    proc.expect('>')
    time.sleep(wait)
    output = proc.before
    print(f"🔹 Résultat de '{cmd}':\n{output}\n")
    return output

def main():
    # Se placer dans le dossier OTNS (ajustez le chemin si besoin)
    os.chdir(os.path.expanduser("~/otns"))

    print("Starting OTNS...")
    # Lancer OTNS
    proc = pexpect.spawn('otns', encoding='utf-8', timeout=20)
    # Afficher toute la sortie dans le terminal
    proc.logfile = None  
    proc.expect('>')

    # Exemple : ajouter un router avec des coordonnées données
    send_cmd(proc, "add router x 300 y 200")
    
    print("OTNS est lancé en mode interactif.")
    print("Vous pouvez désormais taper vos commandes dans ce terminal (ex: state, ping, etc.).")
    print("Pour quitter, tapez 'exit' dans OTNS.")

    # Céder le contrôle à l'utilisateur (la session reste interactive)
    proc.interact()

if __name__ == '__main__':
    main()
