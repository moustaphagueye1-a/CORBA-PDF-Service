"""
corba_client.py — Client HTTP vers le pont Java CORBA
======================================================
Le serveur Java expose un pont HTTP sur le port 8080.
Ce module appelle ce pont avec requests (pas d'omniORBpy requis).

La classe CORBAClient garde exactement la même interface
qu'avant — les views.py n'ont pas besoin de changer.

Architecture :
  Django → requests (HTTP/JSON) → Java HttpBridge → PDFServant (CORBA)
"""

import os
import base64
import logging
import time
from typing import List

import requests

logger = logging.getLogger(__name__)

BRIDGE_HOST = os.environ.get('CORBA_SERVER_HOST', 'corba-server')
BRIDGE_PORT = int(os.environ.get('BRIDGE_PORT', '8080'))
BASE_URL    = f"http://{BRIDGE_HOST}:{BRIDGE_PORT}"
TIMEOUT     = 120  # secondes


def _b64(data: bytes) -> str:
    """bytes → base64 string"""
    return base64.b64encode(data).decode('utf-8')


def _post(endpoint: str, payload: dict) -> dict:
    """Appel HTTP POST vers le pont Java. Lève RuntimeError si erreur."""
    url = f"{BASE_URL}/{endpoint}"
    try:
        resp = requests.post(url, json=payload, timeout=TIMEOUT)
        data = resp.json()
        if not data.get('ok'):
            raise RuntimeError(data.get('error', 'Erreur inconnue du serveur CORBA'))
        return data
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Impossible de joindre le serveur CORBA sur {BASE_URL}.\n"
            "Vérifiez que docker-compose est lancé."
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("Timeout : le serveur CORBA met trop de temps à répondre.")


def _file(data: dict) -> bytes:
    """Extrait et décode le fichier PDF de la réponse JSON."""
    return base64.b64decode(data['data'])


class CORBAClient:
    """
    Client HTTP vers le pont Java CORBA.
    Interface identique à l'ancienne version omniORBpy.
    """

    def check_connection(self) -> bool:
        try:
            r = requests.get(f"{BASE_URL}/status", timeout=5)
            return r.json().get('ok', False)
        except Exception:
            return False

    # ── Opérations de Base ─────────────────────────────────────────

    def merge_pdfs(self, pdf1: bytes, pdf2: bytes) -> bytes:
        return _file(_post('merge', {'pdf1': _b64(pdf1), 'pdf2': _b64(pdf2)}))

    def split_pdf(self, pdf: bytes, from_page: int, to_page: int) -> bytes:
        return _file(_post('split', {'pdf': _b64(pdf), 'from_page': from_page, 'to_page': to_page}))

    def extract_pages(self, pdf: bytes, page_numbers: List[int]) -> bytes:
        return _file(_post('extract-pages', {'pdf': _b64(pdf), 'pages': page_numbers}))

    def delete_pages(self, pdf: bytes, page_numbers: List[int]) -> bytes:
        return _file(_post('delete-pages', {'pdf': _b64(pdf), 'pages': page_numbers}))

    def extract_text(self, pdf: bytes) -> str:
        return _post('extract-text', {'pdf': _b64(pdf)})['text']

    def create_pdf(self, content: str, title: str) -> bytes:
        return _file(_post('create-pdf', {'content': content, 'title': title}))

    def add_password(self, pdf: bytes, user_pwd: str, owner_pwd: str) -> bytes:
        return _file(_post('password', {
            'pdf': _b64(pdf), 'user_password': user_pwd, 'owner_password': owner_pwd
        }))

    def convert_to_image(self, pdf: bytes, page_number: int, dpi: int = 150) -> bytes:
        return _file(_post('convert-image', {
            'pdf': _b64(pdf), 'page_number': page_number, 'dpi': dpi
        }))

    # ── Fonctionnalités Avancées ───────────────────────────────────

    def search_text(self, pdf: bytes, keyword: str) -> List[str]:
        return _post('search', {'pdf': _b64(pdf), 'keyword': keyword}).get('results', [])

    def add_watermark(self, pdf: bytes, text: str) -> bytes:
        return _file(_post('watermark', {'pdf': _b64(pdf), 'watermark_text': text}))

    def get_pdf_info(self, pdf: bytes) -> dict:
        d = _post('info', {'pdf': _b64(pdf)})
        return {
            'page_count':    d.get('page_count', 0),
            'word_count':    d.get('word_count', 0),
            'file_size':     d.get('file_size', 0),
            'title':         d.get('title', ''),
            'author':        d.get('author', ''),
            'subject':       d.get('subject', ''),
            'creator':       d.get('creator', ''),
            'creation_date': d.get('creation_date', ''),
        }

    def compress_pdf(self, pdf: bytes) -> bytes:
        return _file(_post('compress', {'pdf': _b64(pdf)}))

    def rotate_page(self, pdf: bytes, page_number: int, degrees: int) -> bytes:
        return _file(_post('rotate', {
            'pdf': _b64(pdf), 'page_number': page_number, 'degrees': degrees
        }))

    def reorder_pages(self, pdf: bytes, new_order: List[int]) -> bytes:
        return _file(_post('reorder', {'pdf': _b64(pdf), 'order': new_order}))
