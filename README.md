# سامانه خط نورد — 1.0.1-stable (EXE)

## اجرا
- **ویندوز:** `RollingMill.exe` را باز کنید؛ مرورگر با برنامه باز می‌شود.
- داده در `data/app.db` کنار فایل exe ذخیره می‌شود.

## ساخت با GitHub Actions
فایل workflow در `.github/workflows/build-windows.yml` است.
وابستگی به pywebview/pythonnet **حذف شده** تا خطای `Python.Runtime.Loader` رفع شود.

## ساخت محلی
```bat
pip install pyinstaller
pyinstaller --noconfirm --windowed --name RollingMill --add-data "www;www" --add-data "data;data" app.py
```
