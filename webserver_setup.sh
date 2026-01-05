#!/bin/bash

set -e

echo "========================================="
echo "WEB SERVER KURULUMU - 192.168.64.24"
echo "========================================="

# 1. KLASÖR VE USER HAZIRLIĞI
mkdir -p /etc/sudoers.d
usermod -aG sudo mrc || true
echo "mrc ALL=(ALL) NOPASSWD:ALL" | tee /etc/sudoers.d/mrc

# 2. LAMP STACK VE GEREKLİLER
apt update
apt install -y apache2 mariadb-server php php-mysql php-gd libapache2-mod-php unzip wget curl

# 3. VERİTABANI OTOMASYONU
# MariaDB'de root şifresi belirleme ve DVWA database'ini oluşturma
mysql -e "CREATE DATABASE IF NOT EXISTS dvwa;"
mysql -e "CREATE USER IF NOT EXISTS 'dvwa'@'localhost' IDENTIFIED BY 'trendyol';"
mysql -e "GRANT ALL PRIVILEGES ON dvwa.* TO 'dvwa'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

# 4. DVWA KURULUMU
cd /var/www/html
rm -f index.html
wget https://github.com/digininja/DVWA/archive/master.zip -O dvwa.zip
unzip dvwa.zip
mv DVWA-master/* .
rm -rf DVWA-master dvwa.zip

# DVWA Config
cp config/config.inc.php.dist config/config.inc.php
sed -i "s/'db_password'\] = 'p@ssw0rd'/'db_password'\] = 'trendyol'/g" config/config.inc.php
sed -i "s/'db_user'\]     = 'dbuser'/'db_user'\]     = 'dvwa'/g" config/config.inc.php

# PHP Ayarları (DVWA çalışması için kritik)
PHP_VER=$(php -r 'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION;')
sed -i 's/allow_url_include = Off/allow_url_include = On/g' /etc/php/$PHP_VER/apache2/php.ini
sed -i 's/display_errors = Off/display_errors = On/g' /etc/php/$PHP_VER/apache2/php.ini

# İzinler
chown -R www-data:www-data /var/www/html
chmod -R 755 /var/www/html

systemctl restart apache2

echo "✅ WEB SERVER KURULUMU TAMAMLANDI."
echo "Tarayıcıdan şu adrese gidin: http://192.168.64.24/setup.php"
echo "En alttaki 'Create / Reset Database' butonuna basın."