# ŞarjDenge AI — 2020 Holdout Yeniden Eğitim ve Özellik Üretim Protokolü

**Tarih:** 17 Ekim 2026  
**Durum:** Protokol Kesinleştirildi • Kullanıcı Onayına Sunuldu (Veri İndirilmedi)  
**Referans:** [`ONKAYIT_2.md`](file:///c:/Users/HP-PC/OneDrive/Pictures/Desktop/climathon%20v2/ONKAYIT_2.md) • [`VERI_HAZIRLAMA_KURALLARI.md`](file:///c:/Users/HP-PC/OneDrive/Pictures/Desktop/climathon%20v2/VERI_HAZIRLAMA_KURALLARI.md) • [`docs/DONDURMA_MANIFESTI_2020.md`](file:///c:/Users/HP-PC/OneDrive/Pictures/Desktop/climathon%20v2/docs/DONDURMA_MANIFESTI_2020.md)  

---

## 1. Onaylanan Eğitim Kümesi (Seçenek A)

Kullanıcı onayı doğrultusunda **Seçenek A** uygulanacaktır:

1. **Eğitim Verisi:** 2019 yılının tamamına ait, önceden belirlenen dışsallaştırılmış veri hijyeni filtrelerinden geçen beyanlı oturumlar:
   - Ocak–Haziran 2019: **13.123 oturum** (`acn_oturumlar_v2.csv`)
   - Temmuz–Aralık 2019: **12.298 oturum** (`acn_oturumlar_temmuz_aralik.csv`)
   - **Toplam Eğitim Kümesi ($N_{\text{egit}}$):** **25.421 oturum**
2. **Dondurulmuş Model Mimarisi:**
   - Süre Şampiyonu: `GradientBoosting` (Quantile Regresyon: $q_{20}, q_{50}, q_{80}$)
   - Enerji Şampiyonu: `GradientBoosting` (Quantile Regresyon: $q_{20}, q_{50}, q_{80}$)
   - Hiperparametreler, ön işleme adımları ve imputer stratejileri dondurulmuştur; yeni hiperparametre araması yapılmayacaktır.
3. **Boyutsuzlaştırma Ölçekleri ($s_{\text{egit}}$):**
   - $s_{\text{sure}}$ ve $s_{\text{kwh}}$ ölçekleri **yalnızca 2019 eğitim verisinden** hesaplanacaktır ($\max(\text{IQR}, \sigma, 1.0)$). 2020 verisi ölçek hesaplamasına dahil edilmeyecektir.
4. **2020 İzolasyonu:**
   - 2020 holdout oturumları model eğitimine, model seçimine veya eşik optimizasyonuna **kesinlikle sokulmayacaktır**.

---

## 2. Kullanıcı Geçmişi Özellikleri ve Kronolojik Akış (`strict_shift=True`)

Kullanıcının netleştirilmesini istediği soru:  
> *"2020 tahminlerinde `gecmis_sure`, `gecmis_kwh` ve `gecmis_n` özellikleri hesaplanırken, ilgili bağlantı anından önce tamamlanmış 2019 oturumlarının yanı sıra önceki 2020 oturumları da kullanılabiliyor mu?"*

### Kural ve Uygulama:

**EVET, kullanılabilir ve operasyonel gerçekliğe uygun olarak kullanılmalıdır.**

Gerçek bir akıllı şarj sisteminde 15 Ocak 2020'de istasyona bağlanan bir araç için:
1. Sürücünün 2019 yılı boyunca tamamladığı tüm oturumlar operasyonel olarak bilinmektedir.
2. Sürücünün 1 Ocak 2020 ile 15 Ocak 2020 bağlantı anı arasında **fiilen tamamlanmış** ($disconnectTime \le connectionTime$) önceki 2020 oturumları da operasyonel olarak bilinmektedir.
3. Ancak bağlantı anında **hâlâ devam eden (çakışan)** veya **gelecekte gerçekleşecek** hiçbir oturum geçmişe dahil edilemez.

### Matematiksel ve Kod Garantisi:

Eğitim ve test özellik matrisi aynı sıralı kural ile tek seferde üretilecektir:

```python
# 1. 2019 ve 2020 verilerini kesin kronolojik sırayla birleştir
df_tum = pd.concat([df_2019_temiz, df_2020_temiz]).sort_values("connectionTime").reset_index(drop=True)

# 2. strict_shift=True ile özellik matrisini üret
X_tum = veri_hijyeni.ozellikler(df_tum, strict_shift=True)

# 3. Eğitim ve test dilimlerine ayır
X_2019 = X_tum.iloc[:len(df_2019_temiz)].copy()
X_2020 = X_tum.iloc[len(df_2019_temiz):].copy()
```

### Neden Gelecek Bilgisi Sızıntısı Yoktur?
- `strict_shift=True` algoritması, her kullanıcı kümesi içinde yalnızca $disconnectTime_{\text{onceki}} \le connectionTime_{\text{mevcut}}$ koşulunu sağlayan oturumların `sure_dk` ve `kWhDelivered` değerlerini kümülatif toplama dahil eder.
- 2019 oturumlarının tamamı 2020-01-01'den önce ayrıldığı için tüm 2020 oturumları karşısında bu koşulu doğal olarak sağlar.
- 2020 içindeki önceki bir oturum, mevcut oturumun bağlantı anında henüz şarjı bitmemişse (örneğin akşam takılıp ertesi gün devam eden araç) geçmiş ortalamasına **dahil edilmez**.
- 2020 hedef değişkenleri (`sure_dk`, `kWhDelivered`) hiçbir zaman özellik matrisine doğrudan girmez; sadece geçmişte tamamlanmış oturumların kümülatif ortalaması olarak yer alır.
- İlk kez 2020'de görülen yeni bir kullanıcı için `gecmis_n = 0` olur ve eksik değerler 2019 eğitim verisinden öğrenilen medyan ile doldurulur.

---

## 3. Ön Kayıt ve Dondurma Kurallarına Uyumluluk

1. [`ONKAYIT_2.md`](file:///c:/Users/HP-PC/OneDrive/Pictures/Desktop/climathon%20v2/ONKAYIT_2.md) dosyasındaki hiçbir kural, hipotez veya eşik değiştirilmemiştir.
2. [`docs/DONDURMA_MANIFESTI_2020.md`](file:///c:/Users/HP-PC/OneDrive/Pictures/Desktop/climathon%20v2/docs/DONDURMA_MANIFESTI_2020.md) içindeki 20 dosyanın SHA-256 kriptografik özetleri kilitlenmiştir.
3. 2020 verisi henüz indirilmemiştir; indirme işlemi kullanıcının bu protokolü onaylamasının ardından kendi bilgisayarında yürütülecektir.
