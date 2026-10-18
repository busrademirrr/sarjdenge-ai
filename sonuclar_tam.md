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

|   f | yontem             |   gun |    ok |   teslim |   erken_ok |   p10 |
|----:|:-------------------|------:|------:|---------:|-----------:|------:|
| 0.5 | edf_beyan          |    68 | 0.92  |    0.964 |      0.796 | 0.944 |
| 0.5 | edf_tahmin_guvenli |    68 | 0.909 |    0.971 |      0.806 | 0.946 |
| 0.5 | fcfs_beyan         |    68 | 0.892 |    0.959 |      0.77  | 0.864 |
| 0.5 | llf_beyan          |    68 | 0.913 |    0.974 |      0.773 | 0.924 |
| 0.5 | llf_tahmin_guvenli |    68 | 0.899 |    0.973 |      0.798 | 0.932 |
| 0.5 | mpc_beyan          |    68 | 0.909 |    0.973 |      0.747 | 0.93  |
| 0.5 | mpc_tahmin_guvenli |    68 | 0.883 |    0.97  |      0.761 | 0.922 |
| 0.5 | mpc_tahmin_ortanca |    68 | 0.858 |    0.962 |      0.747 | 0.902 |
| 0.7 | edf_beyan          |    68 | 0.944 |    0.986 |      0.868 | 0.978 |
| 0.7 | edf_tahmin_guvenli |    68 | 0.938 |    0.987 |      0.872 | 0.978 |
| 0.7 | fcfs_beyan         |    68 | 0.935 |    0.985 |      0.858 | 0.962 |
| 0.7 | llf_beyan          |    68 | 0.943 |    0.989 |      0.874 | 0.979 |
| 0.7 | llf_tahmin_guvenli |    68 | 0.935 |    0.988 |      0.866 | 0.977 |
| 0.7 | mpc_beyan          |    68 | 0.939 |    0.988 |      0.857 | 0.979 |
| 0.7 | mpc_tahmin_guvenli |    68 | 0.932 |    0.987 |      0.858 | 0.977 |
| 0.7 | mpc_tahmin_ortanca |    68 | 0.92  |    0.985 |      0.852 | 0.969 |
| 0.9 | edf_beyan          |    68 | 0.951 |    0.991 |      0.887 | 0.985 |
| 0.9 | edf_tahmin_guvenli |    68 | 0.95  |    0.991 |      0.89  | 0.985 |
| 0.9 | fcfs_beyan         |    68 | 0.95  |    0.991 |      0.887 | 0.982 |
| 0.9 | llf_beyan          |    68 | 0.952 |    0.992 |      0.896 | 0.987 |
| 0.9 | llf_tahmin_guvenli |    68 | 0.95  |    0.992 |      0.892 | 0.985 |
| 0.9 | mpc_beyan          |    68 | 0.952 |    0.992 |      0.893 | 0.986 |
| 0.9 | mpc_tahmin_guvenli |    68 | 0.95  |    0.992 |      0.89  | 0.986 |
| 0.9 | mpc_tahmin_ortanca |    68 | 0.947 |    0.991 |      0.89  | 0.985 |

## Eşleştirilmiş fark: zamanında hedef oranı (bootstrap %95 GA)

|   f | karsilastirma                  |   fark |    alt |    ust | esik_gecti   |
|----:|:-------------------------------|-------:|-------:|-------:|:-------------|
| 0.5 | mpc_tahmin_guvenli - mpc_beyan | -0.026 | -0.033 | -0.019 | False        |
| 0.5 | mpc_tahmin_ortanca - mpc_beyan | -0.051 | -0.062 | -0.041 | False        |
| 0.5 | edf_tahmin_guvenli - edf_beyan | -0.011 | -0.017 | -0.005 | False        |
| 0.5 | llf_tahmin_guvenli - llf_beyan | -0.014 | -0.022 | -0.006 | False        |
| 0.7 | mpc_tahmin_guvenli - mpc_beyan | -0.007 | -0.013 | -0.002 | False        |
| 0.7 | mpc_tahmin_ortanca - mpc_beyan | -0.019 | -0.026 | -0.013 | False        |
| 0.7 | edf_tahmin_guvenli - edf_beyan | -0.005 | -0.01  | -0.001 | False        |
| 0.7 | llf_tahmin_guvenli - llf_beyan | -0.007 | -0.013 | -0.002 | False        |
| 0.9 | mpc_tahmin_guvenli - mpc_beyan | -0.002 | -0.005 |  0.002 | False        |
| 0.9 | mpc_tahmin_ortanca - mpc_beyan | -0.005 | -0.008 | -0.003 | False        |
| 0.9 | edf_tahmin_guvenli - edf_beyan | -0.001 | -0.005 |  0.002 | False        |
| 0.9 | llf_tahmin_guvenli - llf_beyan | -0.001 | -0.005 |  0.002 | False        |

Önceden yazılmış eşik: ana karşılaştırma mpc_tahmin_guvenli - mpc_beyan, fark >= 0.02 ve GA alt ucu > 0.
