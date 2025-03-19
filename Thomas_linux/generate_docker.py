import jinja2
import os
from dotenv import load_dotenv

# Charge les variables du fichier .env
load_dotenv()
nb_nodes = int(os.getenv("NB_NODES", 5))  # Utilise 5 par défaut si NB_NODES n'est pas défini

template_str = """
version: '3'
services:
  {% for i in range(1, nb_nodes+1) %}
  node{{ i }}:
    image: openthread/environment:latest
    container_name: ot-node{{ i }}
    network_mode: host
    command: ["/openthread/build/examples/apps/cli/ot-cli-ftd", "{{ i }}"]
    tty: true
    stdin_open: true
  {% endfor %}
"""

template = jinja2.Template(template_str)
output = template.render(nb_nodes=nb_nodes)

with open("docker-compose.yml", "w") as f:
    f.write(output)
