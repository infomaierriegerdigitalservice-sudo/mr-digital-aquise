# MR Digital Akquise – EasyPanel Deployment

Da ihr **EasyPanel** auf eurem Hetzner-Server verwendet, ist das Deployment sogar noch einfacher. Ihr müsst mir keine SSH-Zugangsdaten geben, sondern wir können die App direkt über das EasyPanel-Dashboard installieren.

Hier sind die genauen Schritte, wie wir das aufsetzen:

## Schritt 1: Dockerfile in diesem Projekt
Ich habe in unserem Projektordner `Automatisierung/mr-digital-akquise-v2` eine kleine `Dockerfile` angelegt. Das ist das "Rezept", aus dem EasyPanel die App später baut. 

## Schritt 2: Code auf GitHub/GitLab laden (Empfohlen)
EasyPanel zieht sich den Code am besten direkt von einem Git-Repository (z.B. GitHub). 
1. Hast du dieses Projekt (`mr-digital-akquise-v2`) schon auf einem (privaten) GitHub-Repository liegen?
2. Wenn ja: Perfekt!
3. Wenn nein: Ich kann dir helfen, das in 2 Minuten auf GitHub hochzuladen. Alternativ kann man in EasyPanel auch einen Ordner vom Server manuell anbinden, aber via GitHub ist es Updates wegen viel eleganter.

## Schritt 3: In EasyPanel einrichten
Sobald wir den Code z.B. auf GitHub haben, gehst du in dein EasyPanel auf dem Server (meistens unter `eure-server-ip:3000` erreichbar) und machst Folgendes:

1. Klicke auf **Create Service**
2. Wähle **App** (ganz oben, nicht Database oder One-Click)
3. Typ: **GitHub** (oder GitLab, je nachdem wo der Code liegt)
4. Wähle das Repository aus.
5. In den App-Einstellungen (Settings) unter dem Reiter **Build**:
   - Wähle **Dockerfile** als Build-Typ
6. Im Reiter **Environment** füge diese Umgebungsvariablen hinzu:
   ```env
   # GMAIL_ADDRESS=info... (wird ggf. im Dashboard gesetzt)
   # GMAIL_APP_PASSWORD=... (wird ggf. im Dashboard gesetzt)
   SECRET_KEY=mr-digital-akquise-live-key
   PORT=5000
   ```
7. Im Reiter **Domains**:
   - Trage deine gewünschte Domain ein (z.B. `akquise.mr-digital.de`)
   - Stelle den Port auf `5000` um (das ist der Port in unserem Container)
   - Markiere "Issue SSL Certificate", damit die Seite sicher per HTTPS erreichbar ist.

8. Klicke auf **Deploy**.

EasyPanel zieht jetzt den Code, baut den Server zusammen und macht die App auf der Domain verfügbar. Die Datenbank (`akquise.db`) und die Log-Dateien laufen dann direkt im Container-Speicher (wir können später noch einstellen, dass EasyPanel diese persistiert, indem wir unter **Storage** einen Mount-Path `/app/data` anlegen). 

### Nächster Schritt:
Lass uns zuerst die Dockerfile erstellen. Hast du das Projekt schon auf GitHub oder soll ich dir den Git-Push-Befehl zusammenstellen?
