#!/usr/bin/env python3
"""
test_pdf_service.py — Tests automatisés du service CORBA PDF
=========================================================
Ce script teste toutes les opérations via l'API HTTP Django.
Pré-requis : docker-compose up --build (services démarrés)

Utilisation :
    python docs/test_pdf_service.py
"""

import os
import sys
import json
import time
import requests
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────
BASE_URL  = "http://localhost:8000"
TEST_DIR  = Path(__file__).parent / "test_files"
RESULTS   = []

# Couleurs terminal
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"


def log(msg, color=RESET):
    print(f"{color}{msg}{RESET}")


def create_test_pdfs():
    """Crée des PDFs de test via l'API createPDF."""
    log("\n📄 Création des PDFs de test...", CYAN)

    # PDF 1
    r = requests.post(f"{BASE_URL}/create-pdf/", data={
        'title': 'Document Test 1',
        'content': (
            "Chapitre 1 : Introduction à CORBA\n\n"
            "CORBA (Common Object Request Broker Architecture) est un standard "
            "développé par l'OMG pour permettre la communication entre objets "
            "distribués, indépendamment du langage de programmation.\n\n"
            "Le protocole IIOP (Internet Inter-ORB Protocol) est utilisé pour "
            "la communication réseau entre les ORBs.\n\n"
            "Chapitre 2 : Apache PDFBox\n\n"
            "PDFBox est une bibliothèque Java open-source permettant de créer, "
            "modifier et extraire du contenu de documents PDF."
        )
    }, allow_redirects=True)

    if r.status_code == 200 and 'download_url' in r.url or r.history:
        log("  ✓ PDF 1 créé", GREEN)
        return True
    log(f"  ✗ Erreur création PDF : {r.status_code}", RED)
    return False


def test_api_status():
    """Test 0 : Vérification de la connexion CORBA."""
    log("\n🔌 Test 0 : Statut CORBA", CYAN)
    try:
        r = requests.get(f"{BASE_URL}/api/status/", timeout=10)
        data = r.json()
        if data.get('corba_connected'):
            log(f"  ✓ CORBA connecté ({data['server_host']}:{data['server_port']})", GREEN)
            RESULTS.append(('Statut CORBA', True))
        else:
            log(f"  ✗ CORBA non connecté : {data}", RED)
            RESULTS.append(('Statut CORBA', False))
    except Exception as e:
        log(f"  ✗ Erreur : {e}", RED)
        RESULTS.append(('Statut CORBA', False))


def test_create_pdf():
    """Test 1 : Création de PDF."""
    log("\n✨ Test 1 : Création de PDF", CYAN)
    try:
        r = requests.post(f"{BASE_URL}/create-pdf/", data={
            'title': 'Test CORBA PDF',
            'content': 'Contenu de test pour le système CORBA.\nLigne 2.\nLigne 3.'
        }, allow_redirects=True, timeout=30)
        success = r.status_code == 200 and 'Création' in r.text
        log(f"  {'✓' if success else '✗'} createPDF : HTTP {r.status_code}", GREEN if success else RED)
        RESULTS.append(('createPDF', success))
        return success
    except Exception as e:
        log(f"  ✗ Erreur : {e}", RED)
        RESULTS.append(('createPDF', False))
        return False


def test_extract_text(pdf_file_path):
    """Test 2 : Extraction de texte."""
    log("\n📝 Test 2 : Extraction de texte", CYAN)
    try:
        with open(pdf_file_path, 'rb') as f:
            r = requests.post(f"{BASE_URL}/extract-text/",
                files={'pdf': ('test.pdf', f, 'application/pdf')},
                allow_redirects=True, timeout=30)
        success = r.status_code == 200 and 'Extraction' in r.text
        log(f"  {'✓' if success else '✗'} extractText : HTTP {r.status_code}", GREEN if success else RED)
        RESULTS.append(('extractText', success))
    except Exception as e:
        log(f"  ✗ Erreur : {e}", RED)
        RESULTS.append(('extractText', False))


def test_pdf_info(pdf_file_path):
    """Test 3 : Statistiques PDF."""
    log("\n📊 Test 3 : Statistiques PDF", CYAN)
    try:
        with open(pdf_file_path, 'rb') as f:
            r = requests.post(f"{BASE_URL}/info/",
                files={'pdf': ('test.pdf', f, 'application/pdf')},
                allow_redirects=True, timeout=30)
        success = r.status_code == 200 and 'Statistiques' in r.text
        log(f"  {'✓' if success else '✗'} getPDFInfo : HTTP {r.status_code}", GREEN if success else RED)
        RESULTS.append(('getPDFInfo', success))
    except Exception as e:
        log(f"  ✗ Erreur : {e}", RED)
        RESULTS.append(('getPDFInfo', False))


def test_watermark(pdf_file_path):
    """Test 4 : Ajout de filigrane."""
    log("\n💧 Test 4 : Filigrane", CYAN)
    try:
        with open(pdf_file_path, 'rb') as f:
            r = requests.post(f"{BASE_URL}/watermark/",
                files={'pdf': ('test.pdf', f, 'application/pdf')},
                data={'watermark_text': 'TEST CORBA'},
                allow_redirects=True, timeout=30)
        success = r.status_code == 200 and 'Filigrane' in r.text
        log(f"  {'✓' if success else '✗'} addWatermark : HTTP {r.status_code}", GREEN if success else RED)
        RESULTS.append(('addWatermark', success))
    except Exception as e:
        log(f"  ✗ Erreur : {e}", RED)
        RESULTS.append(('addWatermark', False))


def test_compress(pdf_file_path):
    """Test 5 : Compression PDF."""
    log("\n📦 Test 5 : Compression", CYAN)
    try:
        with open(pdf_file_path, 'rb') as f:
            r = requests.post(f"{BASE_URL}/compress/",
                files={'pdf': ('test.pdf', f, 'application/pdf')},
                allow_redirects=True, timeout=30)
        success = r.status_code == 200 and 'Compression' in r.text
        log(f"  {'✓' if success else '✗'} compressPDF : HTTP {r.status_code}", GREEN if success else RED)
        RESULTS.append(('compressPDF', success))
    except Exception as e:
        log(f"  ✗ Erreur : {e}", RED)
        RESULTS.append(('compressPDF', False))


def test_search_text(pdf_file_path):
    """Test 6 : Recherche de texte."""
    log("\n🔍 Test 6 : Recherche de texte", CYAN)
    try:
        with open(pdf_file_path, 'rb') as f:
            r = requests.post(f"{BASE_URL}/search/",
                files={'pdf': ('test.pdf', f, 'application/pdf')},
                data={'keyword': 'CORBA'},
                allow_redirects=True, timeout=30)
        success = r.status_code == 200 and 'Recherche' in r.text
        log(f"  {'✓' if success else '✗'} searchText : HTTP {r.status_code}", GREEN if success else RED)
        RESULTS.append(('searchText', success))
    except Exception as e:
        log(f"  ✗ Erreur : {e}", RED)
        RESULTS.append(('searchText', False))


def test_convert_image(pdf_file_path):
    """Test 7 : Conversion PDF → Image."""
    log("\n🖼️ Test 7 : Conversion en image", CYAN)
    try:
        with open(pdf_file_path, 'rb') as f:
            r = requests.post(f"{BASE_URL}/convert-image/",
                files={'pdf': ('test.pdf', f, 'application/pdf')},
                data={'page_number': '1', 'dpi': '96'},
                allow_redirects=True, timeout=60)
        success = r.status_code == 200 and 'Conversion' in r.text
        log(f"  {'✓' if success else '✗'} convertToImage : HTTP {r.status_code}", GREEN if success else RED)
        RESULTS.append(('convertToImage', success))
    except Exception as e:
        log(f"  ✗ Erreur : {e}", RED)
        RESULTS.append(('convertToImage', False))


def print_summary():
    """Affiche le résumé des tests."""
    log("\n" + "═"*50, BOLD)
    log("  RÉSUMÉ DES TESTS — CORBA PDF SERVICE", BOLD)
    log("═"*50, BOLD)

    passed = sum(1 for _, ok in RESULTS if ok)
    total  = len(RESULTS)

    for name, ok in RESULTS:
        status = f"{GREEN}✓ PASS{RESET}" if ok else f"{RED}✗ FAIL{RESET}"
        print(f"  {status}  {name}")

    log("─"*50)
    color = GREEN if passed == total else (YELLOW if passed > 0 else RED)
    log(f"  Résultat : {passed}/{total} tests passés", color)
    log("═"*50)

    if passed == total:
        log("  🎉 Tous les tests réussis !", GREEN)
    elif passed > 0:
        log("  ⚠️  Certains tests ont échoué", YELLOW)
    else:
        log("  ❌ Tous les tests ont échoué — CORBA démarré ?", RED)
        log("     → docker-compose up --build", YELLOW)


def wait_for_django(max_wait=120):
    """Attend que Django soit disponible."""
    log(f"\n⏳ Attente du démarrage de Django ({BASE_URL})...", YELLOW)
    for i in range(max_wait // 2):
        try:
            r = requests.get(BASE_URL, timeout=3)
            if r.status_code == 200:
                log("  ✓ Django est prêt !", GREEN)
                return True
        except Exception:
            pass
        print(f"  Tentative {i+1}/{max_wait//2}...", end='\r')
        time.sleep(2)
    log("  ✗ Django n'a pas démarré dans les temps", RED)
    return False


if __name__ == '__main__':
    log(f"\n{BOLD}{'═'*55}", CYAN)
    log("  TESTS AUTOMATISÉS — CORBA PDF SERVICE", CYAN)
    log(f"  Cible : {BASE_URL}", CYAN)
    log(f"{'═'*55}{RESET}", CYAN)

    # Attendre Django
    if not wait_for_django():
        sys.exit(1)

    # Créer un PDF de test minimal (sans fichier externe)
    test_pdf = None

    # Test 0 : Statut
    test_api_status()

    # Test 1 : Créer un PDF (ne nécessite pas de fichier en entrée)
    if test_create_pdf():
        log("  → Utilisez un fichier PDF pour les autres tests", YELLOW)
        log("  → Placez un fichier 'test.pdf' dans docs/test_files/", YELLOW)

        test_pdf_path = TEST_DIR / "test.pdf"
        if test_pdf_path.exists():
            log(f"  ✓ Fichier test trouvé : {test_pdf_path}", GREEN)
            test_extract_text(test_pdf_path)
            test_pdf_info(test_pdf_path)
            test_watermark(test_pdf_path)
            test_compress(test_pdf_path)
            test_search_text(test_pdf_path)
            test_convert_image(test_pdf_path)
        else:
            log(f"\n  ℹ️  Aucun fichier test.pdf trouvé dans {TEST_DIR}", YELLOW)
            log("  Les tests nécessitant un PDF d'entrée sont ignorés.", YELLOW)

    print_summary()
