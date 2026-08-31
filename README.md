# 🎬 Telegram Kino Bot (@Girlsfilmbot)

Ushbu Telegram bot foydalanuvchilar kiritgan maxsus kod (masalan `101`) bo'yicha kinolarni `copy_message` orqali yuboradi, hamda **3 ta majburiy kanal obunasi** va **do'stlarni taklif qilish** tugmasi bilan ta'minlangan.

## 🚀 Linux VPS Serverga Joylash (24/7 Avto-ishlash)

### 1. Serverga SSH orqali ulanish
```bash
ssh root@IP_MANZILINGIZ
```

### 2. Loyihani serverga ko'chirish
`kino_bot` papkasini serverga yuklang yoki git orqali oling.

### 3. Avto-deploy skriptini ishga tushirish
```bash
cd kino_bot
chmod +x deploy_linux.sh
./deploy_linux.sh
```

### 4. Bot holatini ko'rish
```bash
sudo systemctl status kino_bot
```

### 5. Botni qayta tushirish / to'xtatish
```bash
sudo systemctl restart kino_bot   # Qayta ishga tushirish
sudo systemctl stop kino_bot      # To'xtatish
sudo journalctl -u kino_bot -f    # Loglarni jonli ko'rish
```
