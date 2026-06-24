# Piyasa Zekası Dokümantasyonu

Bu klasör, mevcut bilimsel günlüklerden ve makale taslağından bağımsız yeni çalışma alanıdır.
Amaç, projeyi sadece sinyal üreten bir sistem olmaktan çıkarıp teknik yapı, haber akışı,
endeks bağımlılığı ve uzman yorumu üretebilen açıklanabilir bir piyasa okuma motoruna taşımaktır.

Buradaki belgeler henüz kod taahhüdü değildir; önce düşünce mimarisi, araştırma protokolü ve
kullanılabilir yorum şeması kurulacaktır. Kodlama aşaması daha sonra, bu çerçeve yeterince keskin
hale geldiğinde başlayacaktır.

## Okuma Sırası

| Belge | Rol |
|---|---|
| [00-framing.md](00-framing.md) | Ana vizyon, kapsam, ilkeler ve sistemin neye dönüşeceği. |
| [01-doc-mimarisi.md](01-doc-mimarisi.md) | Bu yeni alanın dokümantasyon haritası ve üretilecek belge seti. |
| [02-arastirma-protokolu.md](02-arastirma-protokolu.md) | Teknik analiz bilgisini projeye akademik ama uygulanabilir şekilde alma yöntemi. |
| [03-yorum-motoru-tasarimi.md](03-yorum-motoru-tasarimi.md) | Sinyali uzman yorumuna çeviren açıklama katmanının taslak mimarisi. |

## Temel Ayrım

Mevcut proje şunu soruyor:

> Bu sinyal örnek dışı olarak fiyatla ilişki taşıyor mu?

Bu yeni alan şunu soracak:

> Bu sinyal piyasa bağlamında ne anlama geliyor, hangi koşulda ciddiye alınmalı, hangi koşulda
> yanıltıcıdır ve bunu bir uzman nasıl açıklardı?

Bu yüzden buradaki çalışma, istatistiksel validasyonun yerine geçmez. Validasyon katmanı sinyalin
gerçekliğini sınar; piyasa zekası katmanı sinyalin bağlamını, gerekçesini ve insan tarafından
okunabilir yorumunu üretir.

