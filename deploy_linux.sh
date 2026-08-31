#!/bin/bash
# Telegram Kino Bot - Linux VPS Auto Deployment Script

echo "🚀 Linux VPS Bot o'rnatish boshlandi..."

# Serverni yangilash
sudo apt update && sudo apt upgrade -y

# Python3, pip va venv o'rnatish
sudo apt install -y python3 python3-pip python3-venv git

# Virtualenv yaratish
python3 -m venv venv
source venv/bin/activate

# Kutubxonalarni o'rnatish
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Kutubxonalar o'rnatildi!"

# Systemd Servis faylini yaratish (24/7 avto-ishlash uchun)
BOT_DIR=$(pwd)
SERVICE_FILE="/etc/systemd/system/kino_bot.service"

sudo bash -c "cat <<EOF > $SERVICE_FILE
[Unit]
Description=Telegram Kino Bot (@Girlsfilmbot)
After=network.target

[Service]
User=root
WorkingDirectory=$BOT_DIR
ExecStart=$BOT_DIR/venv/bin/python bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF"

# Servisni ishga tushirish
sudo systemctl daemon-reload
sudo systemctl enable kino_bot
sudo systemctl restart kino_bot

echo "🎉 Bot muvaffaqiyatli VPS serverga joylandi va 24/7 rejimda ishga tushdi!"
echo "📊 Bot holatini ko'rish uchun: sudo systemctl status kino_bot"
