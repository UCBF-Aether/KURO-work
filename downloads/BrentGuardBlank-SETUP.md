# BrentGuard Blank — Setup

BrentGuard Blank is the family location-sharing app with **no
backend of its own**. It does nothing on the internet until you
give it a server address. That server is a small program
(a "Worker") that you run on your own free Cloudflare account,
plus a storage bucket on the same account. Your family's
locations live only in that bucket, encrypted, and only your
family's phones can read them.

**What you need:** a Cloudflare account (free), this folder,
and the `BrentGuardBlank.apk` file in it.

> **Honest note:** these steps were written from the Worker
> source code in this folder (`relay-worker/`). They were **not**
> run end-to-end against a live Cloudflare account while this
> build was made, so if a button in the Cloudflare dashboard
> has moved or looks different, the Cloudflare help pages are
> the authority. Nothing here is guessed from thin air — the
> Worker code, the file names, and the app's behaviour are all
> verified from the source — but the clicking itself is
> **unverified**.

---

## Step 1 — Make a storage bucket (R2)

1. Sign in at [dash.cloudflare.com](https://dash.cloudflare.com).
2. On the left, open **R2 Object Storage**.
3. Click **Create bucket**. Name it exactly:
   `brentguard-blank`
4. Leave everything else as it is. Click **Create bucket**.

That bucket is where your family's encrypted locations live.
Nobody can read them without your family key — not even
Cloudflare, because the app encrypts everything before it
leaves the phone.

## Step 2 — Deploy the Worker (your relay)

1. On the left, open **Workers & Pages**.
2. Click **Create**, then **Create Worker**.
3. Give it a name, for example `brentguard-blank`, and click
   **Deploy**. (Cloudflare makes a starter Worker first —
   you will replace its code in the next step.)
4. Click **Configure Worker** (or open the Worker and click
   **Edit Code**).
5. Delete all the starter code. Paste in the contents of
   `relay-worker/src/index.js` from this folder.
6. Click **Add module** (or the file list) and add a second
   file named `lib.js`. Paste in the contents of
   `relay-worker/src/lib.js`.
   - If the editor does not offer adding a file, use the
     `wrangler` method below instead.
7. Click **Deploy**.
8. Go to the Worker's **Settings → Variables**, scroll to
   **R2 Bucket Bindings**, and add a binding:
   - Variable name: `BRENTGUARD_BUCKET`
   - Bucket: `brentguard-blank` (the one from Step 1)
9. Save / redeploy if it asks.

Your Worker now has an address. It looks like this
(your part after the dot will differ):

```
https://brentguard-blank.YOURNAME.workers.dev
```

You can test it in a browser: opening that address should
show a plain download page that says **BrentGuard**.

**Alternative — wrangler (command line, unverified):**
if you have `wrangler` installed and logged in, run this
from the `relay-worker/` folder: `wrangler deploy`. The
`wrangler.toml` file in that folder already names the Worker
`brentguard-blank` and the bucket `brentguard-blank`. The
dashboard method above is the one to use if wrangler gives
you trouble.

## Step 3 — Put the app file in the bucket (so "Check for update" works)

The app checks your Worker for updates. For that to work, the
APK and a small version file must sit in the same bucket.

1. In R2, open the `brentguard-blank` bucket.
2. Upload `BrentGuardBlank.apk` (from this folder).
3. Make a file called `version.json` with exactly this inside:

```json
{"versionCode": 89, "versionName": "1.9.10-blank"}
```

4. Upload `version.json` to the bucket.
5. Make the four update parts. On any computer with Python:

```bash
python3 -c "
import base64
raw = open('BrentGuardBlank.apk','rb').read()
b64 = base64.b64encode(raw).decode()
n = (len(b64) + 3) // 4
for i in range(4):
    open(f'BrentGuard.apk.b64.part{i+1}','w').write(b64[i*n:(i+1)*n])
print('parts written, total base64 chars:', len(b64))
"
```

   That creates `BrentGuard.apk.b64.part1` through
   `BrentGuard.apk.b64.part4`. Upload all four to the bucket.

6. When you ship a newer version later: upload the new APK,
   the four new parts, and a new `version.json` with the new
   numbers. **No Worker redeploy is needed** — the Worker
   reads them from the bucket each time.

## Step 4 — Point the app at your relay

1. Install `BrentGuardBlank.apk` on your Android phone. Your
   phone will ask you to allow installs from your browser or
   file manager — say yes, this once.
2. Open BrentGuard. Tap **Details** (bottom of the main
   screen).
3. At the top you will see **Your relay URL** and the line:
   *"No relay configured — paste your Cloudflare Worker URL
   below and tap Save. Nothing leaves this phone until you do."*
4. Paste your Worker address from Step 2 into the box, for
   example `https://brentguard-blank.YOURNAME.workers.dev`
   (you can leave off the `https://` — the app adds it).
5. Tap **Save**.
6. The app pings your Worker once and tells you the result:
   - **"Relay saved — it answered. Sharing is on."** — done.
     The line under the box now reads
     *"Relay: brentguard-blank.YOURNAME.workers.dev — it
     answered, sharing is on."*
   - **"Relay saved, but it did not answer — check the URL
     and that the Worker is deployed."** — the URL is wrong,
     or the Worker is not deployed yet. Go back to Step 2.

## Step 5 — Make a family circle and invite someone

1. In Details, tap **Create circle**, give it a name
   (for example "Family"), and tap **Create**.
2. Tap **Share invite link** and send it to the other phone
   (text, WhatsApp, whatever you use).
3. On the other phone, tap the link. If BrentGuard is
   installed it opens and joins automatically. If it is not
   installed, the link opens a page with a **Download
   BrentGuard** button — install it, then tap the invite
   link again.
4. Both phones must have the **same relay URL** pasted in
   Step 4, or they will never see each other.

**How to know it works:** on the main screen the line under
your circle name should say *"sharing through your relay"*,
and the other person's dot should appear on the map within
about a minute. Tapping **Check for update** in Details
should say you are up to date (or offer the version from
your bucket).

---

## What this blank build does NOT include

- **No shared backend.** There is no central BrentGuard
  server. Your relay is yours alone; another family's relay
  is a different server entirely.
- **No account, no sign-up, no phone number.** Joining is
  by invite link only. The link carries a code and a secret
  key — whoever holds the link can join, so send it only to
  family.
- **No subscription, no payment.** There is nothing to buy
  and nothing that expires. Circles sync for free, up to
  **10 members** per circle.
- **No support desk.** If your Worker goes down, your
  family stops syncing until you fix it. The app says so
  plainly instead of pretending.
- **No updates from anyone else.** "Check for update" only
  ever looks at *your* bucket. Nobody can push an update to
  your phones.

## The signing key (important for updates)

Android only installs an update over an existing app when
the new APK is signed with the **same key** as the old one.

- `blank.keystore` in this folder is the key this APK was
  signed with. **Keep it, and keep its password.**
  - Alias: `brentguard-blank`
  - Password (store and key): `brentguard-blank`
- The Worker file `relay-worker/src/index.js` contains the
  matching fingerprint (`SHA256 = "8A:2D:39:76:..."`) so
  invite links open straight in the app.
- If you rebuild with a **different** keystore, you must
  also put your new fingerprint in that line of `index.js`,
  and everyone must **uninstall and reinstall** — an update
  signed with a different key will be refused by Android.

## If something goes wrong

| What you see | What it means | Fix |
|---|---|---|
| "No relay configured" | No URL saved yet | Step 4 — paste your Worker URL and tap Save |
| "Relay saved, but it did not answer" | URL wrong, or Worker not deployed | Check the URL spelling; redeploy the Worker (Step 2) |
| "Check for update" says nothing found / 404 | version.json or APK parts missing from R2 | Step 3 — upload them to the `brentguard-blank` bucket |
| Invite link opens a browser page but not the app | App Links not verified for your Worker | The Worker serves `/.well-known/assetlinks.json` — check the SHA-256 fingerprint in `index.js` matches your keystore; otherwise tap **Open in BrentGuard** on the page |
| Circle shows "not syncing" | The relay refused the circle (HTTP 403 = circle full at 10 members; HTTP 401 = wrong family key) | Remove a member to free a spot, or re-join with the correct invite link |

## Files in this folder

- `BrentGuardBlank.apk` — the app (install this).
- `blank.keystore` — the signing key (keep it safe).
- `build_apk.sh` — rebuilds the APK from source (needs JDK 17
  and the Android SDK; run `./build_apk.sh`).
- `app/` — the Android source (Java, package
  `com.familyprotection.blank`, version 1.9.10-blank).
- `relay-worker/` — the Worker source (`src/index.js`,
  `src/lib.js`, `wrangler.toml`).
- `SETUP.md` — this file.
