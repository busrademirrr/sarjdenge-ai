# ŞarjDenge deney sonuçları

Not: Talep = teslim edilen kWh (ACN'nin kendi planlayıcısının sonucu); ok = teslim >= %95 talep.

## Tahmin doğruluğu (test oturumları)

| hedef   | kaynak          |   SMAPE_% |
|:--------|:----------------|----------:|
| süre    | beyan           |     49.44 |
| süre    | tahmin (medyan) |     25.86 |
| enerji  | beyan           |     56.92 |
| enerji  | tahmin (medyan) |     25.77 |

Süre q20 kapsaması (hedef 0,20): 0.212; enerji q80 kapsaması (hedef 0,80): 0.776

## Yöntemler (kapasite = günün kontrolsüz tepe gücünün f katı)

|   f | yontem             |   gun |    ok |   teslim |   erken_ok |   p10 |
|----:|:-------------------|------:|------:|---------:|-----------:|------:|
| 0.5 | edf_beyan          |     4 | 0.909 |    0.965 |      0.723 | 0.95  |
| 0.5 | edf_tahmin_dengeli |     4 | 0.919 |    0.979 |      0.765 | 0.959 |
| 0.5 | edf_tahmin_guvenli |     4 | 0.924 |    0.978 |      0.772 | 0.961 |
| 0.5 | fcfs_beyan         |     4 | 0.878 |    0.946 |      0.678 | 0.838 |
| 0.5 | llf_beyan          |     4 | 0.914 |    0.963 |      0.737 | 0.889 |
| 0.5 | llf_tahmin_guvenli |     4 | 0.922 |    0.978 |      0.778 | 0.945 |
| 0.5 | mpc_beyan          |     4 | 0.92  |    0.969 |      0.758 | 0.921 |
| 0.5 | mpc_tahmin_dengeli |     4 | 0.903 |    0.975 |      0.728 | 0.935 |
| 0.5 | mpc_tahmin_guvenli |     4 | 0.918 |    0.978 |      0.749 | 0.949 |
| 0.5 | mpc_tahmin_ortanca |     4 | 0.895 |    0.962 |      0.708 | 0.875 |
| 0.7 | edf_beyan          |     4 | 0.925 |    0.983 |      0.769 | 0.968 |
| 0.7 | edf_tahmin_dengeli |     4 | 0.925 |    0.986 |      0.778 | 0.974 |
| 0.7 | edf_tahmin_guvenli |     4 | 0.929 |    0.987 |      0.784 | 0.974 |
| 0.7 | fcfs_beyan         |     4 | 0.903 |    0.979 |      0.717 | 0.948 |
| 0.7 | llf_beyan          |     4 | 0.931 |    0.977 |      0.791 | 0.941 |
| 0.7 | llf_tahmin_guvenli |     4 | 0.931 |    0.987 |      0.791 | 0.969 |
| 0.7 | mpc_beyan          |     4 | 0.906 |    0.982 |      0.729 | 0.952 |
| 0.7 | mpc_tahmin_dengeli |     4 | 0.917 |    0.982 |      0.754 | 0.958 |
| 0.7 | mpc_tahmin_guvenli |     4 | 0.931 |    0.988 |      0.791 | 0.973 |
| 0.7 | mpc_tahmin_ortanca |     4 | 0.917 |    0.978 |      0.754 | 0.945 |
| 0.9 | edf_beyan          |     4 | 0.931 |    0.989 |      0.791 | 0.982 |
| 0.9 | edf_tahmin_dengeli |     4 | 0.927 |    0.987 |      0.784 | 0.974 |
| 0.9 | edf_tahmin_guvenli |     4 | 0.931 |    0.988 |      0.791 | 0.974 |
| 0.9 | fcfs_beyan         |     4 | 0.931 |    0.99  |      0.791 | 0.982 |
| 0.9 | llf_beyan          |     4 | 0.931 |    0.987 |      0.791 | 0.969 |
| 0.9 | llf_tahmin_guvenli |     4 | 0.931 |    0.988 |      0.791 | 0.974 |
| 0.9 | mpc_beyan          |     4 | 0.922 |    0.985 |      0.765 | 0.962 |
| 0.9 | mpc_tahmin_dengeli |     4 | 0.927 |    0.987 |      0.784 | 0.974 |
| 0.9 | mpc_tahmin_guvenli |     4 | 0.927 |    0.987 |      0.778 | 0.972 |
| 0.9 | mpc_tahmin_ortanca |     4 | 0.923 |    0.984 |      0.771 | 0.967 |

## Eşleştirilmiş fark: zamanında hedef oranı (bootstrap %95 GA)

|   f | karsilastirma                  |   fark |    alt |    ust | esik_gecti   |
|----:|:-------------------------------|-------:|-------:|-------:|:-------------|
| 0.5 | mpc_tahmin_guvenli - mpc_beyan | -0.002 | -0.034 |  0.029 | False        |
| 0.5 | mpc_tahmin_ortanca - mpc_beyan | -0.025 | -0.046 | -0.008 | False        |
| 0.5 | edf_tahmin_guvenli - edf_beyan |  0.014 | -0.004 |  0.034 | False        |
| 0.5 | llf_tahmin_guvenli - llf_beyan |  0.008 | -0.011 |  0.032 | False        |
| 0.5 | mpc_tahmin_dengeli - mpc_beyan | -0.017 | -0.043 |  0.006 | False        |
| 0.5 | edf_tahmin_dengeli - edf_beyan |  0.01  | -0.006 |  0.027 | False        |
| 0.7 | mpc_tahmin_guvenli - mpc_beyan |  0.025 |  0     |  0.06  | False        |
| 0.7 | mpc_tahmin_ortanca - mpc_beyan |  0.011 | -0.017 |  0.047 | False        |
| 0.7 | edf_tahmin_guvenli - edf_beyan |  0.004 |  0     |  0.012 | False        |
| 0.7 | llf_tahmin_guvenli - llf_beyan |  0     |  0     |  0     | False        |
| 0.7 | mpc_tahmin_dengeli - mpc_beyan |  0.011 | -0.017 |  0.047 | False        |
| 0.7 | edf_tahmin_dengeli - edf_beyan |  0     | -0.006 |  0.006 | False        |
| 0.9 | mpc_tahmin_guvenli - mpc_beyan |  0.005 |  0     |  0.014 | False        |
| 0.9 | mpc_tahmin_ortanca - mpc_beyan |  0.001 | -0.008 |  0.012 | False        |
| 0.9 | edf_tahmin_guvenli - edf_beyan |  0     |  0     |  0     | False        |
| 0.9 | llf_tahmin_guvenli - llf_beyan |  0     |  0     |  0     | False        |
| 0.9 | mpc_tahmin_dengeli - mpc_beyan |  0.005 | -0.008 |  0.027 | False        |
| 0.9 | edf_tahmin_dengeli - edf_beyan | -0.004 | -0.01  |  0     | False        |

Önceden yazılmış eşik: ana karşılaştırma mpc_tahmin_guvenli - mpc_beyan, fark >= 0.02 ve GA alt ucu > 0.
