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
| 0.5 | edf_beyan          |    59 | 0.879 |    0.937 |      0.699 | 0.886 |
| 0.5 | edf_tahmin_dengeli |    59 | 0.845 |    0.947 |      0.712 | 0.869 |
| 0.5 | edf_tahmin_guvenli |    59 | 0.862 |    0.95  |      0.73  | 0.876 |
| 0.5 | fcfs_beyan         |    59 | 0.845 |    0.931 |      0.68  | 0.764 |
| 0.5 | llf_beyan          |    59 | 0.859 |    0.95  |      0.673 | 0.845 |
| 0.5 | llf_tahmin_guvenli |    59 | 0.842 |    0.954 |      0.724 | 0.844 |
| 0.5 | mpc_beyan          |    59 | 0.857 |    0.948 |      0.665 | 0.848 |
| 0.5 | mpc_tahmin_dengeli |    59 | 0.818 |    0.944 |      0.669 | 0.836 |
| 0.5 | mpc_tahmin_guvenli |    59 | 0.84  |    0.951 |      0.701 | 0.862 |
| 0.5 | mpc_tahmin_ortanca |    59 | 0.808 |    0.94  |      0.656 | 0.805 |
| 0.7 | edf_beyan          |    59 | 0.916 |    0.978 |      0.784 | 0.961 |
| 0.7 | edf_tahmin_dengeli |    59 | 0.903 |    0.98  |      0.795 | 0.958 |
| 0.7 | edf_tahmin_guvenli |    59 | 0.913 |    0.981 |      0.813 | 0.958 |
| 0.7 | fcfs_beyan         |    59 | 0.906 |    0.976 |      0.788 | 0.938 |
| 0.7 | llf_beyan          |    59 | 0.92  |    0.982 |      0.802 | 0.953 |
| 0.7 | llf_tahmin_guvenli |    59 | 0.913 |    0.983 |      0.815 | 0.949 |
| 0.7 | mpc_beyan          |    59 | 0.922 |    0.983 |      0.798 | 0.962 |
| 0.7 | mpc_tahmin_dengeli |    59 | 0.898 |    0.979 |      0.786 | 0.942 |
| 0.7 | mpc_tahmin_guvenli |    59 | 0.912 |    0.982 |      0.811 | 0.954 |
| 0.7 | mpc_tahmin_ortanca |    59 | 0.895 |    0.979 |      0.782 | 0.935 |
| 0.9 | edf_beyan          |    59 | 0.934 |    0.989 |      0.831 | 0.977 |
| 0.9 | edf_tahmin_dengeli |    59 | 0.93  |    0.988 |      0.834 | 0.977 |
| 0.9 | edf_tahmin_guvenli |    59 | 0.933 |    0.989 |      0.838 | 0.977 |
| 0.9 | fcfs_beyan         |    59 | 0.933 |    0.989 |      0.834 | 0.976 |
| 0.9 | llf_beyan          |    59 | 0.935 |    0.99  |      0.835 | 0.977 |
| 0.9 | llf_tahmin_guvenli |    59 | 0.934 |    0.99  |      0.838 | 0.978 |
| 0.9 | mpc_beyan          |    59 | 0.935 |    0.99  |      0.831 | 0.978 |
| 0.9 | mpc_tahmin_dengeli |    59 | 0.931 |    0.989 |      0.834 | 0.975 |
| 0.9 | mpc_tahmin_guvenli |    59 | 0.935 |    0.99  |      0.838 | 0.978 |
| 0.9 | mpc_tahmin_ortanca |    59 | 0.93  |    0.988 |      0.831 | 0.975 |

## Eşleştirilmiş fark: zamanında hedef oranı (bootstrap %95 GA)

|   f | karsilastirma                  |   fark |    alt |    ust | esik_gecti   |
|----:|:-------------------------------|-------:|-------:|-------:|:-------------|
| 0.5 | mpc_tahmin_guvenli - mpc_beyan | -0.017 | -0.028 | -0.006 | False        |
| 0.5 | mpc_tahmin_ortanca - mpc_beyan | -0.049 | -0.062 | -0.036 | False        |
| 0.5 | edf_tahmin_guvenli - edf_beyan | -0.017 | -0.028 | -0.006 | False        |
| 0.5 | llf_tahmin_guvenli - llf_beyan | -0.017 | -0.028 | -0.007 | False        |
| 0.5 | mpc_tahmin_dengeli - mpc_beyan | -0.039 | -0.05  | -0.028 | False        |
| 0.5 | edf_tahmin_dengeli - edf_beyan | -0.033 | -0.047 | -0.02  | False        |
| 0.7 | mpc_tahmin_guvenli - mpc_beyan | -0.01  | -0.018 | -0.002 | False        |
| 0.7 | mpc_tahmin_ortanca - mpc_beyan | -0.026 | -0.036 | -0.018 | False        |
| 0.7 | edf_tahmin_guvenli - edf_beyan | -0.003 | -0.011 |  0.005 | False        |
| 0.7 | llf_tahmin_guvenli - llf_beyan | -0.007 | -0.013 | -0     | False        |
| 0.7 | mpc_tahmin_dengeli - mpc_beyan | -0.024 | -0.033 | -0.015 | False        |
| 0.7 | edf_tahmin_dengeli - edf_beyan | -0.012 | -0.022 | -0.003 | False        |
| 0.9 | mpc_tahmin_guvenli - mpc_beyan |  0     | -0.004 |  0.005 | False        |
| 0.9 | mpc_tahmin_ortanca - mpc_beyan | -0.005 | -0.01  | -0.001 | False        |
| 0.9 | edf_tahmin_guvenli - edf_beyan | -0.001 | -0.006 |  0.004 | False        |
| 0.9 | llf_tahmin_guvenli - llf_beyan | -0.001 | -0.005 |  0.003 | False        |
| 0.9 | mpc_tahmin_dengeli - mpc_beyan | -0.004 | -0.01  |  0.001 | False        |
| 0.9 | edf_tahmin_dengeli - edf_beyan | -0.004 | -0.008 |  0.001 | False        |

Önceden yazılmış eşik: ana karşılaştırma mpc_tahmin_guvenli - mpc_beyan, fark >= 0.02 ve GA alt ucu > 0.
