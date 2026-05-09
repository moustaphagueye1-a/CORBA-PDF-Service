"""
views.py — Vues Django du service CORBA PDF
=====================================================================
Chaque vue :
  1. Reçoit la requête HTTP (formulaire + fichiers uploadés)
  2. Lit les fichiers PDF en mémoire (bytes)
  3. Appelle le client CORBA correspondant
  4. Retourne le résultat (fichier téléchargeable, texte, JSON, image)

Gestion des erreurs :
  - Toutes les exceptions CORBA sont catchées et affichées à l'utilisateur
  - Les messages Django (messages framework) informent du succès/échec
"""

import os
import json
import base64
import logging
import tempfile
from datetime import datetime

from django.shortcuts import render, redirect
from django.http import (
    HttpResponse, JsonResponse, Http404
)
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.conf import settings

from .corba_client import CORBAClient

logger = logging.getLogger(__name__)


# ── Utilitaire : instance partagée du client CORBA ─────────────────
def get_client():
    return CORBAClient()


def _save_result(data: bytes, filename: str) -> str:
    """
    Sauvegarde un fichier résultat dans MEDIA_ROOT/results/
    Retourne le chemin relatif (pour l'URL de téléchargement).
    """
    results_dir = os.path.join(settings.MEDIA_ROOT, 'results')
    os.makedirs(results_dir, exist_ok=True)
    filepath = os.path.join(results_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(data)
    return f'/media/results/{filename}'


def _timestamp():
    return datetime.now().strftime('%Y%m%d_%H%M%S')


# ================================================================
#  Page d'accueil
# ================================================================

def index(request):
    """Page d'accueil : grille des 14 opérations + statut CORBA."""
    client = get_client()
    context = {
        'corba_connected': client.check_connection(),
        'arch': [
            ('Navigateur', '🌐', '#eff6ff'),
            ('Django',     '🐍', '#f0fdf4'),
            ('omniORBpy',  '🔌', '#faf5ff'),
            ('Java ORB',   '☕', '#fff7ed'),
            ('PDFBox',     '📦', '#fef2f2'),
        ],
        'operations': [
            ('/merge/',         '🔗', 'Fusion PDF',          'Combiner deux PDFs en un seul fichier'),
            ('/split/',         '✂️',  'Découpage PDF',       'Extraire une plage de pages continues'),
            ('/extract-pages/', '📄', 'Extraction de pages', 'Sélectionner des pages spécifiques'),
            ('/delete-pages/',  '🗑️', 'Suppression pages',   'Retirer des pages indésirables'),
            ('/extract-text/',  '📝', 'Extraction texte',    'Extraire tout le texte brut du PDF'),
            ('/create-pdf/',    '✨', 'Créer un PDF',        'Générer un PDF depuis du texte'),
            ('/password/',      '🔐', 'Mot de passe',        'Chiffrement AES-256 par mot de passe'),
            ('/convert-image/', '🖼️', 'PDF → Image PNG',     'Convertir une page en image'),
            ('/search/',        '🔍', 'Recherche texte',     'Chercher des mots-clés dans le PDF'),
            ('/watermark/',     '💧', 'Filigrane',           'Watermark diagonal sur chaque page'),
            ('/info/',          '📊', 'Statistiques',        'Métadonnées et analyse du document'),
            ('/compress/',      '📦', 'Compression',         'Réduire la taille du fichier PDF'),
            ('/rotate/',        '🔄', 'Rotation de page',    'Pivoter une page (90°/180°/270°)'),
            ('/reorder/',       '🔀', 'Réorganisation',      "Changer l'ordre des pages"),
        ],
    }
    return render(request, 'pdfapp/index.html', context)


# ================================================================
#  OPÉRATION 1 — Fusion de PDFs
# ================================================================

def merge_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/merge.html')

    try:
        pdf1 = request.FILES['pdf1'].read()
        pdf2 = request.FILES['pdf2'].read()

        result = get_client().merge_pdfs(pdf1, pdf2)

        filename = f'fusion_{_timestamp()}.pdf'
        url = _save_result(result, filename)
        return render(request, 'pdfapp/result.html', {
            'operation': 'Fusion PDF',
            'success': True,
            'download_url': url,
            'filename': filename,
            'file_size': len(result),
            'message': f'Fusion réussie ! Fichier de {len(result):,} octets généré.',
        })

    except KeyError as e:
        messages.error(request, f'Fichier manquant : {e}')
    except Exception as e:
        logger.error(f"Erreur merge: {e}")
        messages.error(request, f'Erreur CORBA : {e}')
    return redirect('merge')


# ================================================================
#  OPÉRATION 2 — Découpage de PDF
# ================================================================

def split_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/split.html')

    try:
        pdf       = request.FILES['pdf'].read()
        from_page = int(request.POST.get('from_page', 1))
        to_page   = int(request.POST.get('to_page', 1))

        result   = get_client().split_pdf(pdf, from_page, to_page)
        filename = f'decoupage_p{from_page}-{to_page}_{_timestamp()}.pdf'
        url      = _save_result(result, filename)

        return render(request, 'pdfapp/result.html', {
            'operation': 'Découpage PDF',
            'success': True,
            'download_url': url,
            'filename': filename,
            'file_size': len(result),
            'message': f'Découpage réussi (pages {from_page} à {to_page}).',
        })

    except Exception as e:
        logger.error(f"Erreur split: {e}")
        messages.error(request, f'Erreur : {e}')
    return redirect('split')


# ================================================================
#  OPÉRATION 3 — Extraction de pages
# ================================================================

def extract_pages_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/extract_pages.html')

    try:
        pdf          = request.FILES['pdf'].read()
        pages_input  = request.POST.get('pages', '')
        # Accepte "1,3,5" ou "1 3 5" ou "1-3" (simplifié : virgule et espace)
        pages_raw    = pages_input.replace(' ', ',').split(',')
        page_numbers = [int(p.strip()) for p in pages_raw if p.strip().isdigit()]

        if not page_numbers:
            raise ValueError("Aucun numéro de page valide fourni.")

        result   = get_client().extract_pages(pdf, page_numbers)
        filename = f'extraction_{_timestamp()}.pdf'
        url      = _save_result(result, filename)

        return render(request, 'pdfapp/result.html', {
            'operation': 'Extraction de pages',
            'success': True,
            'download_url': url,
            'filename': filename,
            'file_size': len(result),
            'message': f'Pages {page_numbers} extraites avec succès.',
        })

    except Exception as e:
        logger.error(f"Erreur extract_pages: {e}")
        messages.error(request, f'Erreur : {e}')
    return redirect('extract_pages')


# ================================================================
#  OPÉRATION 4 — Suppression de pages
# ================================================================

def delete_pages_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/delete_pages.html')

    try:
        pdf         = request.FILES['pdf'].read()
        pages_input = request.POST.get('pages', '')
        pages_raw   = pages_input.replace(' ', ',').split(',')
        page_numbers = [int(p.strip()) for p in pages_raw if p.strip().isdigit()]

        if not page_numbers:
            raise ValueError("Aucun numéro de page valide fourni.")

        result   = get_client().delete_pages(pdf, page_numbers)
        filename = f'suppression_{_timestamp()}.pdf'
        url      = _save_result(result, filename)

        return render(request, 'pdfapp/result.html', {
            'operation': 'Suppression de pages',
            'success': True,
            'download_url': url,
            'filename': filename,
            'file_size': len(result),
            'message': f'Pages {page_numbers} supprimées avec succès.',
        })

    except Exception as e:
        logger.error(f"Erreur delete_pages: {e}")
        messages.error(request, f'Erreur : {e}')
    return redirect('delete_pages')


# ================================================================
#  OPÉRATION 5 — Extraction de texte
# ================================================================

def extract_text_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/extract_text.html')

    try:
        pdf  = request.FILES['pdf'].read()
        text = get_client().extract_text(pdf)

        return render(request, 'pdfapp/result.html', {
            'operation': 'Extraction de texte',
            'success': True,
            'text_result': text,
            'text_length': len(text),
            'word_count': len(text.split()) if text.strip() else 0,
            'message': f'{len(text.split()):,} mots extraits.',
        })

    except Exception as e:
        logger.error(f"Erreur extract_text: {e}")
        messages.error(request, f'Erreur : {e}')
    return redirect('extract_text')


# ================================================================
#  OPÉRATION 6 — Création de PDF
# ================================================================

def create_pdf_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/create_pdf.html')

    try:
        content  = request.POST.get('content', '')
        title    = request.POST.get('title', 'Document sans titre')

        if not content.strip():
            raise ValueError("Le contenu ne peut pas être vide.")

        result   = get_client().create_pdf(content, title)
        filename = f'creation_{_timestamp()}.pdf'
        url      = _save_result(result, filename)

        return render(request, 'pdfapp/result.html', {
            'operation': 'Création de PDF',
            'success': True,
            'download_url': url,
            'filename': filename,
            'file_size': len(result),
            'message': f'PDF "{title}" créé avec succès ({len(result):,} octets).',
        })

    except Exception as e:
        logger.error(f"Erreur create_pdf: {e}")
        messages.error(request, f'Erreur : {e}')
    return redirect('create_pdf')


# ================================================================
#  OPÉRATION 7 — Ajout de mot de passe
# ================================================================

def password_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/password.html')

    try:
        pdf            = request.FILES['pdf'].read()
        user_password  = request.POST.get('user_password', '')
        owner_password = request.POST.get('owner_password', '') or user_password

        if not user_password:
            raise ValueError("Le mot de passe utilisateur est obligatoire.")

        result   = get_client().add_password(pdf, user_password, owner_password)
        filename = f'protege_{_timestamp()}.pdf'
        url      = _save_result(result, filename)

        return render(request, 'pdfapp/result.html', {
            'operation': 'Protection par mot de passe',
            'success': True,
            'download_url': url,
            'filename': filename,
            'file_size': len(result),
            'message': 'PDF protégé avec succès (chiffrement AES-256).',
        })

    except Exception as e:
        logger.error(f"Erreur password: {e}")
        messages.error(request, f'Erreur : {e}')
    return redirect('password')


# ================================================================
#  OPÉRATION 8 — Conversion PDF → Image
# ================================================================

def convert_image_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/convert_image.html')

    try:
        pdf         = request.FILES['pdf'].read()
        page_number = int(request.POST.get('page_number', 1))
        dpi         = int(request.POST.get('dpi', 150))

        # Limiter le DPI pour éviter des images trop lourdes
        dpi = min(max(dpi, 72), 300)

        result   = get_client().convert_to_image(pdf, page_number, dpi)
        filename = f'image_p{page_number}_{_timestamp()}.png'
        url      = _save_result(result, filename)

        # Encoder en base64 pour l'affichage inline dans le template
        b64_image = base64.b64encode(result).decode('utf-8')

        return render(request, 'pdfapp/result.html', {
            'operation': 'Conversion PDF → Image',
            'success': True,
            'download_url': url,
            'filename': filename,
            'file_size': len(result),
            'image_b64': b64_image,
            'image_mime': 'image/png',
            'message': f'Page {page_number} convertie en PNG ({dpi} DPI).',
        })

    except Exception as e:
        logger.error(f"Erreur convert_image: {e}")
        messages.error(request, f'Erreur : {e}')
    return redirect('convert_image')


# ================================================================
#  OPÉRATION 9 — Recherche de texte
# ================================================================

def search_text_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/search_text.html')

    try:
        pdf     = request.FILES['pdf'].read()
        keyword = request.POST.get('keyword', '').strip()

        if not keyword:
            raise ValueError("Le mot-clé de recherche est obligatoire.")

        results = get_client().search_text(pdf, keyword)

        return render(request, 'pdfapp/result.html', {
            'operation': 'Recherche de texte',
            'success': True,
            'search_results': results,
            'keyword': keyword,
            'result_count': len(results),
            'message': f'{len(results)} occurrence(s) de "{keyword}" trouvée(s).',
        })

    except Exception as e:
        logger.error(f"Erreur search_text: {e}")
        messages.error(request, f'Erreur : {e}')
    return redirect('search_text')


# ================================================================
#  OPÉRATION 10 — Ajout de filigrane
# ================================================================

def watermark_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/watermark.html')

    try:
        pdf            = request.FILES['pdf'].read()
        watermark_text = request.POST.get('watermark_text', 'CONFIDENTIEL')

        if not watermark_text.strip():
            watermark_text = 'CONFIDENTIEL'

        result   = get_client().add_watermark(pdf, watermark_text)
        filename = f'watermark_{_timestamp()}.pdf'
        url      = _save_result(result, filename)

        return render(request, 'pdfapp/result.html', {
            'operation': 'Ajout de filigrane',
            'success': True,
            'download_url': url,
            'filename': filename,
            'file_size': len(result),
            'message': f'Filigrane "{watermark_text}" ajouté sur toutes les pages.',
        })

    except Exception as e:
        logger.error(f"Erreur watermark: {e}")
        messages.error(request, f'Erreur : {e}')
    return redirect('watermark')


# ================================================================
#  OPÉRATION 11 — Statistiques du PDF
# ================================================================

def pdf_info_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/pdf_info.html')

    try:
        pdf  = request.FILES['pdf'].read()
        info = get_client().get_pdf_info(pdf)

        # Taille humainement lisible
        size_kb = info['file_size'] / 1024
        size_str = f"{size_kb:.1f} Ko" if size_kb < 1024 else f"{size_kb/1024:.2f} Mo"
        info['file_size_human'] = size_str

        return render(request, 'pdfapp/result.html', {
            'operation': 'Statistiques du PDF',
            'success': True,
            'pdf_info': info,
            'message': f'Analyse complète : {info["page_count"]} pages, {info["word_count"]:,} mots.',
        })

    except Exception as e:
        logger.error(f"Erreur pdf_info: {e}")
        messages.error(request, f'Erreur : {e}')
    return redirect('pdf_info')


# ================================================================
#  OPÉRATION 12 — Compression PDF
# ================================================================

def compress_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/compress.html')

    try:
        pdf           = request.FILES['pdf'].read()
        original_size = len(pdf)

        result           = get_client().compress_pdf(pdf)
        compressed_size  = len(result)
        savings          = original_size - compressed_size
        savings_pct      = (savings / original_size * 100) if original_size > 0 else 0

        filename = f'compresse_{_timestamp()}.pdf'
        url      = _save_result(result, filename)

        return render(request, 'pdfapp/result.html', {
            'operation': 'Compression PDF',
            'success': True,
            'download_url': url,
            'filename': filename,
            'file_size': compressed_size,
            'original_size': original_size,
            'savings': savings,
            'savings_pct': f'{savings_pct:.1f}',
            'message': (
                f'Compression réussie : {original_size:,} → {compressed_size:,} octets '
                f'({savings_pct:.1f}% de réduction).'
            ),
        })

    except Exception as e:
        logger.error(f"Erreur compress: {e}")
        messages.error(request, f'Erreur : {e}')
    return redirect('compress')


# ================================================================
#  OPÉRATION 13 — Rotation de page
# ================================================================

def rotate_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/rotate.html')

    try:
        pdf         = request.FILES['pdf'].read()
        page_number = int(request.POST.get('page_number', 1))
        degrees     = int(request.POST.get('degrees', 90))

        result   = get_client().rotate_page(pdf, page_number, degrees)
        filename = f'rotation_p{page_number}_{degrees}deg_{_timestamp()}.pdf'
        url      = _save_result(result, filename)

        return render(request, 'pdfapp/result.html', {
            'operation': 'Rotation de page',
            'success': True,
            'download_url': url,
            'filename': filename,
            'file_size': len(result),
            'message': f'Page {page_number} pivotée de {degrees}° avec succès.',
        })

    except Exception as e:
        logger.error(f"Erreur rotate: {e}")
        messages.error(request, f'Erreur : {e}')
    return redirect('rotate')


# ================================================================
#  OPÉRATION 14 — Réorganisation des pages
# ================================================================

def reorder_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/reorder.html')

    try:
        pdf         = request.FILES['pdf'].read()
        order_input = request.POST.get('order', '')
        order_raw   = order_input.replace(' ', ',').split(',')
        new_order   = [int(p.strip()) for p in order_raw if p.strip().isdigit()]

        if not new_order:
            raise ValueError("Aucun ordre de pages valide fourni.")

        result   = get_client().reorder_pages(pdf, new_order)
        filename = f'reordonne_{_timestamp()}.pdf'
        url      = _save_result(result, filename)

        return render(request, 'pdfapp/result.html', {
            'operation': 'Réorganisation des pages',
            'success': True,
            'download_url': url,
            'filename': filename,
            'file_size': len(result),
            'message': f'Pages réorganisées selon l\'ordre : {new_order}.',
        })

    except Exception as e:
        logger.error(f"Erreur reorder: {e}")
        messages.error(request, f'Erreur : {e}')
    return redirect('reorder')


# ================================================================
#  API JSON — Statut CORBA
# ================================================================

def api_status(request):
    """Endpoint JSON pour vérifier l'état de la connexion CORBA."""
    client = get_client()
    connected = client.check_connection()
    return JsonResponse({
        'corba_connected': connected,
        'server_host': settings.CORBA_SERVER_HOST,
        'server_port': settings.CORBA_SERVER_PORT,
        'ior_file': settings.CORBA_IOR_FILE,
        'ior_exists': os.path.exists(settings.CORBA_IOR_FILE),
    })
