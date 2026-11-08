#!/bin/bash
# ParkOS — Mac ishga tushiruvchi
# Bu faylni ikki marta bosing, terminal ochilmaydi

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# ── Python tekshirish ──
if ! command -v python3 &>/dev/null; then
  osascript -e 'display alert "Python topilmadi" message "python.org saytidan Python 3 ni yuklab o'\''rnating." as critical'
  exit 1
fi

# ── Virtual muhit yo'q bo'lsa — yaratish ──
if [ ! -d "$DIR/venv" ]; then
  osascript -e 'display notification "Virtual muhit yaratilmoqda..." with title "ParkOS"'
  python3 -m venv "$DIR/venv"
fi

# ── Kutubxonalar o'rnatish ──
"$DIR/venv/bin/pip" install -q -r "$DIR/requirements.txt"

# ── Migrations ──
"$DIR/venv/bin/python" manage.py migrate --run-syncdb -q 2>/dev/null

# ── Port tekshirish (8000 band bo'lsa — o'ldirish) ──
lsof -ti:8000 | xargs kill -9 2>/dev/null

# ── Serverni fonda ishga tushirish ──
"$DIR/venv/bin/python" manage.py runserver 8000 \
  --noreload --nothreading \
  >> "$DIR/parking_log.txt" 2>&1 &

SERVER_PID=$!
echo $SERVER_PID > "$DIR/.server.pid"

# ── Server tayyor bo'lgunicha kutish ──
for i in {1..20}; do
  sleep 0.5
  if curl -s http://127.0.0.1:8000 >/dev/null 2>&1; then
    break
  fi
done

# ── Superuser bormi? ──
HAS_SUPER=$("$DIR/venv/bin/python" -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
django.setup()
from django.contrib.auth.models import User
print('yes' if User.objects.filter(is_superuser=True).exists() else 'no')
" 2>/dev/null)

if [ "$HAS_SUPER" = "no" ]; then
  open "http://127.0.0.1:8000/setup/"
else
  open "http://127.0.0.1:8000/"
fi

# ── Ilova yopilguncha server ishlaydi ──
# Brauzer yopilsa ham server ishlashda davom etadi.
# To'xtatish uchun: ParkOS_stop.command ni ishga tushiring.
