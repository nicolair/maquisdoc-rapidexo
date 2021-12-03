from flask import Flask
from flask_cors import CORS
from flask import request
from flask import send_file
from flask import session
from flask import after_this_request
from flask import jsonify

import requests
import random
import pylatex
import os
import uuid

app = Flask(__name__)
CORS(app)

# github credentials (personal token)
#token = "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"
#user = "nicolair"
user = os.environ.get("GITHUB_USER")
token = os.environ.get("GITHUB_TOKEN")

#pour effacer les fichiers créés, on appelle la fonction clean à la fin (à la fin de quoi?)
#pas satisfaisante: sessions ??
def clean(truc):
    print(truc)
    path = "listeRapidexo.pdf"
    os.remove(path)
    return path + ' effacé' 
#app.teardown_appcontext(clean)

# Set the secret key to some random bytes. Keep this really secret!
#utilisé par la session
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


#cette manière de lancer l'appli n'est pas claire du tout.
#je ne sais pas comment initialiser des para globaux

@app.route("/open_sess")
def open_sess():
    session['idSession'] = str(uuid.uuid4())
    print('coucou de open_sess')
    return session['idSession']

@app.route("/rapidexoAPI", methods = ['GET'])
def rapidexoAPI():
    resp = "coucou from flask "
    #pour le moment, je ne sais pas utiliser les sessions
    """
    if not 'idSession' in session:
        open_sess()
        print("vous n'avez pas ouvert de session")
        
    else:
        resp += 'session: ' + session['idsession']
    """
    session['idSession'] = str(uuid.uuid4())
    resp = session['idSession']
    #data = request.args
    #print(data)
    
    #nbs d'exercices demandés pour chaque thème
    #attention ce sont des chaines, pas des nbs
    nbsExos = {}
    for key in request.args:
        nbsExos[key] = int(request.args[key])
    
    liLatex = []
    """
    Pour chaque thème dont on demande des exos
       récupération de données sur les exos du thème dans le repository
       formation de la liste aléatoire d'exos (chemins)
    """
    listeExosPath = []
    for theme in nbsExos:
        if nbsExos[theme] > 0:
            #récupération de données sur les fichiers du repositorydu thème
            liEnonc = getExos(theme)
            #nbs tot d'exos pour le thème
            nbTotExos = len(liEnonc)
            #print(theme, nbsExos[theme], nbTotExos)
            #formation de la liste aléatoire d'exos tirés
            lili = []
                #le premier exo est numéroté 0 dans une liste
            nbTotExos = nbTotExos - 1
            lili = random.sample(range(nbTotExos),nbsExos[theme])
            for key in lili:
                #print(theme + '/' + liEnonc[key])
                listeExosPath.append(theme + '/' + liEnonc[key])
   
    random.shuffle(listeExosPath)
    #path = listeExosPath[0]
    
    #formation du code LateX à compiler
    listeExosLatex = list(map(getLatex,listeExosPath))
    
    #compilation du LateX
    latexCompilEnonc(listeExosLatex,listeExosPath)
    
    #path = "listeRapidexo.pdf"
    #resp = send_file(path,as_attachment=True)

    return resp

@app.route('/getREFS', methods = ['GET'])
def getREFS():
    #data = request.args
    #print(data)
    
    #nbs d'exercices demandés pour chaque thème
    #attention ce sont des chaines, pas des nbs
    nbsExos = {}
    for key in request.args:
        nbsExos[key] = int(request.args[key])
    
    liLatex = []
    """
    Pour chaque thème dont on demande des exos
       récupération de données sur les exos du thème dans le repository
       formation de la liste aléatoire d'exos (chemins)
    """
    listeExosPath = []
    for theme in nbsExos:
        if nbsExos[theme] > 0:
            #récupération de données sur les fichiers du repositorydu thème
            liEnonc = getExos(theme)
            #nbs tot d'exos pour le thème
            nbTotExos = len(liEnonc)
            print(theme, nbsExos[theme], nbTotExos)
            #formation de la liste aléatoire d'exos tirés
            lili = []
                #le premier exo est numéroté 0 dans une liste
            nbTotExos = nbTotExos - 1
            lili = random.sample(range(nbTotExos),nbsExos[theme])
            for key in lili:
                #print(theme + '/' + liEnonc[key])
                listeExosPath.append(theme + '/' + liEnonc[key])
   
    random.shuffle(listeExosPath)
    
    #formation du code LateX à compiler
    #listeExosLatex = list(map(getLatex,listeExosPath))
    
    #compilation du LateX
    #latexCompilEnonc(listeExosLatex,listeExosPath)
    
    #path = "listeRapidexo.pdf"
    #resp = send_file(path,as_attachment=True)

    return jsonify(listeExosPath)

@app.route('/getCOMPIL', methods=['POST'])
def getCOMPIL():
    print("coucou de getCOMPIL")
    session['idSession'] = str(uuid.uuid4())
    
    # récupération de la liste des chemins
    listeExosPath = request.get_json()
    
    #formation du code LateX à compiler
    listeExosLatex = list(map(getLatex,listeExosPath))
    
    #compilation du LateX
    latexCompilEnonc(listeExosLatex,listeExosPath)
    
    path = "pdf/Enonc_" + session['idSession'] + '.pdf'

    #print(listeExosLatex)
    resp = {'level':2,'id_session':session['idSession']}
    return resp

    
@app.route('/getPDF/<idSession>')    
def getPDF(idSession):
    path = "pdf/Enonc_" + str(idSession) + '.pdf' 
    @after_this_request
    def clean(response):
        os.remove(path)
        return response
    return send_file(path,as_attachment=True) 

@app.route('/LATEX',methods=['POST'])
def LATEX():
    print( "coucou de LATEX sur flask ")
    path = request.get_json()
    print(path + '\n')
    return getLatex(path)

#récupérer dans le repo gitHub les références des exos d'un thème
def getExos(theme):
    import json
    import os
    """
    Pour pouvoir faire plus de 60 requêtes par heure  sur l'API de gitHub, il faut s'authentifier (basic authentication) et un token.
    Attention! le token a une durée de vie limitée
    """
    #token = "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"
    #user = "nicolair"
    jsonhead = {'Accept': 'application/vnd.github.v3.json'}

    url = "https://api.github.com/repos/nicolair/math-rapidexos/contents"
    nomFold = theme
    urlFold = url + '/' + nomFold
    r = requests.get(urlFold, headers=jsonhead, auth = (user,token))
    lili = json.loads(r.text)
    liEnonc = []
    for file in lili:
        nom, ext = os.path.splitext(file['name'])
        if nom[0] == 'E' and ext == '.tex':
            liEnonc.append(file['name'])
    return liEnonc


def getLatex(path):
    """
    Pour pouvoir faire plus de 60 requêtes par heure  sur l'API de gitHub, il faut s'authentifier (basic authentication) et un token.
    Pour récupérer le code Latex d'un fichier il faut préciser le "média type" raw pour l'API
    Syntaxe d'appel avec curl
    curl  -u nicolair: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 
          -H"Accept: application/vnd.github.v3.raw" 
          https://api.github.com/repos/nicolair/math-rapidexos/contents/Fracrat/EfracratC9.tex
    """
    #token = "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"
    #token = "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"
    #user = "nicolair"
    rawhead = {'Accept': 'application/vnd.github.v3.raw'}
    url = 'https://api.github.com/repos/nicolair/math-rapidexos/contents/'
    url += path
    # pour récupérer le contenu d'un fichier non encodé
    r = requests.get(url, headers=rawhead, auth = (user,token))

    code = r.text
    return code

def latexCompilEnonc(listeExosLatex,listeExosPath):
    print("coucou de latexCompil")
    
    path = 'pdf/Enonc_' + session['idSession']
    doc = pylatex.Document(path,
                           documentclass='article',
                           document_options=['a4paper','twocolumn'],
                           geometry_options={'hmargin': '1.1cm', 'vmargin': '2.2cm'})
    #doc = pylatex.Document('listeRapidexo')
    
    #packages
    doc.preamble.append(pylatex.Package('amsmath'))
    doc.preamble.append(pylatex.Package('amssymb'))
    doc.preamble.append(pylatex.Package('stmaryrd'))
    doc.preamble.append(pylatex.Package('babel','french'))
    doc.preamble.append(pylatex.Command('selectlanguage','french'))
    
    #commandes
    def ajoutCmd(str):
        return doc.preamble.append(pylatex.NoEscape(str))
    
    commandes = [r'\columnsep=5pt',
                 r'\newcommand{\N}{\mathbb{N}}',
                 r'\newcommand{\Z}{\mathbb{Z}}',
                 r'\newcommand{\C}{\mathbb{C}}',
                 r'\newcommand{\R}{\mathbb{R}}',
                 r'\newcommand{\K}{\mathbf{K}}',
                 r'\newcommand{\Q}{\mathbb{Q}}',
                 r'\newcommand{\F}{\mathbf{F}}',
                 r'\newcommand{\card}{\mathop{\mathrm{Card}}}',
                 r'\newcommand{\Id}{\mathop{\mathrm{Id}}}',
                 r'\newcommand{\Ker}{\mathop{\mathrm{Ker}}}',
                 r'\newcommand{\Vect}{\mathop{\mathrm{Vect}}}',
                 r'\newcommand{\cotg}{\mathop{\mathrm{cotan}}}',
                 r'\newcommand{\cotan}{\mathop{\mathrm{cotan}}}',
                 r'\newcommand{\sh}{\mathop{\mathrm{sh}}}',
                 r'\newcommand{\ch}{\mathop{\mathrm{ch}}}',
                 r'\renewcommand{\th}{\mathop{\mathrm{th}}}',
                 r'\newcommand{\arcth}{\mathop{\mathrm{arcth}}}',
                 r'\newcommand{\argth}{\mathop{\mathrm{argth}}}',
                 r'\newcommand{\argsh}{\mathop{\mathrm{argsh}}}',
                 r'\newcommand{\argch}{\mathop{\mathrm{argch}}}',
                 r'\renewcommand{\Re}{\mathop{\mathrm{Re}}}',
                 r'\newcommand{\Ima}{\mathop{\mathrm{Im}}}',
                 r'\renewcommand{\Im}{\mathop{\mathrm{Im}}}']

    for cmd in commandes:
        ajoutCmd(cmd)

    #header
    header = pylatex.PageStyle("header")
    with header.create(pylatex.Head('C')):
        header.append(pylatex.basic.LargeText("Rapidexo: énoncés"))
        
    doc.preamble.append(header)
    doc.change_document_style("header")
    
    #formation de la liste    
    #ajout du nom de l'exo au code latex de l'exo
    def ajoutNom(nom,code):
        return r'\begin{tiny}(' + nom + r')\end{tiny} ' + code
    lili = list(map(ajoutNom,listeExosPath,listeExosLatex))
    lili = list(map(pylatex.NoEscape,lili))
    
    with doc.create(pylatex.Enumerate()) as enum:
        for exo in lili:
            enum.add_item(exo)
    
    doc.generate_pdf()





