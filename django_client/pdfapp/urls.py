"""
urls.py — Routage de l'application pdfapp
"""
from django.urls import path
from . import views

urlpatterns = [
    # Page d'accueil
    path('',                    views.index,              name='index'),

    # ── Opérations de Base ──────────────────────────────────────────
    path('merge/',              views.merge_view,         name='merge'),
    path('split/',              views.split_view,         name='split'),
    path('extract-pages/',      views.extract_pages_view, name='extract_pages'),
    path('delete-pages/',       views.delete_pages_view,  name='delete_pages'),
    path('extract-text/',       views.extract_text_view,  name='extract_text'),
    path('create-pdf/',         views.create_pdf_view,    name='create_pdf'),
    path('password/',           views.password_view,      name='password'),
    path('convert-image/',      views.convert_image_view, name='convert_image'),

    # ── Fonctionnalités Avancées ───────────────────────────────────
    path('search/',             views.search_text_view,   name='search_text'),
    path('watermark/',          views.watermark_view,     name='watermark'),
    path('info/',               views.pdf_info_view,      name='pdf_info'),
    path('compress/',           views.compress_view,      name='compress'),
    path('rotate/',             views.rotate_view,        name='rotate'),
    path('reorder/',            views.reorder_view,       name='reorder'),

    # ── API JSON ───────────────────────────────────────────────────
    path('api/status/',         views.api_status,         name='api_status'),
]
