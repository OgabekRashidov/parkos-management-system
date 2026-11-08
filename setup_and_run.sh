#!/bin/bash
# Avtoturargoh Django loyihasini ishga tushirish

echo "=== Django o'rnatilmoqda ==="
pip install django

echo ""
echo "=== Ma'lumotlar bazasi tayyorlanmoqda ==="
python manage.py makemigrations parking
python manage.py migrate

echo ""
echo "=== Admin foydalanuvchi yaratilmoqda ==="
echo "Foydalanuvchi nomi: admin"
echo "Parol so'raladi:"
python manage.py createsuperuser --username admin --email admin@localhost

echo ""
echo "=== Default transport turlari qo'shilmoqda ==="
python manage.py shell -c "
from parking.models import VehicleType, Settings
defaults = [('Yengil mashina', 5000), ('Yuk mashina', 8000), ('Moto', 3000)]
for name, price in defaults:
    VehicleType.objects.get_or_create(name=name, defaults={'price': price})
Settings.objects.get_or_create(key='total_spots', defaults={'value': '20'})
print('Transport turlari qo\\'shildi.')
"

echo ""
echo "✅ Hammasi tayyor! Server ishga tushirilmoqda..."
echo "Brauzerda oching: http://127.0.0.1:8000"
echo ""
python manage.py runserver
