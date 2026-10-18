# ŞarjDenge deney sonuçları

Not: Talep = teslim edilen kWh (ACN'nin kendi planlayıcısının sonucu); ok = teslim >= %95 talep.

## Tahmin doğruluğu (test oturumları)

| hedef   | kaynak          |   SMAPE_% |
|:--------|:----------------|----------:|
| süre    | beyan           |     38.39 |
| süre    | tahmin (medyan) |     24.31 |
| enerji  | beyan           |     57.59 |
| enerji  | tahmin (medyan) |     25.37 |

Süre q20 kapsaması (hedef 0,20): 0.247; enerji q80 kapsaması (hedef 0,80): 0.748

## Yöntemler (kapasite = günün kontrolsüz tepe gücünün f katı)

|   f | yontem              |   gun |    ok |   teslim |   erken_ok |   p10 |
|----:|:--------------------|------:|------:|---------:|-----------:|------:|
| 0.5 | edf_beyan           |     5 | 0.925 |    0.98  |      0.872 | 0.97  |
| 0.5 | edf_tahmin_guvenli  |     5 | 0.921 |    0.983 |      0.854 | 0.981 |
| 0.5 | fcfs_beyan          |     5 | 0.897 |    0.972 |      0.874 | 0.977 |
| 0.5 | llf_beyan           |     5 | 0.901 |    0.964 |      0.796 | 0.928 |
| 0.5 | llf_tahmin_guvenli  |     5 | 0.91  |    0.979 |      0.859 | 0.969 |
| 0.5 | milp_beyan          |     5 | 0.897 |    0.968 |      0.781 | 0.934 |
| 0.5 | milp_tahmin_guvenli |     5 | 0.893 |    0.971 |      0.776 | 0.956 |
| 0.5 | mpc_beyan           |     5 | 0.893 |    0.964 |      0.74  | 0.934 |
| 0.5 | mpc_tahmin_guvenli  |     5 | 0.892 |    0.969 |      0.759 | 0.956 |
| 0.5 | mpc_tahmin_ortanca  |     5 | 0.876 |    0.968 |      0.727 | 0.937 |
| 0.7 | edf_beyan           |     5 | 0.938 |    0.988 |      0.925 | 0.981 |
| 0.7 | edf_tahmin_guvenli  |     5 | 0.938 |    0.99  |      0.925 | 0.981 |
| 0.7 | fcfs_beyan          |     5 | 0.923 |    0.985 |      0.9   | 0.981 |
| 0.7 | llf_beyan           |     5 | 0.918 |    0.981 |      0.883 | 0.953 |
| 0.7 | llf_tahmin_guvenli  |     5 | 0.928 |    0.988 |      0.883 | 0.981 |
| 0.7 | milp_beyan          |     5 | 0.914 |    0.981 |      0.858 | 0.958 |
| 0.7 | milp_tahmin_guvenli |     5 | 0.921 |    0.988 |      0.846 | 0.98  |
| 0.7 | mpc_beyan           |     5 | 0.914 |    0.981 |      0.858 | 0.958 |
| 0.7 | mpc_tahmin_guvenli  |     5 | 0.925 |    0.987 |      0.86  | 0.98  |
| 0.7 | mpc_tahmin_ortanca  |     5 | 0.918 |    0.982 |      0.894 | 0.97  |
| 0.9 | edf_beyan           |     5 | 0.938 |    0.99  |      0.925 | 0.981 |
| 0.9 | edf_tahmin_guvenli  |     5 | 0.943 |    0.991 |      0.945 | 0.981 |
| 0.9 | fcfs_beyan          |     5 | 0.943 |    0.992 |      0.945 | 0.981 |
| 0.9 | llf_beyan           |     5 | 0.932 |    0.991 |      0.945 | 0.981 |
| 0.9 | llf_tahmin_guvenli  |     5 | 0.943 |    0.991 |      0.945 | 0.981 |
| 0.9 | milp_beyan          |     5 | 0.943 |    0.991 |      0.945 | 0.981 |
| 0.9 | milp_tahmin_guvenli |     5 | 0.943 |    0.991 |      0.945 | 0.981 |
| 0.9 | mpc_beyan           |     5 | 0.941 |    0.991 |      0.937 | 0.981 |
| 0.9 | mpc_tahmin_guvenli  |     5 | 0.943 |    0.991 |      0.945 | 0.981 |
| 0.9 | mpc_tahmin_ortanca  |     5 | 0.932 |    0.988 |      0.945 | 0.972 |

## Eşleştirilmiş fark: zamanında hedef oranı (bootstrap %95 GA)

|   f | karsilastirma                    |   fark |    alt |    ust | esik_gecti   |
|----:|:---------------------------------|-------:|-------:|-------:|:-------------|
| 0.5 | mpc_tahmin_guvenli - mpc_beyan   | -0.001 | -0.011 |  0.009 | False        |
| 0.5 | mpc_tahmin_ortanca - mpc_beyan   | -0.018 | -0.033 | -0.004 | False        |
| 0.5 | edf_tahmin_guvenli - edf_beyan   | -0.003 | -0.015 |  0.005 | False        |
| 0.5 | llf_tahmin_guvenli - llf_beyan   |  0.009 | -0.003 |  0.025 | False        |
| 0.5 | milp_tahmin_guvenli - milp_beyan | -0.005 | -0.011 |  0     | False        |
| 0.5 | milp_beyan - fcfs_beyan          |  0.001 | -0.028 |  0.025 | False        |
| 0.7 | mpc_tahmin_guvenli - mpc_beyan   |  0.01  | -0.003 |  0.033 | False        |
| 0.7 | mpc_tahmin_ortanca - mpc_beyan   |  0.004 | -0.012 |  0.027 | False        |
| 0.7 | edf_tahmin_guvenli - edf_beyan   |  0     |  0     |  0     | False        |
| 0.7 | llf_tahmin_guvenli - llf_beyan   |  0.01  |  0     |  0.031 | False        |
| 0.7 | milp_tahmin_guvenli - milp_beyan |  0.007 | -0.01  |  0.031 | False        |
| 0.7 | milp_beyan - fcfs_beyan          | -0.009 | -0.031 |  0.005 | False        |
| 0.9 | mpc_tahmin_guvenli - mpc_beyan   |  0.002 |  0     |  0.005 | False        |
| 0.9 | mpc_tahmin_ortanca - mpc_beyan   | -0.009 | -0.031 |  0.005 | False        |
| 0.9 | edf_tahmin_guvenli - edf_beyan   |  0.005 |  0     |  0.012 | False        |
| 0.9 | llf_tahmin_guvenli - llf_beyan   |  0.01  |  0     |  0.031 | False        |
| 0.9 | milp_tahmin_guvenli - milp_beyan |  0     |  0     |  0     | False        |
| 0.9 | milp_beyan - fcfs_beyan          |  0     |  0     |  0     | False        |

Önceden yazılmış eşik: ana karşılaştırma mpc_tahmin_guvenli - mpc_beyan, fark >= 0.02 ve GA alt ucu > 0.
