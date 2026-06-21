# BULUT 7/24 NÖBET — Kurulum Rehberi (Telegram + GitHub Actions)

**Ne yapar:** GitHub'in sunucularında her 30 dakikada bir çalışır (senin PC'n KAPALI olsa bile), kripto + hisse haber kaynaklarını tarar, katalizör başlığı çıkınca **telefonuna Telegram'dan alarm** atar. Ücretsiz, sunucu yok.

**Sen 3 şey yapacaksın (bot + chat_id + secrets), gerisi kodda hazır.**

---

## ADIM 1 — Telegram bot oluştur (2 dk)
1. Telegram'da **@BotFather**'ı aç (mavi tikli olan).
2. `/newbot` yaz → Enter.
3. Bota bir **isim** ver (örn: `Nabiz Nobet`).
4. Bir **kullanıcı adı** ver, `bot` ile bitmeli (örn: `nabiz_nobet_bot`).
5. BotFather sana bir **TOKEN** verir, şuna benzer:
   `8123456789:AAH...uzun-bir-dizi...`
   → **Bu TOKEN'ı kopyala, sakla.** (TG_TOKEN)

## ADIM 2 — chat_id'ini öğren (1 dk)
1. Az önce oluşturduğun bota Telegram'da **bir mesaj yaz** (herhangi: "merhaba").
2. Tarayıcıda şu adresi aç (TOKEN'ı yapıştır):
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
   (örn: `https://api.telegram.org/bot8123456789:AAH.../getUpdates`)
3. Çıkan metinde `"chat":{"id":123456789` gibi bir **sayı** ara → **o senin chat_id'in.** (TG_CHAT)
   - Görünmüyorsa: bota tekrar mesaj yaz, sayfayı yenile.

## ADIM 3 — GitHub Secrets ekle (2 dk)
1. GitHub'da bu repo'yu aç → **Settings** → sol menü **Secrets and variables** → **Actions**.
2. **New repository secret**:
   - Name: `TG_TOKEN` → Value: (Adım 1 token) → Add.
   - Tekrar New: Name: `TG_CHAT` → Value: (Adım 2 chat_id) → Add.

## ADIM 4 — Dosyaları GitHub'a gönder (push)
Bu dosyalar zaten hazır: `cloud/nabiz_cloud_watch.py` + `.github/workflows/nabiz-watch.yml`.
- Ben push edeyim: bana **"push"** de.
- Ya da kendin: `git add cloud .github && git commit -m "feat: bulut 7/24 nobet" && git push`
- **Not:** Zamanlanmış (cron) workflow SADECE **main** dalında çalışır → main'e push et.

## ADIM 5 — Actions'ı çalıştır + test et
1. GitHub'da repo → **Actions** sekmesi → (ilk sefer "I understand... enable" de).
2. Sol listede **"Nabiz 7-24 Nobet"** → sağda **Run workflow** → Run (elle test).
3. ~1 dk sonra çalışır; **son 35 dakikada katalizör haberi varsa Telegram'a düşer.**
4. Bundan sonra **otomatik her 30 dk** çalışır (UTC). Bir şey bulamazsa sessiz kalır (spam yok).

---

## Ayar / bakım
- **Sıklık:** `.github/workflows/nabiz-watch.yml` içindeki `cron: "*/30 * * * *"` → `*/20` daha sık (ama ücretsiz private 2000 dk/ay sınırına dikkat; public repo = sınırsız).
- **İzlenen kelimeler/coinler:** `cloud/nabiz_cloud_watch.py` → `KW`, `CRYPTO_FEEDS`, `STOCK_FEEDS`, `STOCK_NAMES` listeleri.
- **chat_id testi:** `TG_TOKEN=... python cloud/nabiz_cloud_watch.py --chatid`
- **Sınır:** GitHub cron bazen yoğunlukta ~5-15 dk gecikir; saniye-anlık değil, "haber-yakala" amaçlı. Anlık fiyat tetikleri Claude Code açıkken çalışan nöbetlerde.
