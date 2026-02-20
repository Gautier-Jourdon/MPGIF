# 🌍 Guide d'installation Ngrok pour MPGIF Bot

Pour que Discord puisse accéder à tes fichiers locaux et que tes amis puissent voir les vidéos, tu dois "exposer" ton serveur local `localhost:5000` sur internet. Nous utilisons **ngrok** pour cela.

## Pré-requis OBLIGATOIRE : Créer un compte Ngrok

Depuis peu, ngrok oblige à avoir un compte, même pour la version gratuite.

1.  **Créer un compte** sur [dashboard.ngrok.com/signup](https://dashboard.ngrok.com/signup).
2.  **Récupérer ton Authtoken** dans le tableau de bord (Watching "Your Authtoken").
3.  **Configurer ton PC** :
    Ouvre un terminal et lance la commande suivante (en remplaçant le code par le tien) :
    ```bash
    ngrok config add-authtoken 2M7...TonToken...
    ```
    *Si la commande `ngrok` n'est pas trouvée, installe d'abord ngrok (Méthode 2) ou la librairie pyngrok gère parfois l'installation.*
    
    *Alternative via Python/Pyngrok :*
    ```bash
    python -c "import pyngrok.ngrok; pyngrok.ngrok.set_auth_token('TON_TOKEN')"
    ```

## Méthode 1 : Automatique (Recommandée)

Cette méthode utilise une librairie Python pour lancer ngrok automatiquement.

1.  **Installer la librairie :**
    Ouvre un terminal et tape :
    ```bash
    pip install pyngrok
    ```

2.  **Lancer le serveur :**
    ```bash
    python Discord/Integration/server.py
    ```
    *   Regarde la console, tu verras une ligne comme :
    *   `* ngrok tunnel "https://abcd-123-456.ngrok-free.app" -> "http://127.0.0.1:5000"`

3.  **Copier l'URL** (ex: `https://abcd-123-456.ngrok-free.app`)

4.  **Mettre à jour le Bot :**
    *   Ouvre `Discord/Integration/bot.py`
    *   Remplace la variable `SERVER_URL` par cette nouvelle URL.
    *   *(Ou définis la variable d'environnement `SERVER_URL`)*

---

## Méthode 2 : Manuelle (Si tu as déjà ngrok.exe)

1.  **Télécharger & Installer Ngrok :**
    *   Va sur [ngrok.com](https://ngrok.com/download)
    *   Télécharge et installe-le.
    *   Crée un compte gratuit pour obtenir ton "AuthToken".

2.  **Lancer Ngrok :**
    Ouvre un terminal et tape :
    ```bash
    ngrok http 5000
    ```

3.  **Récupérer l'URL :**
    L'interface ngrok t'affichera une ligne `Forwarding`. Copie l'URL en `https://...`.

4.  **Mettre à jour le Bot** (comme Méthode 1).

---

## 🚦 Lancer le tout

1.  Terminal 1 : `python Discord/Integration/server.py`
2.  Terminal 2 : `python Discord/Integration/bot.py` (Après avoir mis à jour l'URL)
3.  Discord : Tape `/mpgif random`

⚠️ **Note :** La version gratuite de ngrok change d'URL à chaque redémarrage. Il faudra penser à mettre à jour `bot.py` à chaque fois, ou utiliser les variables d'environnement.
