package com.pdfservice;

import PDFService.PDFException;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;

import java.io.*;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.Base64;

public class HttpBridge {

    private final PDFServant servant;
    private HttpServer httpServer;

    public HttpBridge(PDFServant servant) {
        this.servant = servant;
    }

    public void start() throws IOException {
        httpServer = HttpServer.create(new InetSocketAddress(8080), 0);
        httpServer.createContext("/merge",         new MergeHandler());
        httpServer.createContext("/split",         new SplitHandler());
        httpServer.createContext("/extract-pages", new ExtractPagesHandler());
        httpServer.createContext("/delete-pages",  new DeletePagesHandler());
        httpServer.createContext("/extract-text",  new ExtractTextHandler());
        httpServer.createContext("/create-pdf",    new CreatePdfHandler());
        httpServer.createContext("/password",      new PasswordHandler());
        httpServer.createContext("/convert-image", new ConvertImageHandler());
        httpServer.createContext("/search",        new SearchHandler());
        httpServer.createContext("/watermark",     new WatermarkHandler());
        httpServer.createContext("/info",          new InfoHandler());
        httpServer.createContext("/compress",      new CompressHandler());
        httpServer.createContext("/rotate",        new RotateHandler());
        httpServer.createContext("/reorder",       new ReorderHandler());
        httpServer.createContext("/status",        new StatusHandler());
        httpServer.setExecutor(java.util.concurrent.Executors.newFixedThreadPool(4));
        httpServer.start();
        System.out.println("[HTTP] Pont HTTP démarré sur le port 8080");
    }

    // ── Utilitaires ───────────────────────────────────────────────

    /** Lit le corps HTTP — compatible Java 8 (pas de readAllBytes) */
    private static String readBody(HttpExchange ex) throws IOException {
        InputStream is = ex.getRequestBody();
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        byte[] buf = new byte[4096];
        int n;
        while ((n = is.read(buf)) != -1) baos.write(buf, 0, n);
        return baos.toString("UTF-8");
    }

    private static String jsonString(String json, String key) {
        String pattern = "\"" + key + "\"";
        int idx = json.indexOf(pattern);
        if (idx < 0) return "";
        int colon = json.indexOf(':', idx);
        int start = json.indexOf('"', colon + 1) + 1;
        int end   = json.indexOf('"', start);
        if (start <= 0 || end <= 0) return "";
        return json.substring(start, end);
    }

    private static int jsonInt(String json, String key) {
        String pattern = "\"" + key + "\"";
        int idx = json.indexOf(pattern);
        if (idx < 0) return 1;
        int colon = json.indexOf(':', idx) + 1;
        while (colon < json.length() && json.charAt(colon) == ' ') colon++;
        int end = colon;
        while (end < json.length() && (Character.isDigit(json.charAt(end)) || json.charAt(end) == '-')) end++;
        try { return Integer.parseInt(json.substring(colon, end).trim()); }
        catch (NumberFormatException e) { return 1; }
    }

    private static int[] jsonIntArray(String json, String key) {
        String pattern = "\"" + key + "\"";
        int idx = json.indexOf(pattern);
        if (idx < 0) return new int[]{};
        int start = json.indexOf('[', idx) + 1;
        int end   = json.indexOf(']', start);
        if (start <= 0 || end <= 0) return new int[]{};
        String[] parts = json.substring(start, end).split(",");
        List<Integer> list = new ArrayList<Integer>();
        for (String p : parts) {
            try { list.add(Integer.parseInt(p.trim())); } catch (NumberFormatException ignored) {}
        }
        int[] arr = new int[list.size()];
        for (int i = 0; i < list.size(); i++) arr[i] = list.get(i);
        return arr;
    }

    private static byte[] b64decode(String b64) { return Base64.getDecoder().decode(b64.trim()); }
    private static String b64encode(byte[] data) { return Base64.getEncoder().encodeToString(data); }

    private static void sendFile(HttpExchange ex, byte[] data) throws IOException {
        sendJson(ex, 200, "{\"ok\":true,\"data\":\"" + b64encode(data) + "\"}");
    }

    private static void sendText(HttpExchange ex, String text) throws IOException {
        String escaped = text.replace("\\","\\\\").replace("\"","\\\"")
                             .replace("\n","\\n").replace("\r","").replace("\t","\\t");
        sendJson(ex, 200, "{\"ok\":true,\"text\":\"" + escaped + "\"}");
    }

    private static void sendError(HttpExchange ex, String msg) throws IOException {
        String escaped = msg == null ? "erreur" : msg.replace("\"","'").replace("\n"," ");
        sendJson(ex, 500, "{\"ok\":false,\"error\":\"" + escaped + "\"}");
    }

    private static void sendJson(HttpExchange ex, int status, String json) throws IOException {
        byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
        ex.getResponseHeaders().set("Content-Type", "application/json; charset=UTF-8");
        ex.getResponseHeaders().set("Access-Control-Allow-Origin", "*");
        ex.sendResponseHeaders(status, bytes.length);
        OutputStream os = ex.getResponseBody();
        os.write(bytes);
        os.close();
    }

    // ── Handlers ──────────────────────────────────────────────────

    class MergeHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                String body = readBody(ex);
                byte[] r = servant.mergePDFs(b64decode(jsonString(body,"pdf1")), b64decode(jsonString(body,"pdf2")));
                sendFile(ex, r);
            } catch (PDFException e) { sendError(ex, e.message); }
            catch (Exception e)      { sendError(ex, e.getMessage()); }
        }
    }

    class SplitHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                String body = readBody(ex);
                byte[] r = servant.splitPDF(b64decode(jsonString(body,"pdf")), jsonInt(body,"from_page"), jsonInt(body,"to_page"));
                sendFile(ex, r);
            } catch (PDFException e) { sendError(ex, e.message); }
            catch (Exception e)      { sendError(ex, e.getMessage()); }
        }
    }

    class ExtractPagesHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                String body = readBody(ex);
                byte[] r = servant.extractPages(b64decode(jsonString(body,"pdf")), jsonIntArray(body,"pages"));
                sendFile(ex, r);
            } catch (PDFException e) { sendError(ex, e.message); }
            catch (Exception e)      { sendError(ex, e.getMessage()); }
        }
    }

    class DeletePagesHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                String body = readBody(ex);
                byte[] r = servant.deletePages(b64decode(jsonString(body,"pdf")), jsonIntArray(body,"pages"));
                sendFile(ex, r);
            } catch (PDFException e) { sendError(ex, e.message); }
            catch (Exception e)      { sendError(ex, e.getMessage()); }
        }
    }

    class ExtractTextHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                String body = readBody(ex);
                String text = servant.extractText(b64decode(jsonString(body,"pdf")));
                sendText(ex, text);
            } catch (PDFException e) { sendError(ex, e.message); }
            catch (Exception e)      { sendError(ex, e.getMessage()); }
        }
    }

    class CreatePdfHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                String body    = readBody(ex);
                String content = jsonString(body,"content").replace("\\n","\n").replace("\\t","\t");
                byte[] r = servant.createPDF(content, jsonString(body,"title"));
                sendFile(ex, r);
            } catch (PDFException e) { sendError(ex, e.message); }
            catch (Exception e)      { sendError(ex, e.getMessage()); }
        }
    }

    class PasswordHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                String body  = readBody(ex);
                String uPwd  = jsonString(body,"user_password");
                String oPwd  = jsonString(body,"owner_password");
                if (oPwd.isEmpty()) oPwd = uPwd;
                byte[] r = servant.addPassword(b64decode(jsonString(body,"pdf")), uPwd, oPwd);
                sendFile(ex, r);
            } catch (PDFException e) { sendError(ex, e.message); }
            catch (Exception e)      { sendError(ex, e.getMessage()); }
        }
    }

    class ConvertImageHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                String body = readBody(ex);
                int dpi = jsonInt(body,"dpi"); if (dpi <= 0) dpi = 150;
                byte[] r = servant.convertToImage(b64decode(jsonString(body,"pdf")), jsonInt(body,"page_number"), dpi);
                sendFile(ex, r);
            } catch (PDFException e) { sendError(ex, e.message); }
            catch (Exception e)      { sendError(ex, e.getMessage()); }
        }
    }

    class SearchHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                String body = readBody(ex);
                String[] results = servant.searchText(b64decode(jsonString(body,"pdf")), jsonString(body,"keyword"));
                StringBuilder sb = new StringBuilder("{\"ok\":true,\"results\":[");
                for (int i = 0; i < results.length; i++) {
                    String esc = results[i].replace("\\","\\\\").replace("\"","\\\"").replace("\n"," ").replace("\r","");
                    sb.append("\"").append(esc).append("\"");
                    if (i < results.length - 1) sb.append(",");
                }
                sb.append("]}");
                sendJson(ex, 200, sb.toString());
            } catch (PDFException e) { sendError(ex, e.message); }
            catch (Exception e)      { sendError(ex, e.getMessage()); }
        }
    }

    class WatermarkHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                String body = readBody(ex);
                byte[] r = servant.addWatermark(b64decode(jsonString(body,"pdf")), jsonString(body,"watermark_text"));
                sendFile(ex, r);
            } catch (PDFException e) { sendError(ex, e.message); }
            catch (Exception e)      { sendError(ex, e.getMessage()); }
        }
    }

    class InfoHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                String body = readBody(ex);
                PDFService.PDFInfo info = servant.getPDFInfo(b64decode(jsonString(body,"pdf")));
                String json = String.format(
                    "{\"ok\":true,\"page_count\":%d,\"word_count\":%d,\"file_size\":%d," +
                    "\"title\":\"%s\",\"author\":\"%s\",\"subject\":\"%s\",\"creator\":\"%s\",\"creation_date\":\"%s\"}",
                    info.pageCount, info.wordCount, info.fileSize,
                    esc(info.title), esc(info.author), esc(info.subject), esc(info.creator), esc(info.creationDate));
                sendJson(ex, 200, json);
            } catch (PDFException e) { sendError(ex, e.message); }
            catch (Exception e)      { sendError(ex, e.getMessage()); }
        }
        private String esc(String s) { return s==null?"":s.replace("\"","'").replace("\n"," "); }
    }

    class CompressHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                String body = readBody(ex);
                byte[] r = servant.compressPDF(b64decode(jsonString(body,"pdf")));
                sendFile(ex, r);
            } catch (PDFException e) { sendError(ex, e.message); }
            catch (Exception e)      { sendError(ex, e.getMessage()); }
        }
    }

    class RotateHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                String body = readBody(ex);
                byte[] r = servant.rotatePage(b64decode(jsonString(body,"pdf")), jsonInt(body,"page_number"), jsonInt(body,"degrees"));
                sendFile(ex, r);
            } catch (PDFException e) { sendError(ex, e.message); }
            catch (Exception e)      { sendError(ex, e.getMessage()); }
        }
    }

    class ReorderHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            try {
                String body = readBody(ex);
                byte[] r = servant.reorderPages(b64decode(jsonString(body,"pdf")), jsonIntArray(body,"order"));
                sendFile(ex, r);
            } catch (PDFException e) { sendError(ex, e.message); }
            catch (Exception e)      { sendError(ex, e.getMessage()); }
        }
    }

    class StatusHandler implements HttpHandler {
        public void handle(HttpExchange ex) throws IOException {
            sendJson(ex, 200, "{\"ok\":true,\"service\":\"CORBA PDF Bridge\",\"status\":\"running\"}");
        }
    }
}