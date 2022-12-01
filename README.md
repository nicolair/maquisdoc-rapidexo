# rapidexo 
---------------
---------------

Interface Flask avec les repos github des fichiers LateX des rapidexo

C'est un projet Python qui utilise 

- le gestionnaire d'environnement virtuel poetry
- le framework flask 
_ le code est dans le fichier API.py

Lancement de l'appli
--------------------

- ouvrir une console dans le dossier de rapidexo
- activer l'environnement virtuel en ouvrant une console spécifique:
        poetry shell
- exporter le nom de l'application comme variable d'environnement:
        export FLASK_APP=API
- lancer l'appli
        flask run

On utilise aussi pour le développement local
gunicorn --bind 127.0.0.1:5000 wsgi:app

et pour le service sur digital ocean
gunicorn -worker-tmp-dir /dev/shm wsgi:app
