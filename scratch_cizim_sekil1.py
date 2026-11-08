import os
import shutil
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Şekil 1: Akış Şeması Yeniden Çizimi
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.family'] = 'sans-serif'

fig, ax = plt.subplots(figsize=(10.5, 5.2), dpi=300)
ax.set_xlim(0, 105)
ax.set_ylim(0, 55)
ax.axis('off')

# Başlık
ax.text(52.5, 52, "Açık şarj verisinden risk tabanlı bağlantı gücü önerisine uzanan hat", 
        ha='center', va='center', fontsize=12, fontweight='bold', color='#111827')

# Kutu çizme fonksiyonu
def draw_box(x, y, w, h, bg_color, border_color, title, lines, title_color='#111827', title_size=9, body_size=7.5):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.8,rounding_size=1.5",
                                 facecolor=bg_color, edgecolor=border_color, linewidth=1.2)
    ax.add_patch(rect)
    # Başlık
    if title:
        ax.text(x + w/2, y + h - 2.5, title, ha='center', va='center', 
                fontsize=title_size, fontweight='bold', color=title_color)
    # Metin satırları
    start_y = y + h - 5.5 if title else y + h/2 + (len(lines)-1)*1.2
    for i, line in enumerate(lines):
        ax.text(x + w/2, start_y - i*2.5, line, ha='center', va='center', 
                fontsize=body_size, color='#374151')

# 1. Sol Veri ve Ön Çalışma Kutuları
draw_box(4, 34, 20, 13, '#EBF5FF', '#3B82F6', "ACN-Data (iş yeri)", 
         ["2019 geliştirme", "2020 ayrı test", "2021 doğrulayıcı test"], title_color='#1D4ED8')

draw_box(4, 18, 20, 13, '#F0F9FF', '#0EA5E9', "Trondheim konut", 
         ["24 garaj; 6.878 oturum", "+ saatlik ana sayaç (1 garajda)"], title_color='#0369A1')

draw_box(4, 2, 20, 13, '#F3F4F6', '#6B7280', "Ön çalışma kodu", 
         ["15 dk simülatör", "EDF, Eşit, LP-MPC", "ikili arama motoru"], title_color='#374151')

# 2. Yatay İş Paketleri Hattı (İP1 -> İP2 -> İP3 -> İP5)
draw_box(29, 26, 15, 15, '#FEF3C7', '#F59E0B', "İP1", 
         ["Ortak şema,", "veri dondurma", "ve ön kayıt"], title_color='#B45309', title_size=10)

draw_box(47, 26, 16, 15, '#FEF3C7', '#F59E0B', "İP2", 
         ["Gün-saha bazında", "asgari kapasite", "(4 planlayıcı)"], title_color='#B45309', title_size=10)

draw_box(66, 26, 15, 15, '#FEF3C7', '#F59E0B', "İP3", 
         ["Risk tabanlı", "boyutlandırma", "+ güven aralığı"], title_color='#B45309', title_size=10)

draw_box(84, 26, 16, 15, '#ECFDF5', '#10B981', "İP5", 
         ["Kapasite Danışmanı", "karar destek", "aracı"], title_color='#047857', title_size=10)

# 3. İP4 Kutusu (Alt Ortada)
draw_box(44, 4, 39, 13, '#EEF2FF', '#6366F1', 
         "İP4: Aktarım Testi", 
         ["2019 → 2020/2021 ve iş yeri → konut",
          "(önerilen kapasitenin test günlerindeki kapsama oranı K)"], 
         title_color='#4338CA', title_size=9)

# 4. Sağ Çıktı Kutusu (Kapasite Çıktısı)
draw_box(84, 5, 17, 13, '#FFFFFF', '#9CA3AF', "Çıktı Biçimi", 
         ["C_α = ... kW", "GA (Güven Aralığı)", "Kapsama: ≥%92"], title_color='#111827', title_size=9, body_size=7.5)

# Oklar
arrow_style = dict(arrowstyle="->,head_width=0.4,head_length=0.6", color='#4B5563', lw=1.3)

# Sol kutulardan İP1'e
ax.annotate("", xy=(29, 36), xytext=(24, 40.5), arrowprops=arrow_style)
ax.annotate("", xy=(29, 33.5), xytext=(24, 24.5), arrowprops=arrow_style)
ax.annotate("", xy=(29, 31), xytext=(24, 8.5), arrowprops=arrow_style)

# İP1 -> İP2 -> İP3 -> İP5
ax.annotate("", xy=(47, 33.5), xytext=(44, 33.5), arrowprops=arrow_style)
ax.annotate("", xy=(66, 33.5), xytext=(63, 33.5), arrowprops=arrow_style)
ax.annotate("", xy=(84, 33.5), xytext=(81, 33.5), arrowprops=arrow_style)

# İP3'ten İP4'e ve İP4'ten İP5'e
ax.annotate("", xy=(63.5, 17), xytext=(73.5, 26), arrowprops=arrow_style)
ax.annotate("", xy=(92, 26), xytext=(83, 13), arrowprops=arrow_style)

# İP5'ten Çıktı Kutusuna
ax.annotate("", xy=(92, 17), xytext=(92, 26), arrowprops=arrow_style)

plt.tight_layout()
os.makedirs("docs", exist_ok=True)
out_path = "docs/sekil1_akis_semasi.png"
plt.savefig(out_path, dpi=300, bbox_inches='tight')
print(f"Şekil 1 kaydedildi: {out_path}")

artifact_dir = r"C:\Users\HP-PC\.gemini\antigravity\brain\bfa06e6f-39c3-42a2-b9ad-5c3db15ad755"
shutil.copy(out_path, os.path.join(artifact_dir, "sekil1_akis_semasi.png"))
print("Artifact dizinine kopyalandı.")
