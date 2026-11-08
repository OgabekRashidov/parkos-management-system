import re
import math
import hashlib
import os
import logging
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db import transaction
import csv

from .models import Vehicle, VehicleType, ParkingHistory, Settings, SuperuserSecurityQuestion

logger = logging.getLogger(__name__)

TOTAL_SPOTS_KEY = "total_spots"
TOTAL_INCOME_KEY = "total_income"
TOTAL_EXPENSE_KEY = "total_expense"
DAILY_INCOME_KEY = "daily_income"
DAILY_DATE_KEY = "daily_date"


def login_page(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("admin_panel")
        return redirect("dashboard")
    return render(request, "parking/login.html", {})


def validate_plate(plate: str) -> None:
    """Avtomobil davlat raqamini tekshiradi. Xato bo'lsa ValueError ko'taradi."""
    if not re.match(r'^[A-Z0-9]{2,10}$', plate.upper()):
        raise ValueError(
            "Noto'g'ri raqam formati! Faqat lotin harflari va raqamlar (2-10 belgi). Misol: 01A123BC"
        )


def get_total_spots():
    return Settings.get_int(TOTAL_SPOTS_KEY, 20)


def get_finance():
    today = str(timezone.now().date())
    daily_date = Settings.get(DAILY_DATE_KEY, today)
    daily_income = Settings.get_int(DAILY_INCOME_KEY, 0)
    if daily_date != today:
        Settings.set(DAILY_DATE_KEY, today)
        Settings.set(DAILY_INCOME_KEY, 0)
        daily_income = 0
    total_income  = Settings.get_int(TOTAL_INCOME_KEY, 0)
    total_expense = Settings.get_int(TOTAL_EXPENSE_KEY, 0)
    return {
        "total_income":  total_income,
        "total_expense": total_expense,
        "balance":       total_income - total_expense,
        "daily_income":  daily_income,
        "daily_date":    daily_date,
    }


# ─────────────── ASOSIY SAHIFA ───────────────

@login_required
def dashboard(request):
    if request.user.is_superuser:
        return redirect("admin_panel")
    total_spots  = get_total_spots()
    vehicles     = Vehicle.objects.select_related("vehicle_type").all()
    occupied_cnt = vehicles.count()
    free_spots   = total_spots - occupied_cnt
    finance      = get_finance()
    types        = VehicleType.objects.all()

    context = {
        "vehicles":     vehicles,
        "total_spots":  total_spots,
        "occupied_cnt": occupied_cnt,
        "free_spots":   max(free_spots, 0),
        "finance":      finance,
        "types":        types,
    }
    return render(request, "parking/dashboard.html", context)


# ─────────────── AVTOMOBIL KIRISHI ───────────────

@login_required
@require_POST
def enter_vehicle(request):
    plate = request.POST.get("plate", "").upper().strip()
    type_id = request.POST.get("vehicle_type")

    try:
        validate_plate(plate)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("dashboard")

    if Vehicle.objects.filter(plate=plate).exists():
        messages.error(request, f"'{plate}' avtomobili allaqachon ichkarida!")
        return redirect("dashboard")

    total_spots  = get_total_spots()
    occupied_cnt = Vehicle.objects.count()
    if occupied_cnt >= total_spots:
        messages.error(request, "Bo'sh joy yo'q! Avtoturargoh to'la.")
        return redirect("dashboard")

    vtype = get_object_or_404(VehicleType, pk=type_id)
    Vehicle.objects.create(plate=plate, vehicle_type=vtype)
    logger.info(f"KIRDI | {plate} | {vtype.name}")
    messages.success(request, f"✅ {plate} ({vtype.name}) muvaffaqiyatli kiritildi.")
    return redirect("dashboard")


# ─────────────── AVTOMOBIL CHIQISHI ───────────────

@login_required
def exit_vehicle(request, plate):
    vehicle = get_object_or_404(Vehicle, plate=plate)

    exit_time  = timezone.now()
    delta_secs = (exit_time - vehicle.enter_time).total_seconds()
    hours      = max(1, math.ceil(delta_secs / 3600))
    price      = hours * vehicle.vehicle_type.price

    today        = str(exit_time.date())
    finance      = get_finance()
    daily_income = finance["daily_income"]
    if finance["daily_date"] != today:
        daily_income = 0
    daily_income += price

    with transaction.atomic():
        ParkingHistory.objects.create(
            plate        = vehicle.plate,
            vehicle_type = vehicle.vehicle_type.name,
            enter_time   = vehicle.enter_time,
            exit_time    = exit_time,
            hours        = hours,
            price        = price,
            date         = exit_time.date(),
        )
        vehicle.delete()
        Settings.set(TOTAL_INCOME_KEY,  finance["total_income"] + price)
        Settings.set(DAILY_INCOME_KEY,  daily_income)
        Settings.set(DAILY_DATE_KEY,    today)

    logger.info(f"CHIQDI | {plate} | {hours} soat | {price:,} so'm")
    messages.success(request, f"✅ {plate} chiqdi. {hours} soat — {price:,} so'm.")
    return redirect("dashboard")


# ─────────────── TARIX ───────────────

@login_required
def history(request):
    records = ParkingHistory.objects.all()[:200]
    return render(request, "parking/history.html", {"records": records})


# ─────────────── HISOBOT / MOLIYA ───────────────

@login_required
def report(request):
    finance      = get_finance()
    occupied_cnt = Vehicle.objects.count()
    total_spots  = get_total_spots()
    return render(request, "parking/report.html", {
        "finance":      finance,
        "occupied_cnt": occupied_cnt,
        "free_spots":   max(total_spots - occupied_cnt, 0),
        "total_spots":  total_spots,
    })


@login_required
@require_POST
def add_expense(request):
    try:
        amount = int(request.POST.get("amount", 0))
    except ValueError:
        messages.error(request, "Noto'g'ri summa!")
        return redirect("report")

    finance = get_finance()
    if amount <= 0:
        messages.error(request, "Xarajat musbat son bo'lishi kerak!")
    elif amount > finance["balance"]:
        messages.error(request, "Balansda yetarli mablag' yo'q!")
    else:
        Settings.set(TOTAL_EXPENSE_KEY, finance["total_expense"] + amount)
        logger.info(f"XARAJAT | {amount:,} so'm")
        messages.success(request, f"✅ {amount:,} so'm xarajat kiritildi.")
    return redirect("report")


@login_required
@require_POST
def reset_finance(request):
    old_balance = get_finance()["balance"]
    Settings.set(TOTAL_INCOME_KEY,  0)
    Settings.set(TOTAL_EXPENSE_KEY, 0)
    Settings.set(DAILY_INCOME_KEY,  0)
    Settings.set(DAILY_DATE_KEY,    str(timezone.now().date()))
    logger.info(f"KASSA NOLLASHTIRILDI | Oldingi balans: {old_balance:,} so'm")
    messages.success(request, "✅ Kassa nollashtirildi.")
    return redirect("report")


# ─────────────── SIG'IM ───────────────

@login_required
@require_POST
def set_capacity(request):
    try:
        new_cap = int(request.POST.get("capacity", 0))
    except ValueError:
        messages.error(request, "Musbat butun son kiriting!")
        return redirect("dashboard")

    occupied = Vehicle.objects.count()
    if new_cap < 1:
        messages.error(request, "Sig'im kamida 1 bo'lishi kerak!")
    elif new_cap < occupied:
        messages.error(request, f"Hozir {occupied} ta mashina ichkarida! Sig'im {occupied} dan kam bo'lishi mumkin emas.")
    else:
        Settings.set(TOTAL_SPOTS_KEY, new_cap)
        logger.info(f"SIG'IM O'ZGARTIRILDI → {new_cap}")
        messages.success(request, f"✅ Sig'im {new_cap} ta joyga o'zgartirildi.")
    return redirect("dashboard")


# ─────────────── TRANSPORT TURLARI ───────────────

@login_required
def vehicle_types(request):
    types = VehicleType.objects.all()
    return render(request, "parking/vehicle_types.html", {"types": types})


@login_required
@require_POST
def add_vehicle_type(request):
    name  = request.POST.get("name", "").strip()
    try:
        price = int(request.POST.get("price", 0))
    except ValueError:
        messages.error(request, "Narx butun son bo'lishi kerak!")
        return redirect("vehicle_types")

    if len(name) < 2:
        messages.error(request, "Tur nomi kamida 2 ta belgi bo'lishi kerak!")
    elif price <= 0:
        messages.error(request, "Narx musbat son bo'lishi kerak!")
    elif VehicleType.objects.filter(name=name).exists():
        messages.error(request, f"'{name}' turi allaqachon mavjud!")
    else:
        VehicleType.objects.create(name=name, price=price)
        logger.info(f"YANGI TUR | {name} | {price:,} so'm/soat")
        messages.success(request, f"✅ '{name}' turi {price:,} so'm narxda qo'shildi.")
    return redirect("vehicle_types")


@login_required
@require_POST
def edit_vehicle_type(request, pk):
    vtype    = get_object_or_404(VehicleType, pk=pk)
    old_name = vtype.name
    new_name = request.POST.get("name", "").strip()
    try:
        new_price = int(request.POST.get("price", 0))
    except ValueError:
        messages.error(request, "Narx butun son bo'lishi kerak!")
        return redirect("vehicle_types")

    if not new_name:
        messages.error(request, "Tur nomi bo'sh bo'lishi mumkin emas!")
    elif new_price <= 0:
        messages.error(request, "Narx musbat son bo'lishi kerak!")
    elif new_name != old_name and VehicleType.objects.filter(name=new_name).exists():
        messages.error(request, f"'{new_name}' nomi allaqachon mavjud!")
    else:
        vtype.name  = new_name
        vtype.price = new_price
        vtype.save()
        logger.info(f"TUR TAHRIRLANDI | '{old_name}'→'{new_name}' | {new_price:,} so'm/soat")
        messages.success(request, f"✅ '{old_name}' → '{new_name}' yangilandi.")
    return redirect("vehicle_types")


@login_required
@require_POST
def delete_vehicle_type(request, pk):
    vtype  = get_object_or_404(VehicleType, pk=pk)
    in_use = Vehicle.objects.filter(vehicle_type=vtype)
    if in_use.exists():
        plates = ", ".join(v.plate for v in in_use)
        messages.error(request, f"'{vtype.name}' hozir ishlatilmoqda: {plates}. Avval ularni chiqaring.")
    elif VehicleType.objects.count() <= 1:
        messages.error(request, "Kamida 1 ta tur bo'lishi kerak!")
    else:
        name = vtype.name
        vtype.delete()
        logger.info(f"TUR O'CHIRILDI | {name}")
        messages.success(request, f"✅ '{name}' turi o'chirildi.")
    return redirect("vehicle_types")


# ─────────────── CSV EKSPORT ───────────────

@login_required
def export_history_csv(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="tarix.csv"'
    response.write("\ufeff")  # BOM for Excel

    writer = csv.writer(response)
    writer.writerow(["Raqam", "Tur", "Kirish", "Chiqish", "Soat", "To'lov (so'm)", "Sana"])
    for r in ParkingHistory.objects.all():
        writer.writerow([
            r.plate, r.vehicle_type,
            r.enter_time.strftime("%d.%m.%Y %H:%M"),
            r.exit_time.strftime("%d.%m.%Y %H:%M"),
            r.hours, r.price,
            r.date.strftime("%d.%m.%Y"),
        ])
    return response


# ─────────────── ADMIN SETUP ───────────────

def setup_admin(request):
    from django.contrib.auth.models import User
    from parking.models import SuperuserSecurityQuestion
    import hashlib

    # Agar superuser allaqachon mavjud bo'lsa — kirish sahifasiga yo'naltir
    if User.objects.filter(is_superuser=True).exists():
        messages.info(request, "Admin allaqachon mavjud. Iltimos, kiring.")
        return redirect("login")

    # Brute-force himoya: bir seansdagi urinishlarni cheklaymiz
    attempts = request.session.get("setup_admin_attempts", 0)
    if attempts >= 5:
        messages.error(request, "Juda ko'p urinish. Sahifani yangilang va qayta boshlang.")
        return render(request, "parking/setup_admin.html", {
            "error": "Juda ko'p urinish. Sahifani yangilang.",
            "blocked": True,
            "defaults": {},
            "preset_questions": [],
        })

    defaults = {"username": "", "password1": "", "password2": ""}

    PRESET_QUESTIONS = [
        "Tug'ilgan shahringiz?",
        "Birinchi maktabingiz nomi?",
        "Sevimli hayvon turiningiz?",
        "Onangizning qizlik familiyasi?",
        "Bolaligingizda sevimli o'yinchangiz nomi?",
    ]

    error = None
    if request.method == "POST":
        username   = request.POST.get("username", "").strip()
        password1  = request.POST.get("password1", "")
        password2  = request.POST.get("password2", "")
        first_name = request.POST.get("first_name", "").strip()
        last_name  = request.POST.get("last_name", "").strip()
        sq_choice  = request.POST.get("sq_choice", "").strip()
        sq_custom  = request.POST.get("sq_custom", "").strip()
        sq_answer  = request.POST.get("sq_answer", "").strip()

        question = sq_custom if sq_choice == "__custom__" else sq_choice

        if not username:
            error = "Foydalanuvchi nomi bo'sh bo'lishi mumkin emas."
        elif len(password1) < 8:
            error = "Parol kamida 8 ta belgi bo'lishi kerak."
        elif password1 != password2:
            error = "Parollar mos kelmadi."
        elif not question:
            error = "Maxfiy savol tanlanmagan."
        elif len(sq_answer) < 2:
            error = "Maxfiy savol javobi kamida 2 ta belgi bo'lishi kerak."
        else:
            answer_hash = hashlib.sha256(sq_answer.lower().strip().encode()).hexdigest()
            user = User.objects.create_superuser(
                username=username, password=password1,
                first_name=first_name, last_name=last_name
            )
            SuperuserSecurityQuestion.objects.all().delete()
            SuperuserSecurityQuestion.objects.create(
                question=question,
                answer_hash=answer_hash,
            )
            logger.info(f"SUPERUSER YARATILDI | {username}")
            # Muvaffaqiyatli bo'lganda urinishlar hisobini tozalaymiz
            request.session.pop("setup_admin_attempts", None)
            login(request, user)
            messages.success(request, f"Admin hisob yaratildi. Xush kelibsiz, {username}!")
            return redirect("dashboard")

        if error:
            request.session["setup_admin_attempts"] = attempts + 1

    return render(request, "parking/setup_admin.html", {
        "error": error,
        "defaults": defaults,
        "preset_questions": PRESET_QUESTIONS,
    })


def reset_superuser(request):  # noqa: C901
    """Superuser parolini maxfiy savol orqali tiklash."""
    from django.contrib.auth.models import User
    from parking.models import SuperuserSecurityQuestion
    import hashlib

    sq = SuperuserSecurityQuestion.get_instance()
    if not sq:
        messages.error(request, "Maxfiy savol o'rnatilmagan. Tizim administratoriga murojaat qiling.")
        return redirect("login")

    # Brute-force himoya: noto'g'ri javoblar sonini cheklaymiz
    attempts = request.session.get("reset_su_attempts", 0)
    if attempts >= 5:
        messages.error(request, "Juda ko'p noto'g'ri urinish. Keyinroq qayta urinib ko'ring.")
        return render(request, "parking/reset_superuser.html", {
            "sq": sq,
            "error": "Juda ko'p urinish. Keyinroq qayta urinib ko'ring.",
            "success": False,
            "blocked": True,
        })

    error = None
    success = False

    if request.method == "POST":
        answer    = request.POST.get("answer", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")

        answer_hash = hashlib.sha256(answer.lower().strip().encode()).hexdigest()

        if answer_hash != sq.answer_hash:
            request.session["reset_su_attempts"] = attempts + 1
            error = "Javob noto'g'ri. Qayta urinib ko'ring."
        elif len(password1) < 8:
            error = "Yangi parol kamida 8 ta belgi bo'lishi kerak."
        elif password1 != password2:
            error = "Parollar mos kelmadi."
        else:
            superuser = User.objects.filter(is_superuser=True).first()
            if superuser:
                superuser.set_password(password1)
                superuser.save()
                from django.utils import timezone as tz
                sq.last_reset_at = tz.now()
                sq.save()
                # Muvaffaqiyatli bo'lganda urinishlar hisobini tozalaymiz
                request.session.pop("reset_su_attempts", None)
                logger.info(f"SUPERUSER PAROLI TIKLANDI | {superuser.username}")
                messages.success(request, "Parol muvaffaqiyatli tiklandi. Yangi parol bilan kiring.")
                return redirect("login")
            else:
                error = "Superuser topilmadi."

    return render(request, "parking/reset_superuser.html", {
        "sq": sq,
        "error": error,
        "success": success,
    })


# ─────────────── RO'YXATDAN O'TISH ───────────────

def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = UserCreationForm(request.POST or None)
    if request.method == "POST":
        # Ism va familiyani qo'lda biriktiramiz
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = request.POST.get("first_name", "").strip()
            user.last_name  = request.POST.get("last_name", "").strip()
            user.save()
            logger.info(f"YANGI FOYDALANUVCHI | {user.username}")
            login(request, user)
            messages.success(request, f"✅ Xush kelibsiz, {user.username}! Hisob muvaffaqiyatli yaratildi.")
            return redirect("dashboard")

    return render(request, "parking/register.html", {"form": form})


# ─────────────── PROFIL TAHRIRLASH ───────────────

@login_required
def profile(request):
    user = request.user
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name  = request.POST.get("last_name", "").strip()
        new_password1 = request.POST.get("new_password1", "")
        new_password2 = request.POST.get("new_password2", "")

        user.first_name = first_name
        user.last_name  = last_name

        if new_password1 or new_password2:
            if len(new_password1) < 8:
                messages.error(request, "Yangi parol kamida 8 ta belgi bo'lishi kerak!")
                return render(request, "parking/profile.html", {"user": user})
            if new_password1 != new_password2:
                messages.error(request, "Parollar mos kelmadi!")
                return render(request, "parking/profile.html", {"user": user})
            user.set_password(new_password1)
            user.save()
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            logger.info(f"PAROL O'ZGARTIRILDI | {user.username}")
            messages.success(request, "✅ Profil va parol muvaffaqiyatli yangilandi.")
        else:
            user.save()
            logger.info(f"PROFIL YANGILANDI | {user.username}")
            messages.success(request, "✅ Profil muvaffaqiyatli yangilandi.")

        if user.is_superuser:
            return redirect("admin_panel")
        return redirect("dashboard")

    return render(request, "parking/profile.html", {"user": user})


# ─────────────── QIDIRUV (AJAX) ───────────────

@login_required
def search_vehicle(request):
    q = request.GET.get("q", "").upper().strip()
    if q:
        vehicles = Vehicle.objects.filter(plate__icontains=q).select_related("vehicle_type")
    else:
        vehicles = Vehicle.objects.none()
    data = [
        {
            "plate":  v.plate,
            "type":   v.vehicle_type.name,
            "enter":  v.enter_time.strftime("%d.%m.%Y %H:%M"),
            "hours":  v.hours_parked(),
            "fee":    v.current_fee(),
        }
        for v in vehicles
    ]
    return JsonResponse({"results": data})


# ─────────────── ROLE-BASED LOGIN ───────────────

def login_operator(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user and not user.is_superuser:
            login(request, user)
            return redirect("dashboard")
        return render(request, "parking/login.html", {
            "error": "Foydalanuvchi nomi yoki parol noto'g'ri!",
            "role": "operator"
        })
    return redirect("login")


def login_superuser(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user and user.is_superuser:
            login(request, user)
            return redirect("admin_panel")
        return render(request, "parking/login.html", {
            "error": "Admin nomi yoki parol noto'g'ri!",
            "role": "superuser"
        })
    return redirect("login")


# ─────────────── ADMIN PANEL (OPERATORLAR) ───────────────

def superuser_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return wrapper


@superuser_required
@require_POST
def switch_user(request, pk):
    """Superuser boshqa operator sifatida tizimga kiradi (impersonate).

    Xavfsizlik choralari:
    - Faqat POST so'rovi qabul qilinadi (CSRF himoyasi ishlaydi).
    - impersonator_id oddiy ID emas — HMAC imzolangan token sifatida
      saqlanadi. Operator token ichidagi ID ni o'zgartira olmaydi,
      chunki imzo buziladi va restore_user uni rad etadi.
    """
    import hmac
    import hashlib
    from django.conf import settings as django_settings
    from django.contrib.auth.models import User

    target = get_object_or_404(User, pk=pk, is_superuser=False)
    if not target.is_active:
        messages.error(request, f"'{target.username}' bloklangan, kirish mumkin emas.")
        return redirect("admin_panel")

    admin_pk = str(request.user.pk)
    # HMAC(SECRET_KEY, admin_pk) — operator uni soxtalashtira olmaydi
    sig = hmac.new(
        django_settings.SECRET_KEY.encode(),
        admin_pk.encode(),
        hashlib.sha256,
    ).hexdigest()
    token = f"{admin_pk}:{sig}"

    request.session["impersonator_token"] = token
    login(request, target)
    logger.info(f"SEANS ALMASHINUVI | admin (pk={admin_pk}) → {target.username}")
    messages.success(request, f"✅ Siz hozir '{target.username}' sifatida kirgansiz.")
    return redirect("dashboard")


@login_required
def restore_user(request):
    """Operator seansi tugatiladi va superuser qaytadi.

    Xavfsizlik choralari:
    - Token HMAC imzosi tekshiriladi — buzilgan yoki soxta token rad etiladi.
    - Token ichidagi admin pk bazadan qayta tekshiriladi (superuser bo'lishi shart).
    - Muvaffaqiyatli yoki muvaffaqiyatsiz holatda ham token sessiondan o'chiriladi.
    """
    import hmac
    import hashlib
    from django.conf import settings as django_settings
    from django.contrib.auth.models import User

    token = request.session.get("impersonator_token")
    if not token:
        messages.error(request, "Siz hozir impersonatsiya rejimida emassiz.")
        return redirect("dashboard")

    # Tokenni har doim o'chiramiz — muvaffaqiyatsiz bo'lsa ham qayta ishlatib bo'lmasin
    del request.session["impersonator_token"]

    # Token formatini tekshirish
    try:
        admin_pk_str, provided_sig = token.rsplit(":", 1)
    except ValueError:
        logger.warning(f"IMPERSONATSIYA: noto'g'ri token formati | {request.user.username}")
        messages.error(request, "Sessiya buzilgan. Qaytadan kiring.")
        return redirect("login")

    # HMAC imzosini tekshirish (timing-safe taqqoslash)
    expected_sig = hmac.new(
        django_settings.SECRET_KEY.encode(),
        admin_pk_str.encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(provided_sig, expected_sig):
        logger.warning(f"IMPERSONATSIYA: imzo mos kelmadi | {request.user.username}")
        messages.error(request, "Sessiya buzilgan. Qaytadan kiring.")
        return redirect("login")

    # Bazadan superuserni olish
    try:
        admin_user = User.objects.get(pk=int(admin_pk_str), is_superuser=True)
    except (User.DoesNotExist, ValueError):
        logger.warning(f"IMPERSONATSIYA: admin topilmadi pk={admin_pk_str}")
        messages.error(request, "Admin topilmadi.")
        return redirect("login")

    op_name = request.user.username
    login(request, admin_user)
    logger.info(f"SEANS TIKLANDI | {op_name} → admin ({admin_user.username})")
    messages.success(request, f"✅ '{op_name}' seansidan chiqdingiz. Admin paneliga qaytdingiz.")
    return redirect("admin_panel")


@superuser_required
def admin_panel(request):
    from django.contrib.auth.models import User
    operators = User.objects.filter(is_superuser=False).order_by("-date_joined")
    active_count = operators.filter(is_active=True).count()
    vehicle_count = Vehicle.objects.count()
    superuser = request.user
    sq = SuperuserSecurityQuestion.get_instance()
    return render(request, "parking/admin_panel.html", {
        "operators": operators,
        "active_count": active_count,
        "vehicle_count": vehicle_count,
        "show_add_modal": request.GET.get("add") == "1",
        "superuser": superuser,
        "security_question": sq,
    })


@superuser_required
@require_POST
def admin_edit_superuser(request):
    import hashlib as _hashlib
    from django.contrib.auth.models import User

    user = request.user
    first_name   = request.POST.get("first_name", "").strip()
    last_name    = request.POST.get("last_name", "").strip()
    new_username = request.POST.get("username", "").strip()
    password1    = request.POST.get("password1", "")
    password2    = request.POST.get("password2", "")

    # Savol-javob maydonlari
    sq_question  = request.POST.get("sq_question", "").strip()
    sq_answer    = request.POST.get("sq_answer", "").strip()

    if not new_username:
        messages.error(request, "Foydalanuvchi nomi bo'sh bo'lishi mumkin emas!")
        return redirect("admin_panel")
    if User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
        messages.error(request, f"'{new_username}' nomi allaqachon band!")
        return redirect("admin_panel")

    user.first_name = first_name
    user.last_name  = last_name
    user.username   = new_username

    password_changed = False
    if password1 or password2:
        if len(password1) < 8:
            messages.error(request, "Parol kamida 8 ta belgi bo'lishi kerak!")
            return redirect("admin_panel")
        if password1 != password2:
            messages.error(request, "Parollar mos kelmadi!")
            return redirect("admin_panel")
        user.set_password(password1)
        password_changed = True

    user.save()

    if password_changed:
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)

    # Savol-javob yangilash (ikkalasi ham to'ldirilgan bo'lsa)
    sq_updated = False
    if sq_question or sq_answer:
        if not sq_question:
            messages.error(request, "Maxfiy savol matnini kiriting!")
            return redirect("admin_panel")
        if len(sq_answer) < 2:
            messages.error(request, "Maxfiy savol javobi kamida 2 ta belgi bo'lishi kerak!")
            return redirect("admin_panel")
        answer_hash = _hashlib.sha256(sq_answer.lower().strip().encode()).hexdigest()
        sq = SuperuserSecurityQuestion.get_instance()
        if sq:
            sq.question    = sq_question
            sq.answer_hash = answer_hash
            sq.save()
        else:
            SuperuserSecurityQuestion.objects.create(
                question=sq_question,
                answer_hash=answer_hash,
            )
        sq_updated = True
        logger.info(f"SUPERUSER MAXFIY SAVOL YANGILANDI | {user.username}")

    if password_changed and sq_updated:
        messages.success(request, "✅ Ma'lumotlar, parol va maxfiy savol-javob muvaffaqiyatli yangilandi.")
    elif password_changed:
        messages.success(request, "✅ Ma'lumotlar va parol muvaffaqiyatli yangilandi.")
    elif sq_updated:
        messages.success(request, "✅ Ma'lumotlar va maxfiy savol-javob muvaffaqiyatli yangilandi.")
    else:
        messages.success(request, "✅ Ma'lumotlar muvaffaqiyatli yangilandi.")

    logger.info(f"SUPERUSER MA'LUMOTLARI YANGILANDI | {user.username}")
    return redirect("admin_panel")


@superuser_required
@require_POST
def admin_add_operator(request):
    from django.contrib.auth.models import User
    username  = request.POST.get("username", "").strip()
    first_name = request.POST.get("first_name", "").strip()
    last_name  = request.POST.get("last_name", "").strip()
    password1  = request.POST.get("password1", "")
    password2  = request.POST.get("password2", "")

    if not username:
        messages.error(request, "Foydalanuvchi nomi bo'sh bo'lishi mumkin emas!")
    elif User.objects.filter(username=username).exists():
        messages.error(request, f"'{username}' nomi allaqachon band!")
    elif len(password1) < 8:
        messages.error(request, "Parol kamida 8 ta belgi bo'lishi kerak!")
    elif password1 != password2:
        messages.error(request, "Parollar mos kelmadi!")
    else:
        user = User.objects.create_user(
            username=username, password=password1,
            first_name=first_name, last_name=last_name
        )
        logger.info(f"OPERATOR QOSHILDI | {username}")
        messages.success(request, f"✅ '{username}' operatori muvaffaqiyatli qo'shildi.")
    return redirect("admin_panel")


@superuser_required
@require_POST
def admin_edit_operator(request, pk):
    from django.contrib.auth.models import User
    user = get_object_or_404(User, pk=pk, is_superuser=False)
    username   = request.POST.get("username", "").strip()
    first_name = request.POST.get("first_name", "").strip()
    last_name  = request.POST.get("last_name", "").strip()
    password   = request.POST.get("password", "")

    if not username:
        messages.error(request, "Foydalanuvchi nomi bo'sh bo'lishi mumkin emas!")
    elif User.objects.filter(username=username).exclude(pk=pk).exists():
        messages.error(request, f"'{username}' nomi allaqachon band!")
    else:
        user.username   = username
        user.first_name = first_name
        user.last_name  = last_name
        if password:
            if len(password) < 8:
                messages.error(request, "Yangi parol kamida 8 ta belgi bo'lishi kerak!")
                return redirect("admin_panel")
            user.set_password(password)
        user.save()
        logger.info(f"OPERATOR TAHRIRLANDI | {username}")
        messages.success(request, f"✅ '{username}' ma'lumotlari yangilandi.")
    return redirect("admin_panel")


@superuser_required
@require_POST
def admin_toggle_operator(request, pk):
    from django.contrib.auth.models import User
    user = get_object_or_404(User, pk=pk, is_superuser=False)
    user.is_active = not user.is_active
    user.save()
    status = "faollashtirildi" if user.is_active else "bloklandi"
    logger.info(f"OPERATOR {status.upper()} | {user.username}")
    messages.success(request, f"✅ '{user.username}' {status}.")
    return redirect("admin_panel")


@superuser_required
@require_POST
def admin_delete_operator(request, pk):
    from django.contrib.auth.models import User
    user = get_object_or_404(User, pk=pk, is_superuser=False)
    username = user.username
    user.delete()
    logger.info(f"OPERATOR O'CHIRILDI | {username}")
    messages.success(request, f"✅ '{username}' o'chirildi.")
    return redirect("admin_panel")
