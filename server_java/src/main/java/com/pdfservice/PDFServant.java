package com.pdfservice;

// ================================================================
//  PDFServant.java — Implémentation des méthodes CORBA PDF
//
//  Cette classe est le "servant" CORBA : elle hérite de PDFManagerPOA
//  (classe générée par idlj depuis l'IDL) et implémente concrètement
//  toutes les opérations de manipulation PDF via Apache PDFBox 2.0.
//
//  Protocole CORBA :
//    Client envoie une requête IIOP → ORB → PDFServant.methode()
//    PDFServant traite avec PDFBox → retourne le résultat via IIOP
// ================================================================

import PDFService.PDFException;
import PDFService.PDFInfo;
import PDFService.PDFManagerPOA;

import org.apache.pdfbox.multipdf.PDFMergerUtility;
import org.apache.pdfbox.pdmodel.*;
import org.apache.pdfbox.pdmodel.common.PDRectangle;
import org.apache.pdfbox.pdmodel.encryption.AccessPermission;
import org.apache.pdfbox.pdmodel.encryption.StandardProtectionPolicy;
import org.apache.pdfbox.pdmodel.font.PDFont;
import org.apache.pdfbox.pdmodel.font.PDType1Font;
import org.apache.pdfbox.rendering.ImageType;
import org.apache.pdfbox.rendering.PDFRenderer;
import org.apache.pdfbox.text.PDFTextStripper;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class PDFServant extends PDFManagerPOA {

    // ----------------------------------------------------------------
    //  Utilitaires internes (helpers)
    // ----------------------------------------------------------------

    /**
     * Charge un PDDocument depuis un tableau d'octets.
     * @param data Contenu binaire du PDF
     * @return PDDocument prêt à l'emploi
     */
    private PDDocument loadDoc(byte[] data) throws IOException {
        return PDDocument.load(data);
    }

    /**
     * Sérialise un PDDocument en tableau d'octets.
     * @param doc Le document à sérialiser
     * @return Contenu binaire du PDF (données IIOP)
     */
    private byte[] saveDoc(PDDocument doc) throws IOException {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        doc.save(baos);
        return baos.toByteArray();
    }

    /**
     * Ferme un document sans lever d'exception (pour les blocs finally).
     */
    private void closeQuietly(PDDocument doc) {
        if (doc != null) {
            try { doc.close(); } catch (IOException ignored) {}
        }
    }

    // ================================================================
    //  BLOC 1 — Opérations de Base
    // ================================================================

    /**
     * Fusionne deux documents PDF en un seul.
     * Utilise PDFMergerUtility de PDFBox pour concaténer les pages.
     */
    @Override
    public byte[] mergePDFs(byte[] pdf1, byte[] pdf2) throws PDFException {
        System.out.println("[CORBA] → mergePDFs() appelé");
        PDDocument doc1 = null, doc2 = null;
        try {
            doc1 = loadDoc(pdf1);
            doc2 = loadDoc(pdf2);

            // Utiliser PDFMergerUtility pour fusionner doc2 dans doc1
            PDFMergerUtility merger = new PDFMergerUtility();
            merger.appendDocument(doc1, doc2);

            byte[] result = saveDoc(doc1);
            System.out.println("[CORBA] ✓ mergePDFs : " + doc1.getNumberOfPages() + " pages au total");
            return result;

        } catch (Exception e) {
            System.err.println("[ERREUR] mergePDFs : " + e.getMessage());
            throw new PDFException("Erreur lors de la fusion : " + e.getMessage());
        } finally {
            closeQuietly(doc1);
            closeQuietly(doc2);
        }
    }

    /**
     * Extrait une plage de pages d'un PDF (fromPage à toPage, 1-indexé).
     * Exemple : splitPDF(pdf, 2, 4) → pages 2, 3 et 4.
     */
    @Override
    public byte[] splitPDF(byte[] pdf, int fromPage, int toPage) throws PDFException {
        System.out.println("[CORBA] → splitPDF() pages " + fromPage + " à " + toPage);
        PDDocument doc = null, result = null;
        try {
            doc = loadDoc(pdf);
            int totalPages = doc.getNumberOfPages();

            // Validation des numéros de pages
            if (fromPage < 1 || toPage > totalPages || fromPage > toPage) {
                throw new PDFException(
                    "Pages invalides : fromPage=" + fromPage + ", toPage=" + toPage +
                    ", total=" + totalPages + ". Les pages doivent être entre 1 et " + totalPages
                );
            }

            result = new PDDocument();
            for (int i = fromPage - 1; i < toPage; i++) {
                result.addPage(doc.getPage(i));
            }

            byte[] output = saveDoc(result);
            System.out.println("[CORBA] ✓ splitPDF : " + result.getNumberOfPages() + " pages extraites");
            return output;

        } catch (PDFException e) {
            throw e;
        } catch (Exception e) {
            System.err.println("[ERREUR] splitPDF : " + e.getMessage());
            throw new PDFException("Erreur lors du découpage : " + e.getMessage());
        } finally {
            closeQuietly(doc);
            closeQuietly(result);
        }
    }

    /**
     * Extrait des pages spécifiques (liste de numéros) vers un nouveau PDF.
     * Exemple : extractPages(pdf, [1, 3, 5]) → pages 1, 3 et 5 seulement.
     */
    @Override
    public byte[] extractPages(byte[] pdf, int[] pageNumbers) throws PDFException {
        System.out.println("[CORBA] → extractPages() : " + pageNumbers.length + " page(s)");
        PDDocument doc = null, result = null;
        try {
            doc = loadDoc(pdf);
            result = new PDDocument();

            for (int pageNum : pageNumbers) {
                if (pageNum < 1 || pageNum > doc.getNumberOfPages()) {
                    throw new PDFException("Numéro de page invalide : " + pageNum +
                        " (total : " + doc.getNumberOfPages() + ")");
                }
                result.addPage(doc.getPage(pageNum - 1)); // 0-indexé dans PDFBox
            }

            byte[] output = saveDoc(result);
            System.out.println("[CORBA] ✓ extractPages : " + pageNumbers.length + " page(s) extraite(s)");
            return output;

        } catch (PDFException e) {
            throw e;
        } catch (Exception e) {
            System.err.println("[ERREUR] extractPages : " + e.getMessage());
            throw new PDFException("Erreur lors de l'extraction : " + e.getMessage());
        } finally {
            closeQuietly(doc);
            closeQuietly(result);
        }
    }

    /**
     * Supprime des pages spécifiques d'un PDF.
     * Les pages sont supprimées en ordre décroissant pour préserver les indices.
     */
    @Override
    public byte[] deletePages(byte[] pdf, int[] pageNumbers) throws PDFException {
        System.out.println("[CORBA] → deletePages() : " + pageNumbers.length + " page(s) à supprimer");
        PDDocument doc = null;
        try {
            doc = loadDoc(pdf);

            // Trier en ordre DÉCROISSANT pour supprimer sans décaler les indices
            List<Integer> pages = new ArrayList<>();
            for (int p : pageNumbers) pages.add(p);
            pages.sort(Collections.reverseOrder());

            for (int pageNum : pages) {
                if (pageNum < 1 || pageNum > doc.getNumberOfPages()) {
                    throw new PDFException("Numéro de page invalide : " + pageNum);
                }
                doc.removePage(pageNum - 1);
            }

            byte[] output = saveDoc(doc);
            System.out.println("[CORBA] ✓ deletePages : " + doc.getNumberOfPages() + " page(s) restante(s)");
            return output;

        } catch (PDFException e) {
            throw e;
        } catch (Exception e) {
            System.err.println("[ERREUR] deletePages : " + e.getMessage());
            throw new PDFException("Erreur lors de la suppression : " + e.getMessage());
        } finally {
            closeQuietly(doc);
        }
    }

    /**
     * Extrait tout le texte brut d'un document PDF.
     * Utilise PDFTextStripper qui parcourt chaque page et extrait le contenu textuel.
     */
    @Override
    public String extractText(byte[] pdf) throws PDFException {
        System.out.println("[CORBA] → extractText()");
        PDDocument doc = null;
        try {
            doc = loadDoc(pdf);
            PDFTextStripper stripper = new PDFTextStripper();
            stripper.setSortByPosition(true); // Ordre de lecture naturel
            String text = stripper.getText(doc);
            System.out.println("[CORBA] ✓ extractText : " + text.length() + " caractères extraits");
            return text;
        } catch (Exception e) {
            System.err.println("[ERREUR] extractText : " + e.getMessage());
            throw new PDFException("Erreur lors de l'extraction du texte : " + e.getMessage());
        } finally {
            closeQuietly(doc);
        }
    }

    /**
     * Crée un nouveau document PDF à partir d'un contenu textuel.
     * Gère automatiquement le retour à la ligne et les pages multiples.
     */
    @Override
    public byte[] createPDF(String content, String title) throws PDFException {
        System.out.println("[CORBA] → createPDF() titre='" + title + "'");
        PDDocument doc = null;
        try {
            doc = new PDDocument();

            // Polices
            PDFont fontNormal = PDType1Font.HELVETICA;
            PDFont fontBold   = PDType1Font.HELVETICA_BOLD;

            float pageWidth   = PDRectangle.A4.getWidth();
            float pageHeight  = PDRectangle.A4.getHeight();
            float margin      = 60f;
            float yPosition   = pageHeight - margin;
            float lineHeight  = 16f;
            float maxWidth    = pageWidth - 2 * margin;

            PDPage currentPage = new PDPage(PDRectangle.A4);
            doc.addPage(currentPage);
            PDPageContentStream stream = new PDPageContentStream(doc, currentPage);

            // ── Titre du document ──
            if (title != null && !title.isEmpty()) {
                stream.beginText();
                stream.setFont(fontBold, 20);
                stream.newLineAtOffset(margin, yPosition);
                stream.showText(sanitizeText(title));
                stream.endText();
                yPosition -= lineHeight * 2;

                // Ligne de séparation
                stream.setStrokingColor(0.2f, 0.4f, 0.8f);
                stream.setLineWidth(1.5f);
                stream.moveTo(margin, yPosition + 8);
                stream.lineTo(pageWidth - margin, yPosition + 8);
                stream.stroke();
                yPosition -= lineHeight;
            }

            // ── Contenu ligne par ligne ──
            stream.beginText();
            stream.setFont(fontNormal, 11);
            stream.setLeading(lineHeight);
            stream.newLineAtOffset(margin, yPosition);

            String[] lines = content.split("\n", -1);
            for (String line : lines) {
                // Découpage des lignes trop longues (word-wrap manuel)
                List<String> wrappedLines = wrapText(line, fontNormal, 11, maxWidth);
                for (String wl : wrappedLines) {
                    yPosition -= lineHeight;

                    // Si on atteint le bas de page → nouvelle page
                    if (yPosition < margin) {
                        stream.endText();
                        stream.close();

                        currentPage = new PDPage(PDRectangle.A4);
                        doc.addPage(currentPage);
                        stream = new PDPageContentStream(doc, currentPage);
                        stream.setFont(fontNormal, 11);
                        stream.setLeading(lineHeight);
                        yPosition = pageHeight - margin;
                        stream.beginText();
                        stream.newLineAtOffset(margin, yPosition);
                    }

                    stream.showText(sanitizeText(wl));
                    stream.newLine();
                }
            }

            stream.endText();
            stream.close();

            // Métadonnées du document
            PDDocumentInformation info = doc.getDocumentInformation();
            info.setTitle(title);
            info.setCreator("CORBA PDF Service — Projet AGROTIC");
            info.setProducer("Apache PDFBox 2.0 + Java CORBA ORB");

            byte[] output = saveDoc(doc);
            System.out.println("[CORBA] ✓ createPDF : " + doc.getNumberOfPages() + " page(s) créée(s)");
            return output;

        } catch (Exception e) {
            System.err.println("[ERREUR] createPDF : " + e.getMessage());
            throw new PDFException("Erreur lors de la création du PDF : " + e.getMessage());
        } finally {
            closeQuietly(doc);
        }
    }

    /**
     * Ajoute une protection par mot de passe au PDF (chiffrement AES-256).
     * userPassword : mot de passe pour l'ouverture
     * ownerPassword : mot de passe administrateur (permissions complètes)
     */
    @Override
    public byte[] addPassword(byte[] pdf, String userPassword, String ownerPassword) throws PDFException {
        System.out.println("[CORBA] → addPassword()");
        PDDocument doc = null;
        try {
            doc = loadDoc(pdf);

            // Permissions d'accès (lecture seule par défaut pour l'utilisateur)
            AccessPermission ap = new AccessPermission();
            ap.setCanPrint(true);
            ap.setCanExtractContent(false);
            ap.setCanModify(false);

            // Politique de protection AES-256 bits
            StandardProtectionPolicy policy = new StandardProtectionPolicy(
                ownerPassword, userPassword, ap
            );
            policy.setEncryptionKeyLength(256); // AES-256

            doc.protect(policy);

            byte[] output = saveDoc(doc);
            System.out.println("[CORBA] ✓ addPassword : PDF protégé (AES-256)");
            return output;

        } catch (Exception e) {
            System.err.println("[ERREUR] addPassword : " + e.getMessage());
            throw new PDFException("Erreur lors de l'ajout du mot de passe : " + e.getMessage());
        } finally {
            closeQuietly(doc);
        }
    }

    /**
     * Convertit une page d'un PDF en image PNG.
     * Utilise PDFRenderer pour rastériser la page à la résolution demandée (DPI).
     */
    @Override
    public byte[] convertToImage(byte[] pdf, int pageNumber, int dpi) throws PDFException {
        System.out.println("[CORBA] → convertToImage() page=" + pageNumber + " dpi=" + dpi);
        PDDocument doc = null;
        try {
            doc = loadDoc(pdf);

            if (pageNumber < 1 || pageNumber > doc.getNumberOfPages()) {
                throw new PDFException("Numéro de page invalide : " + pageNumber +
                    " (total : " + doc.getNumberOfPages() + ")");
            }

            // Rastériser avec PDFRenderer
            PDFRenderer renderer = new PDFRenderer(doc);
            BufferedImage image = renderer.renderImageWithDPI(
                pageNumber - 1,  // 0-indexé
                dpi,
                ImageType.RGB
            );

            // Encoder en PNG
            ByteArrayOutputStream baos = new ByteArrayOutputStream();
            ImageIO.write(image, "PNG", baos);

            System.out.println("[CORBA] ✓ convertToImage : " +
                image.getWidth() + "x" + image.getHeight() + " pixels");
            return baos.toByteArray();

        } catch (PDFException e) {
            throw e;
        } catch (Exception e) {
            System.err.println("[ERREUR] convertToImage : " + e.getMessage());
            throw new PDFException("Erreur lors de la conversion en image : " + e.getMessage());
        } finally {
            closeQuietly(doc);
        }
    }

    // ================================================================
    //  BLOC 2 — Fonctionnalités Avancées
    // ================================================================

    /**
     * Recherche un mot-clé dans toutes les pages du PDF.
     * Retourne une liste de résultats avec le numéro de page et le contexte.
     * La recherche est insensible à la casse.
     */
    @Override
    public String[] searchText(byte[] pdf, String keyword) throws PDFException {
        System.out.println("[CORBA] → searchText() mot-clé='" + keyword + "'");
        PDDocument doc = null;
        try {
            doc = loadDoc(pdf);
            List<String> results = new ArrayList<>();
            PDFTextStripper stripper = new PDFTextStripper();
            int numPages = doc.getNumberOfPages();

            for (int i = 1; i <= numPages; i++) {
                stripper.setStartPage(i);
                stripper.setEndPage(i);
                String pageText = stripper.getText(doc);

                // Recherche insensible à la casse
                String lowerPage    = pageText.toLowerCase();
                String lowerKeyword = keyword.toLowerCase();
                int searchIdx = 0;

                while (true) {
                    int idx = lowerPage.indexOf(lowerKeyword, searchIdx);
                    if (idx < 0) break;

                    // Extraire le contexte autour du mot trouvé (±60 caractères)
                    int ctxStart = Math.max(0, idx - 60);
                    int ctxEnd   = Math.min(pageText.length(), idx + keyword.length() + 60);
                    String context = pageText.substring(ctxStart, ctxEnd)
                        .replace("\n", " ")
                        .trim();

                    results.add("Page " + i + " : …" + context + "…");
                    searchIdx = idx + keyword.length();
                }
            }

            System.out.println("[CORBA] ✓ searchText : " + results.size() + " occurrence(s) trouvée(s)");
            return results.toArray(new String[0]);

        } catch (Exception e) {
            System.err.println("[ERREUR] searchText : " + e.getMessage());
            throw new PDFException("Erreur lors de la recherche : " + e.getMessage());
        } finally {
            closeQuietly(doc);
        }
    }

    /**
     * Ajoute un filigrane (watermark) diagonal sur chaque page du PDF.
     * Le filigrane est en gris semi-transparent, incliné à 45°.
     */
    @Override
    public byte[] addWatermark(byte[] pdf, String watermarkText) throws PDFException {
        System.out.println("[CORBA] → addWatermark() texte='" + watermarkText + "'");
        PDDocument doc = null;
        try {
            doc = loadDoc(pdf);
            PDFont font = PDType1Font.HELVETICA_BOLD;

            for (PDPage page : doc.getPages()) {
                PDRectangle pageSize = page.getMediaBox();
                float pageWidth  = pageSize.getWidth();
                float pageHeight = pageSize.getHeight();

                // Ajouter le filigrane par-dessus le contenu existant
                PDPageContentStream cs = new PDPageContentStream(
                    doc, page,
                    PDPageContentStream.AppendMode.APPEND, // Ne pas écraser le contenu
                    true,   // Compression
                    true    // Réinitialiser l'état graphique
                );

                cs.saveGraphicsState();

                // Couleur gris clair semi-transparent
                cs.setNonStrokingColor(0.75f, 0.75f, 0.75f);
                cs.setFont(font, 48);

                // Matrice de rotation 45° centrée sur la page
                float angle  = (float) Math.toRadians(45);
                float cosA   = (float) Math.cos(angle);
                float sinA   = (float) Math.sin(angle);
                float centerX = pageWidth  / 2 - 100;
                float centerY = pageHeight / 2 - 20;

                cs.beginText();
                cs.setTextMatrix(cosA, sinA, -sinA, cosA, centerX, centerY);
                cs.showText(sanitizeText(watermarkText));
                cs.endText();

                cs.restoreGraphicsState();
                cs.close();
            }

            byte[] output = saveDoc(doc);
            System.out.println("[CORBA] ✓ addWatermark : filigrane ajouté sur " +
                doc.getNumberOfPages() + " page(s)");
            return output;

        } catch (Exception e) {
            System.err.println("[ERREUR] addWatermark : " + e.getMessage());
            throw new PDFException("Erreur lors de l'ajout du filigrane : " + e.getMessage());
        } finally {
            closeQuietly(doc);
        }
    }

    /**
     * Retourne les métadonnées et statistiques complètes d'un PDF.
     * Analyse le texte pour estimer le nombre de mots.
     */
    @Override
    public PDFInfo getPDFInfo(byte[] pdf) throws PDFException {
        System.out.println("[CORBA] → getPDFInfo()");
        PDDocument doc = null;
        try {
            doc = loadDoc(pdf);
            PDDocumentInformation meta = doc.getDocumentInformation();

            // Extraction du texte pour compter les mots
            PDFTextStripper stripper = new PDFTextStripper();
            String text = stripper.getText(doc);
            int wordCount = text.trim().isEmpty() ? 0 : text.trim().split("\\s+").length;

            // Remplir la structure PDFInfo (générée par idlj depuis l'IDL)
            PDFInfo info = new PDFInfo();
            info.pageCount   = doc.getNumberOfPages();
            info.wordCount   = wordCount;
            info.fileSize    = pdf.length;
            info.title       = nvl(meta.getTitle());
            info.author      = nvl(meta.getAuthor());
            info.subject     = nvl(meta.getSubject());
            info.creator     = nvl(meta.getCreator());
            info.creationDate = meta.getCreationDate() != null
                ? meta.getCreationDate().getTime().toString()
                : "Non spécifiée";

            System.out.println("[CORBA] ✓ getPDFInfo : " + info.pageCount +
                " pages, " + info.wordCount + " mots, " + info.fileSize + " octets");
            return info;

        } catch (Exception e) {
            System.err.println("[ERREUR] getPDFInfo : " + e.getMessage());
            throw new PDFException("Erreur lors de la récupération des infos : " + e.getMessage());
        } finally {
            closeQuietly(doc);
        }
    }

    /**
     * Compresse un document PDF en réoptimisant sa structure interne.
     * PDFBox re-encode le document avec la compression par défaut.
     */
    @Override
    public byte[] compressPDF(byte[] pdf) throws PDFException {
        System.out.println("[CORBA] → compressPDF()");
        PDDocument doc = null;
        try {
            doc = loadDoc(pdf);
            long originalSize = pdf.length;

            // PDFBox applique la compression Deflate lors de la sauvegarde
            byte[] output = saveDoc(doc);

            long compressedSize = output.length;
            long savings = originalSize - compressedSize;
            double pct = originalSize > 0 ? (savings * 100.0 / originalSize) : 0;

            System.out.println("[CORBA] ✓ compressPDF : " + originalSize + " → " +
                compressedSize + " octets (" + String.format("%.1f", pct) + "% de réduction)");
            return output;

        } catch (Exception e) {
            System.err.println("[ERREUR] compressPDF : " + e.getMessage());
            throw new PDFException("Erreur lors de la compression : " + e.getMessage());
        } finally {
            closeQuietly(doc);
        }
    }

    /**
     * Applique une rotation à une page spécifique.
     * degrees doit être 90, 180 ou 270 (multiples de 90).
     */
    @Override
    public byte[] rotatePage(byte[] pdf, int pageNumber, int degrees) throws PDFException {
        System.out.println("[CORBA] → rotatePage() page=" + pageNumber + " degrés=" + degrees);
        PDDocument doc = null;
        try {
            doc = loadDoc(pdf);

            if (pageNumber < 1 || pageNumber > doc.getNumberOfPages()) {
                throw new PDFException("Numéro de page invalide : " + pageNumber);
            }
            if (degrees % 90 != 0) {
                throw new PDFException("La rotation doit être un multiple de 90° (90, 180, 270)");
            }

            PDPage page = doc.getPage(pageNumber - 1);
            int currentRotation = page.getRotation();
            int newRotation = (currentRotation + degrees) % 360;
            page.setRotation(newRotation);

            byte[] output = saveDoc(doc);
            System.out.println("[CORBA] ✓ rotatePage : page " + pageNumber +
                " pivotée de " + degrees + "° → rotation totale " + newRotation + "°");
            return output;

        } catch (PDFException e) {
            throw e;
        } catch (Exception e) {
            System.err.println("[ERREUR] rotatePage : " + e.getMessage());
            throw new PDFException("Erreur lors de la rotation : " + e.getMessage());
        } finally {
            closeQuietly(doc);
        }
    }

    /**
     * Réorganise les pages d'un PDF selon un ordre personnalisé.
     * Exemple : reorderPages(pdf, [3,1,2]) → page 3 en premier, puis 1, puis 2.
     */
    @Override
    public byte[] reorderPages(byte[] pdf, int[] newOrder) throws PDFException {
        System.out.println("[CORBA] → reorderPages() nouvel ordre : " + newOrder.length + " pages");
        PDDocument doc = null, result = null;
        try {
            doc = loadDoc(pdf);
            result = new PDDocument();

            for (int pageNum : newOrder) {
                if (pageNum < 1 || pageNum > doc.getNumberOfPages()) {
                    throw new PDFException("Numéro de page invalide dans l'ordre : " + pageNum +
                        " (total : " + doc.getNumberOfPages() + ")");
                }
                result.addPage(doc.getPage(pageNum - 1));
            }

            byte[] output = saveDoc(result);
            System.out.println("[CORBA] ✓ reorderPages : " + result.getNumberOfPages() + " pages réorganisées");
            return output;

        } catch (PDFException e) {
            throw e;
        } catch (Exception e) {
            System.err.println("[ERREUR] reorderPages : " + e.getMessage());
            throw new PDFException("Erreur lors de la réorganisation : " + e.getMessage());
        } finally {
            closeQuietly(doc);
            closeQuietly(result);
        }
    }

    // ================================================================
    //  Utilitaires privés
    // ================================================================

    /** Remplace null par une chaîne vide (pour les métadonnées PDF). */
    private String nvl(String s) {
        return s != null ? s : "";
    }

    /**
     * Nettoie une chaîne pour l'affichage PDF (supprime les caractères
     * non supportés par PDType1Font/WinAnsiEncoding).
     */
    private String sanitizeText(String text) {
        if (text == null) return "";
        // PDType1Font ne supporte que les caractères Latin-1
        return text.replaceAll("[^\\x20-\\x7E\\xA0-\\xFF]", "?");
    }

    /**
     * Découpe une ligne de texte pour qu'elle rentre dans la largeur max.
     * (Word-wrap manuel car PDFBox ne gère pas cela automatiquement.)
     */
    private List<String> wrapText(String text, PDFont font, float fontSize, float maxWidth)
        throws IOException {
        List<String> lines = new ArrayList<>();
        if (text == null || text.isEmpty()) {
            lines.add("");
            return lines;
        }

        String[] words = text.split(" ");
        StringBuilder currentLine = new StringBuilder();

        for (String word : words) {
            String testLine = currentLine.length() > 0
                ? currentLine + " " + word
                : word;
            String sanitized = sanitizeText(testLine);

            float lineWidth = font.getStringWidth(sanitized) / 1000 * fontSize;
            if (lineWidth > maxWidth && currentLine.length() > 0) {
                lines.add(currentLine.toString());
                currentLine = new StringBuilder(word);
            } else {
                currentLine = new StringBuilder(testLine);
            }
        }
        if (currentLine.length() > 0) {
            lines.add(currentLine.toString());
        }
        return lines;
    }
}
