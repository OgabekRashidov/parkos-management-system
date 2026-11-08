<<<<<<< HEAD
# 🅿️ Avtoturargoh — Django Web Versiyasi

## Ishga tushirish (bir marta)

```bash
# 1. Papkaga kiring
cd avtoturargoh

# 2. Django o'rnating
pip install django

# 3. Ma'lumotlar bazasini tayyorlang
python manage.py makemigrations parking
python manage.py migrate

# 4. Admin foydalanuvchi yarating
python manage.py createsuperuser

# 5. Default turlarni qo'shing (ixtiyoriy — dastur o'zi ham qo'shadi)
python manage.py shell -c "
from parking.models import VehicleType, Settings
for name, price in [('Yengil mashina',5000),('Yuk mashina',8000),('Moto',3000)]:
    VehicleType.objects.get_or_create(name=name, defaults={'price':price})
Settings.objects.get_or_create(key='total_spots', defaults={'value':'20'})
"

# 6. Serverni ishga tushiring
python manage.py runserver
```

Brauzerda oching: **http://127.0.0.1:8000**

## Xususiyatlar

| Tkinter versiya | Django versiya |
|-----------------|----------------|
| Parol bilan kirish | Login (foydalanuvchi nomi + parol) |
| Avtomobil kiritish | ✅ |
| Avtomobil chiqarish + to'lov | ✅ |
| Qidiruv | ✅ (real-vaqt AJAX) |
| Tarix | ✅ + CSV yuklab olish |
| Moliya (kirim, xarajat, balans) | ✅ |
| Kassani nollash | ✅ |
| Transport turlarini boshqarish | ✅ (qo'shish, tahrirlash, o'chirish) |
| Joylar sig'imini o'zgartirish | ✅ |

## Sahifalar

- `/` — Asosiy (ichkaridagi mashinalar + kiritish formasi)
- `/history/` — Chiqib ketganlar tarixi
- `/report/` — Moliyaviy hisobot
- `/types/` — Transport turlarini boshqarish
- `/admin/` — Django admin panel
=======
# parkos-management-system
ParkOs
>>>>>>> 38e27fef07d9393f781bb26cabeef0b72760c695
