# Araç Filo Yönetim Sistemi

Bu proje, 128 araçlık bir filonun yönetimini sağlamak amacıyla geliştirilmiş web tabanlı bir sistemdir.

## Özellikler
- Kullanıcı ve rol yönetimi
- Araç ve personel yönetimi
- Zimmet (Araç Atama) işlemleri
- Kilometre, yakıt, bakım ve ceza takibi
- Sigorta, kasko ve muayene geçmişi

## Gereksinimler
- Python 3.9+
- PostgreSQL
- pip (Python paket yöneticisi)

## Kurulum Adımları

1. **Projeyi Klonlayın veya İndirin**
   (Bu adım, projenin mevcut dizininde zaten bulunuyorsunuz varsayılarak geçilebilir)

2. **Veritabanını Oluşturun**
   PostgreSQL'de `arac_filo` adında bir veritabanı oluşturun:
   ```sql
   CREATE DATABASE arac_filo;
   ```

3. **Sanal Ortamı Aktif Edin**
   ```bash
   # Windows
   .\venv\Scripts\activate
   ```

4. **Bağımlılıkları Yükleyin**
   ```bash
   pip install -r requirements.txt
   ```

5. **Çevre Değişkenlerini (Environment Variables) Ayarlayın**
   `.env.example` dosyasını `.env` olarak kopyalayın ve PostgreSQL bilgilerinizi girin:
   ```
   DB_NAME=arac_filo
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_HOST=localhost
   DB_PORT=5432
   ```

6. **Veritabanı Tablolarını Oluşturun (Migrations)**
   ```bash
   python manage.py migrate
   ```

7. **Süper Kullanıcı (Admin) Oluşturun**
   ```bash
   python manage.py createsuperuser
   ```

8. **Geliştirme Sunucusunu Başlatın**
   ```bash
   python manage.py runserver
   ```
   
Sisteme `http://127.0.0.1:8000/` adresinden erişebilirsiniz.