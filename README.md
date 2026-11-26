# سامانه خط نورد — نسخه پایدار دسکتاپ 1.0.0-stable

## ویژگی‌ها
- نسخهٔ **امضاشده / ثابت** از برنامه (SHA256 در `www/VERSION.txt`)
- **دیتابیس SQLite** در مسیر `data/app.db` کنار برنامه
- با بستن و باز کردن برنامه، داده‌های ثبت‌شده حفظ می‌شوند
- شامل تمام داده‌های ورودی اکسل قبلی (تعویض کالیبر ماه‌های ۱–۸، داشبورد شکست، موقعیت بلبرینگ و …)

## نصب (ویندوز / لینوکس / مک)

```bash
cd rolling-mill-desktop
python -m venv .venv
# ویندوز:
.venv\Scripts\activate
# لینوکس/مک:
source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

## ساخت فایل اجرایی (اختیاری)

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name "RollingMill" ^
  --add-data "www;www" --add-data "data;data" app.py
```

(در لینوکس به‌جای `;` از `:` استفاده کنید.)

پس از ساخت، پوشهٔ `dist/RollingMill` را کپی کنید. فایل `data/app.db` کنار exe ساخته/به‌روز می‌شود.

## ساختار
```
rolling-mill-desktop/
  app.py                 # اجراکننده
  requirements.txt
  www/rolling-mill-system.html
  www/VERSION.txt
  data/app.db            # پس از اولین اجرا
```

## نکات
- داده در جدول `kv` داخل SQLite ذخیره می‌شود (همان کلیدهای قبلی localStorage).
- برای پشتیبان‌گیری کافی است از `data/app.db` کپی بگیرید.
