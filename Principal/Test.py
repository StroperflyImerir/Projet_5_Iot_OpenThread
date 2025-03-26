import sys
sys.path.insert(0, '/home/jbonn/ot-ns/pylibs')

from otns.cli import OTNS  # ou otns.OTNS selon la version
ns = OTNS()  # démarrer OTNS en arrière-plan
node_id = ns.add("router", x=500, y=250)  # ajoute un routeur à la position (500,250)
print(node_id)  # Affiche l’ID du nouveau nœud, ex: 1
