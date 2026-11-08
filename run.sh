#!/bin/bash
# Avtoturargoh Django loyihasini ishga tushirish

python3 -m venv venv
source venv/bin/activate
pip install django


echo ""
echo "=== Ma'lumotlar bazasi tayyorlanmoqda ==="
python manage.py makemigrations parking
python manage.py migrate

echo ""
echo "=== Default transport turlari qo'shilmoqda ==="
python manage.py shell -c "
from parking.models import VehicleType, Settings
for name, price in [('Yengil mashina',5000),('Yuk mashina',8000),('Moto',3000)]:
    VehicleType.objects.get_or_create(name=name, defaults={'price':price})
Settings.objects.get_or_create(key='total_spots', defaults={'value':'20'})
print('Tayyor!')
"

echo ""
echo "✅ Hammasi tayyor! Server ishga tushirilmoqda..."
echo "Brauzerda oching: http://127.0.0.1:8000/setup/"
echo ""
python manage.py runserver
