"""
views.py — Vues Django du service CORBA PDF
En production : retourne les fichiers directement via HttpResponse
(pas de sauvegarde sur disque → pas de problème de serving media)
"""

import os
import base64
import logging
from datetime import datetime

from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.conf import settings

from .corba_client import CORBAClient

logger = logging.getLogger(__name__)


def get_client():
    return CORBAClient()


def _timestamp():
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def _pdf_response(data: bytes, filename: str) -> HttpResponse:
    """Retourne un PDF directement en téléchargement — pas de fichier disque."""
    response = HttpResponse(data, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _png_response(data: bytes, filename: str) -> HttpResponse:
    """Retourne une image PNG directement."""
    response = HttpResponse(data, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ================================================================
#  Page d'accueil
# ================================================================

def index(request):
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
#  OPÉRATION 1 — Fusion
# ================================================================
def merge_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/merge.html')
    try:
        pdf1 = request.FILES['pdf1'].read()
        pdf2 = request.FILES['pdf2'].read()
        result = get_client().merge_pdfs(pdf1, pdf2)
        return _pdf_response(result, f'fusion_{_timestamp()}.pdf')
    except Exception as e:
        messages.error(request, f'Erreur : {e}')
    return redirect('merge')


# ================================================================
#  OPÉRATION 2 — Découpage
# ================================================================
def split_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/split.html')
    try:
        pdf       = request.FILES['pdf'].read()
        from_page = int(request.POST.get('from_page', 1))
        to_page   = int(request.POST.get('to_page', 1))
        result = get_client().split_pdf(pdf, from_page, to_page)
        return _pdf_response(result, f'decoupage_p{from_page}-{to_page}_{_timestamp()}.pdf')
    except Exception as e:
        messages.error(request, f'Erreur : {e}')
    return redirect('split')


# ================================================================
#  OPÉRATION 3 — Extraction de pages
# ================================================================
def extract_pages_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/extract_pages.html')
    try:
        pdf         = request.FILES['pdf'].read()
        pages_input = request.POST.get('pages', '')
        page_numbers = [int(p.strip()) for p in pages_input.replace(' ',',').split(',') if p.strip().isdigit()]
        if not page_numbers:
            raise ValueError("Aucun numéro de page valide.")
        result = get_client().extract_pages(pdf, page_numbers)
        return _pdf_response(result, f'extraction_{_timestamp()}.pdf')
    except Exception as e:
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
        page_numbers = [int(p.strip()) for p in pages_input.replace(' ',',').split(',') if p.strip().isdigit()]
        if not page_numbers:
            raise ValueError("Aucun numéro de page valide.")
        result = get_client().delete_pages(pdf, page_numbers)
        return _pdf_response(result, f'suppression_{_timestamp()}.pdf')
    except Exception as e:
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
        messages.error(request, f'Erreur : {e}')
    return redirect('extract_text')


# ================================================================
#  OPÉRATION 6 — Création de PDF
# ================================================================
def create_pdf_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/create_pdf.html')
    try:
        content = request.POST.get('content', '')
        title   = request.POST.get('title', 'Document sans titre')
        if not content.strip():
            raise ValueError("Le contenu ne peut pas être vide.")
        result = get_client().create_pdf(content, title)
        return _pdf_response(result, f'creation_{_timestamp()}.pdf')
    except Exception as e:
        messages.error(request, f'Erreur : {e}')
    return redirect('create_pdf')


# ================================================================
#  OPÉRATION 7 — Mot de passe
# ================================================================
def password_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/password.html')
    try:
        pdf            = request.FILES['pdf'].read()
        user_password  = request.POST.get('user_password', '')
        owner_password = request.POST.get('owner_password', '') or user_password
        if not user_password:
            raise ValueError("Le mot de passe est obligatoire.")
        result = get_client().add_password(pdf, user_password, owner_password)
        return _pdf_response(result, f'protege_{_timestamp()}.pdf')
    except Exception as e:
        messages.error(request, f'Erreur : {e}')
    return redirect('password')


# ================================================================
#  OPÉRATION 8 — Conversion en image
# ================================================================
def convert_image_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/convert_image.html')
    try:
        pdf         = request.FILES['pdf'].read()
        page_number = int(request.POST.get('page_number', 1))
        dpi         = int(request.POST.get('dpi', 150))
        dpi = min(max(dpi, 72), 300)
        result = get_client().convert_to_image(pdf, page_number, dpi)

        # Afficher dans le template avec aperçu
        b64_image = base64.b64encode(result).decode('utf-8')
        return render(request, 'pdfapp/result.html', {
            'operation': 'Conversion PDF → Image',
            'success': True,
            'image_b64': b64_image,
            'image_mime': 'image/png',
            'image_data': result,
            'filename': f'image_p{page_number}_{_timestamp()}.png',
            'file_size': len(result),
            'message': f'Page {page_number} convertie en PNG ({dpi} DPI).',
        })
    except Exception as e:
        messages.error(request, f'Erreur : {e}')
    return redirect('convert_image')


# ================================================================
#  OPÉRATION 9 — Recherche
# ================================================================
def search_text_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/search_text.html')
    try:
        pdf     = request.FILES['pdf'].read()
        keyword = request.POST.get('keyword', '').strip()
        if not keyword:
            raise ValueError("Le mot-clé est obligatoire.")
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
        messages.error(request, f'Erreur : {e}')
    return redirect('search_text')


# ================================================================
#  OPÉRATION 10 — Filigrane
# ================================================================
def watermark_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/watermark.html')
    try:
        pdf            = request.FILES['pdf'].read()
        watermark_text = request.POST.get('watermark_text', 'CONFIDENTIEL')
        result = get_client().add_watermark(pdf, watermark_text)
        return _pdf_response(result, f'watermark_{_timestamp()}.pdf')
    except Exception as e:
        messages.error(request, f'Erreur : {e}')
    return redirect('watermark')


# ================================================================
#  OPÉRATION 11 — Statistiques
# ================================================================
def pdf_info_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/pdf_info.html')
    try:
        pdf  = request.FILES['pdf'].read()
        info = get_client().get_pdf_info(pdf)
        size_kb = info['file_size'] / 1024
        info['file_size_human'] = f"{size_kb:.1f} Ko" if size_kb < 1024 else f"{size_kb/1024:.2f} Mo"
        return render(request, 'pdfapp/result.html', {
            'operation': 'Statistiques du PDF',
            'success': True,
            'pdf_info': info,
            'message': f'Analyse : {info["page_count"]} pages, {info["word_count"]:,} mots.',
        })
    except Exception as e:
        messages.error(request, f'Erreur : {e}')
    return redirect('pdf_info')


# ================================================================
#  OPÉRATION 12 — Compression
# ================================================================
def compress_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/compress.html')
    try:
        pdf           = request.FILES['pdf'].read()
        original_size = len(pdf)
        result        = get_client().compress_pdf(pdf)
        compressed    = len(result)
        pct = (original_size - compressed) / original_size * 100 if original_size > 0 else 0
        response = _pdf_response(result, f'compresse_{_timestamp()}.pdf')
        # Ajouter les stats dans un header custom
        response['X-Original-Size'] = str(original_size)
        response['X-Compressed-Size'] = str(compressed)
        return response
    except Exception as e:
        messages.error(request, f'Erreur : {e}')
    return redirect('compress')


# ================================================================
#  OPÉRATION 13 — Rotation
# ================================================================
def rotate_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/rotate.html')
    try:
        pdf         = request.FILES['pdf'].read()
        page_number = int(request.POST.get('page_number', 1))
        degrees     = int(request.POST.get('degrees', 90))
        result = get_client().rotate_page(pdf, page_number, degrees)
        return _pdf_response(result, f'rotation_p{page_number}_{degrees}deg_{_timestamp()}.pdf')
    except Exception as e:
        messages.error(request, f'Erreur : {e}')
    return redirect('rotate')


# ================================================================
#  OPÉRATION 14 — Réorganisation
# ================================================================
def reorder_view(request):
    if request.method == 'GET':
        return render(request, 'pdfapp/operations/reorder.html')
    try:
        pdf       = request.FILES['pdf'].read()
        order_raw = request.POST.get('order', '').replace(' ',',').split(',')
        new_order = [int(p.strip()) for p in order_raw if p.strip().isdigit()]
        if not new_order:
            raise ValueError("Aucun ordre valide fourni.")
        result = get_client().reorder_pages(pdf, new_order)
        return _pdf_response(result, f'reordonne_{_timestamp()}.pdf')
    except Exception as e:
        messages.error(request, f'Erreur : {e}')
    return redirect('reorder')


# ================================================================
#  API statut CORBA
# ================================================================
def api_status(request):
    client = get_client()
    return JsonResponse({
        'corba_connected': client.check_connection(),
        'server_host': os.environ.get('CORBA_SERVER_HOST', 'localhost'),
        'server_port': os.environ.get('BRIDGE_PORT', '8080'),
    })