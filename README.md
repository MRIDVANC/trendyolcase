# Trendyol Network Security Engineer - WAF & IDS Case Study

## 📁 Dosya Yapısı
```
trendyolcase/
├── ids.py                  # Python IDS Engine (v15.0)
├── trigger.py              # Red Team Attack Simulator
├── nginx.conf              # Nginx Configuration
├── custom-rules.conf       # ModSecurity Custom Rules
├── NetworkSecurityCASE.pdf # Teknik Rapor
└── README.md
```

---

## 🚀 Kurulum

### 1. Gereksinimler
```bash
# Ubuntu/Debian
apt update && apt install -y nginx modsecurity-crs python3 python3-pip iptables

# Python bağımlılıkları
pip3 install psutil requests
```

### 2. IDS'i Başlat
```bash
chmod +x ids.py
sudo python3 ids.py
```

### 3. Saldırı Simülasyonu (Test Ortamı)
```bash
python3 trigger.py
```

---

## 📊 Dashboard Görünümü
```
╔══════════════════════════════════════════════════════════════════════╗
║          🛡️  TRENDYOL SOC - AUTONOMOUS DEFENSE ENGINE v15.0         ║
╠══════════════════════════════════════════════════════════════════════╣
║  UPTIME: 00:15:32 │ ATTACKS: 25 │ L7 BANS: 1 │ L4 BANS: 1          ║
╠──────────────────────────────────────────────────────────────────────╣
║  CPU: 12.3% │ RAM: 45.2% │ NETWORK: 0.15 Mbps │ LATENCY: 8.5ms     ║
╠──────────────────────────────────────────────────────────────────────╣
║  SOURCE IP         │ HITS  │ CATEGORY         │ DEFENSE STATUS      ║
╠──────────────────────────────────────────────────────────────────────╣
║  192.168.64.26     │    25 │ SQL INJECTION    │ 🚫 KERNEL DROP (L4) ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

## 🔬 Test Edilen Saldırı Vektörleri

| Teknik | Payload Örneği | Sonuç |
|--------|----------------|-------|
| SQL Injection | `1' UNION SELECT * FROM users--` | ✅ Blocked |
| XSS | `<script>alert(1)</script>` | ✅ Blocked |
| RCE | `; cat /etc/passwd` | ✅ Blocked |
| Path Traversal | `../../etc/passwd` | ✅ Blocked |
| Scanner Detection | User-Agent: sqlmap | ✅ Blocked |

---

## 📖 Teknik Dokümantasyon

Detaylı mimari, log analizi ve performans metrikleri için: **[NetworkSecurityCASE.pdf](NetworkSecurityCASE.pdf)**

---

## 🎯 Production Deployment

HA Architecture

[Internet] → [HAProxy LB] → [WAF-1 / WAF-2] → [Backend Pool]
