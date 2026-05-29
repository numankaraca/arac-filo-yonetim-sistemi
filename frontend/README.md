# Frontend — Araç Filo Yönetim Sistemi

Bu klasör, projenin **arayüz (frontend)** katmanını temsil eder.

## Yapı

Django monolitik mimarisi kullanıldığından frontend dosyaları aşağıdaki klasörlerde yer almaktadır:

### 📄 Şablonlar (HTML)
```
templates/
├── base.html                  ← Ana şablon (navbar, sidebar, layout)
└── fleet/
    ├── dashboard.html         ← Gösterge paneli
    ├── vehicle_list.html      ← Araç listesi
    ├── vehicle_detail.html    ← Araç detay sayfası
    ├── vehicle_form.html      ← Araç ekle / düzenle formu
    ├── department_list.html   ← Birim yönetimi
    ├── login.html             ← Giriş sayfası
    ├── partials/              ← Tekrar kullanılan bileşenler
    └── pdf/                   ← PDF şablonları
```

### 🎨 Statik Dosyalar (CSS / JS / Görseller)
```
static/
├── css/      ← Stil dosyaları
├── js/       ← JavaScript dosyaları
└── img/      ← Logo ve görseller
```

## Kullanılan Teknolojiler

- **Bootstrap 5.3** — UI bileşenleri ve grid sistemi
- **Bootstrap Icons** — İkon kütüphanesi
- **SweetAlert2** — Modal ve bildirim kutuları
- **Django Template Engine** — Sunucu taraflı HTML render
- **Google Fonts (Inter)** — Tipografi

## Kurumsal Bilgiler

**Kurum:** İstanbul İl Göç İdaresi  
**Sistem:** Araç Filo Yönetim Sistemi  
