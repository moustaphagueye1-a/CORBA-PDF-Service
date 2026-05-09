package com.pdfservice;

import org.omg.CORBA.ORB;
import org.omg.PortableServer.POA;
import org.omg.PortableServer.POAHelper;

import java.io.*;
import java.net.InetAddress;
import java.util.Properties;

public class PDFServer {

    public static void main(String[] args) {
        System.out.println("╔══════════════════════════════════════════╗");
        System.out.println("║  CORBA PDF Server + HTTP Bridge          ║");
        System.out.println("║  CORBA → port 1050  |  HTTP → port 8080  ║");
        System.out.println("╚══════════════════════════════════════════╝");

        try {
            // ── 1. Démarrer le Servant CORBA ──────────────────────
            String serverHost = System.getenv("CORBA_SERVER_HOST");
            if (serverHost == null || serverHost.isEmpty())
                serverHost = InetAddress.getLocalHost().getHostAddress();

            Properties orbProps = new Properties();
            orbProps.setProperty("com.sun.CORBA.ORBServerHost", serverHost);
            orbProps.setProperty("com.sun.CORBA.ORBServerPort", "1050");

            ORB orb = ORB.init(new String[]{}, orbProps);
            POA rootPOA = POAHelper.narrow(orb.resolve_initial_references("RootPOA"));
            rootPOA.the_POAManager().activate();

            PDFServant servant = new PDFServant();
            org.omg.CORBA.Object ref = rootPOA.servant_to_reference(servant);
            PDFService.PDFManager pdfManager = PDFService.PDFManagerHelper.narrow(ref);

            // Écrire l'IOR pour référence (compatibilité)
            String ior = orb.object_to_string(pdfManager);
            new File("/shared").mkdirs();
            try (FileWriter w = new FileWriter("/shared/pdfservice.ior")) {
                w.write(ior);
            }
            System.out.println("[CORBA] Serveur CORBA actif sur port 1050");
            System.out.println("[CORBA] IOR écrit dans /shared/pdfservice.ior");

            // ── 2. Démarrer le Pont HTTP ──────────────────────────
            HttpBridge bridge = new HttpBridge(servant);
            bridge.start();
            System.out.println("[HTTP]  Pont HTTP actif sur port 8080");
            System.out.println("[OK]    Système prêt — Django peut se connecter sur http://corba-server:8080");

            // ── 3. Boucle CORBA ───────────────────────────────────
            orb.run();

        } catch (Exception e) {
            System.err.println("[ERREUR] " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
}
