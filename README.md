# CORBA PDF Service — Projet Académique
## Université USSEIN Kaolack — Licence 2 AGROTIC

---

## 🏗️ Architecture du Système

```
┌─────────────────────────────────────────────────────────────────┐
│                     CORBA PDF Service                           │
│                                                                 │
│  ┌──────────┐    HTTP    ┌──────────────┐   IIOP   ┌─────────┐ │
│  │Navigateur│ ─────────► │ Django 4.2   │ ────────► │Java ORB │ │
│  │          │            │ omniORBpy    │           │PDFBox   │ │
│  └──────────┘            └──────────────┘           └─────────┘ │
│                                │                        │        │
│                                └──── Volume /shared ────┘        │
│                                    (échange IOR CORBA)           │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Démarrage rapide (3 commandes)

```bash
# 1. Cloner / récupérer le projet
cd corba-pdf-project/

# 2. Builder et lancer TOUS les services
docker-compose up --build

# 3. Ouvrir l'interface web
# → http://localhost:8000
```

**C'est tout ! Le système démarre automatiquement :**
- Le serveur Java compile et démarre
- L'IOR est écrit dans le volume partagé `/shared/`
- Django attend l'IOR puis démarre
- L'interface web est disponible sur le port 8000

---

## 📁 Structure du projet

```
corba-pdf-project/
│
├── docker-compose.yml           ← Orchestration Docker
├── .dockerignore
│
├── idl/
│   └── PDFService.idl           ← Interface CORBA (14 méthodes)
│
├── server_java/
│   ├── Dockerfile               ← Java 8 + Maven + PDFBox
│   ├── pom.xml                  ← Dépendances Maven
│   └── src/main/java/com/pdfservice/
│       ├── PDFServer.java       ← Point d'entrée ORB
│       └── PDFServant.java      ← Implémentation PDF (PDFBox)
│
└── django_client/
    ├── Dockerfile               ← Python 3.9 + omniORBpy compilé
    ├── requirements.txt
    ├── entrypoint.sh            ← Attend l'IOR avant de démarrer
    ├── manage.py
    ├── config/
    │   ├── settings.py
    │   └── urls.py
    ├── pdfapp/
    │   ├── views.py             ← 14 vues + API statut
    │   ├── urls.py
    │   └── corba_client.py      ← Client omniORBpy
    └── templates/pdfapp/
        ├── base.html            ← Layout avec sidebar
        ├── index.html           ← Page d'accueil
        ├── result.html          ← Affichage résultats
        └── operations/          ← 14 formulaires
```

---

## 📋 Fonctionnalités disponibles

### Opérations de Base
| # | Endpoint | Description |
|---|----------|-------------|
| 1 | `/merge/` | Fusion de deux PDFs |
| 2 | `/split/` | Découpage par plage de pages |
| 3 | `/extract-pages/` | Extraction de pages spécifiques |
| 4 | `/delete-pages/` | Suppression de pages |
| 5 | `/extract-text/` | Extraction du texte brut |
| 6 | `/create-pdf/` | Création d'un PDF depuis du texte |
| 7 | `/password/` | Protection AES-256 par mot de passe |
| 8 | `/convert-image/` | Conversion page PDF → PNG |

### Fonctionnalités Avancées
| # | Endpoint | Description |
|---|----------|-------------|
| 9 | `/search/` | Recherche de mots-clés |
| 10 | `/watermark/` | Ajout de filigrane diagonal |
| 11 | `/info/` | Statistiques et métadonnées |
| 12 | `/compress/` | Compression du PDF |
| 13 | `/rotate/` | Rotation d'une page |
| 14 | `/reorder/` | Réorganisation des pages |

---

## 🧪 Tests des fonctionnalités

### Via l'interface web
1. Ouvrir `http://localhost:8000`
2. Vérifier le badge **CORBA Connecté** (vert) en haut à droite
3. Cliquer sur une opération dans la grille ou la sidebar
4. Uploader un PDF et valider le formulaire

### Via l'API JSON
```bash
# Vérifier la connexion CORBA
curl http://localhost:8000/api/status/

# Réponse attendue :
# {"corba_connected": true, "server_host": "corba-server", ...}
```

### Commandes Docker utiles
```bash
# Voir les logs du serveur CORBA Java
docker-compose logs corba-server

# Voir les logs Django
docker-compose logs django-client

# Logs en temps réel
docker-compose logs -f

# Arrêter tous les services
docker-compose down

# Rebuild complet (après modification du code)
docker-compose down && docker-compose up --build

# Vérifier l'état des conteneurs
docker-compose ps

# Inspecter le volume partagé (fichier IOR)
docker-compose exec django-client cat /shared/pdfservice.ior
```

---

## 🔧 Technologies utilisées

| Technologie | Version | Rôle |
|-------------|---------|------|
| Java | 8 (JDK) | Serveur CORBA ORB natif |
| Apache PDFBox | 2.0.30 | Manipulation PDF |
| Bouncycastle | 1.70 | Chiffrement AES-256 |
| Python | 3.9 | Client CORBA + backend web |
| omniORB | 4.3.0 | ORB CORBA Python (compilé) |
| Django | 4.2 | Framework web |
| Docker | 24+ | Conteneurisation |
| docker-compose | 3.9 | Orchestration |
| CORBA/IIOP | 3.0 | Protocole de communication |

---

## 📊 Flux CORBA détaillé

```
1. Utilisateur remplit le formulaire Django (upload PDF)
2. Django view lit le fichier en bytes
3. CORBAClient._call() invoque la méthode via omniORBpy
4. omniORBpy encode la requête en IIOP (binary)
5. Le paquet IIOP est envoyé sur TCP port 1050 au serveur Java
6. L'ORB Java reçoit, décode et dispatche vers PDFServant
7. PDFServant exécute la méthode avec Apache PDFBox
8. Le résultat (bytes PDF/texte/image) retourne via IIOP
9. Django reçoit le résultat et affiche la page de résultat
```

---

## ⚠️ Notes importantes

- **Java 8 obligatoire** : L'ORB CORBA natif (`com.sun.corba`) n'est disponible que sous Java 8. C'est pourquoi le Dockerfile du serveur utilise `openjdk:8`.
- **omniORBpy doit être compilé** : Il n'existe pas de wheel pip universel pour omniORBpy, d'où la compilation depuis les sources dans le Dockerfile Django.
- **Volume partagé** : Le fichier IOR (`/shared/pdfservice.ior`) est le mécanisme de découverte de service. Django lit ce fichier pour obtenir l'adresse exacte du serveur CORBA.
- **Attente de démarrage** : Django attend automatiquement que le serveur Java soit prêt avant de démarrer (via `entrypoint.sh`).

---

*Projet réalisé dans le cadre du cours Systèmes Distribués — Licence 2 AGROTIC — USSEIN Kaolack*
