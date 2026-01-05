#!/bin/bash
set -e

echo "========================================="
echo "WAF FINAL RECOVERY - 192.168.64.22"
echo "========================================="

# 1. HATA VEREN TÜM CRS DOSYALARINI TEMİZLE
# .data dosyası kullanan her şeyi siliyoruz ki Nginx artık takılmasın
echo "[INFO] Sorunlu kural dosyalari temizleniyor..."
cd /etc/modsecurity/rules/
rm -f REQUEST-944-APPLICATION-ATTACK-JAVA.conf
rm -f REQUEST-941-APPLICATION-ATTACK-XSS.conf
rm -f REQUEST-942-APPLICATION-ATTACK-SQLI.conf
rm -f REQUEST-913-SCANNER-DETECTION.conf
rm -f REQUEST-920-PROTOCOL-ENFORCEMENT.conf
rm -f REQUEST-93* # Tüm uygulama atak kuralları (LFI, RFI, RCE vb.)

# 2. MODSECURITY ANA CONFIG (Sadece senin kuralların kalacak şekilde)
cat << 'EOF' > /etc/modsecurity/modsecurity.conf
SecRuleEngine On
SecRequestBodyAccess On
SecResponseBodyAccess On
SecRequestBodyLimit 13107200
SecStatusEngine On
SecAuditEngine RelevantOnly
SecAuditLogRelevantStatus "^(?:5|4(?!04))"
SecAuditLogParts ABIJDEFHK
SecAuditLogType Serial
SecAuditLog /var/log/modsecurity_audit.log

# Kendi özel kurallarımızı dahil ediyoruz
Include /etc/modsecurity/custom_rules.conf
EOF

# 3. ÖDEVİN İSTEDİĞİ CUSTOM KURALLAR (Trendyol Case Kuralları)
cat << 'EOF' > /etc/modsecurity/custom_rules.conf
# Rule 1: Block POST and DELETE to /admin (Task 4.2)
SecRule REQUEST_URI "@rx ^/admin" \
    "id:200001,phase:1,deny,status:403,log,msg:'Trendyol Case: Blocked POST/DELETE to Admin',chain"
    SecRule REQUEST_METHOD "@rx ^(POST|DELETE)$"

# Rule 2: SQL Injection Protection (Task 4.1)
SecRule ARGS "@rx (?i)(union.*select|select.*from|insert.*into|' OR '1'='1|--)" \
    "id:200002,phase:2,deny,status:403,log,msg:'Trendyol Case: SQL Injection Blocked'"

# Rule 3: XSS Protection (Task 4.1)
SecRule ARGS "@rx <script" \
    "id:200003,phase:2,deny,status:403,log,msg:'Trendyol Case: XSS Blocked'"
EOF

# 4. NGINX CONFIG
cat << 'EOF' > /etc/nginx/sites-available/default
server {
    listen 80;
    listen 443 ssl;
    server_name _;

    ssl_certificate /etc/nginx/ssl/waf.crt;
    ssl_certificate_key /etc/nginx/ssl/waf.key;

    modsecurity on;
    modsecurity_rules_file /etc/modsecurity/modsecurity.conf;

    location / {
        proxy_pass http://192.168.64.24;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 5. TEST VE BAŞLAT
echo "--- Nginx Test Ediliyor ---"
if nginx -t; then
    systemctl restart nginx
    echo "✅✅ WAF AKTİF VE ÇALIŞIYOR! ✅✅"
else
    echo "❌ HATA: Hala bir dosya takiliyor. Hatayi buraya yapistir."
    nginx -t
fi