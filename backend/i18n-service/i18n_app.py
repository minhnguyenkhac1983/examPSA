"""
Equilibrium Internationalization (i18n) Service
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import json
from typing import Dict, List, Optional

app = FastAPI(title="Equilibrium i18n Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class TranslationRequest(BaseModel):
    text: str
    source_language: str = "en"
    target_language: str
    context: Optional[str] = None

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float

class LanguageSupport(BaseModel):
    language_code: str
    language_name: str
    is_rtl: bool = False
    is_supported: bool = True

# Translation database
translations_db = {
    "en": {
        "welcome": "Welcome to Equilibrium",
        "get_price_estimate": "Get Price Estimate",
        "pickup_location": "Pickup Location",
        "dropoff_location": "Dropoff Location",
        "driver_status": "Driver Status",
        "online": "Online",
        "offline": "Offline",
        "demand_heatmap": "Demand Heatmap",
        "login": "Login",
        "logout": "Logout",
        "mobile_app": "Mobile App",
        "driver_app": "Driver App",
        "admin_portal": "Admin Portal",
        "real_time_pricing": "Real-time Dynamic Pricing",
        "location_based_pricing": "Location-based Pricing",
        "live_updates": "Live WebSocket Updates",
        "authentication": "Authentication",
        "machine_learning": "Machine Learning Pricing",
        "push_notifications": "Push Notifications",
        "analytics": "Advanced Analytics"
    },
    "vi": {
        "welcome": "Chào mừng đến với Equilibrium",
        "get_price_estimate": "Lấy Ước Tính Giá",
        "pickup_location": "Điểm Đón",
        "dropoff_location": "Điểm Đến",
        "driver_status": "Trạng Thái Tài Xế",
        "online": "Trực Tuyến",
        "offline": "Ngoại Tuyến",
        "demand_heatmap": "Bản Đồ Nhiệt Nhu Cầu",
        "login": "Đăng Nhập",
        "logout": "Đăng Xuất",
        "mobile_app": "Ứng Dụng Di Động",
        "driver_app": "Ứng Dụng Tài Xế",
        "admin_portal": "Cổng Quản Trị",
        "real_time_pricing": "Định Giá Động Thời Gian Thực",
        "location_based_pricing": "Định Giá Theo Vị Trí",
        "live_updates": "Cập Nhật WebSocket Trực Tiếp",
        "authentication": "Xác Thực",
        "machine_learning": "Định Giá Học Máy",
        "push_notifications": "Thông Báo Đẩy",
        "analytics": "Phân Tích Nâng Cao"
    },
    "es": {
        "welcome": "Bienvenido a Equilibrium",
        "get_price_estimate": "Obtener Estimación de Precio",
        "pickup_location": "Ubicación de Recogida",
        "dropoff_location": "Ubicación de Destino",
        "driver_status": "Estado del Conductor",
        "online": "En Línea",
        "offline": "Desconectado",
        "demand_heatmap": "Mapa de Calor de Demanda",
        "login": "Iniciar Sesión",
        "logout": "Cerrar Sesión",
        "mobile_app": "Aplicación Móvil",
        "driver_app": "Aplicación del Conductor",
        "admin_portal": "Portal de Administración",
        "real_time_pricing": "Precios Dinámicos en Tiempo Real",
        "location_based_pricing": "Precios Basados en Ubicación",
        "live_updates": "Actualizaciones WebSocket en Vivo",
        "authentication": "Autenticación",
        "machine_learning": "Precios de Aprendizaje Automático",
        "push_notifications": "Notificaciones Push",
        "analytics": "Análisis Avanzados"
    },
    "fr": {
        "welcome": "Bienvenue chez Equilibrium",
        "get_price_estimate": "Obtenir une Estimation de Prix",
        "pickup_location": "Lieu de Prise en Charge",
        "dropoff_location": "Lieu de Destination",
        "driver_status": "Statut du Conducteur",
        "online": "En Ligne",
        "offline": "Hors Ligne",
        "demand_heatmap": "Carte de Chaleur de la Demande",
        "login": "Se Connecter",
        "logout": "Se Déconnecter",
        "mobile_app": "Application Mobile",
        "driver_app": "Application Conducteur",
        "admin_portal": "Portail d'Administration",
        "real_time_pricing": "Tarification Dynamique en Temps Réel",
        "location_based_pricing": "Tarification Basée sur la Localisation",
        "live_updates": "Mises à Jour WebSocket en Direct",
        "authentication": "Authentification",
        "machine_learning": "Tarification par Apprentissage Automatique",
        "push_notifications": "Notifications Push",
        "analytics": "Analyses Avancées"
    },
    "de": {
        "welcome": "Willkommen bei Equilibrium",
        "get_price_estimate": "Preisschätzung Abrufen",
        "pickup_location": "Abholort",
        "dropoff_location": "Zielort",
        "driver_status": "Fahrerstatus",
        "online": "Online",
        "offline": "Offline",
        "demand_heatmap": "Nachfrage-Heatmap",
        "login": "Anmelden",
        "logout": "Abmelden",
        "mobile_app": "Mobile App",
        "driver_app": "Fahrer-App",
        "admin_portal": "Admin-Portal",
        "real_time_pricing": "Echtzeit-Dynamische Preisgestaltung",
        "location_based_pricing": "Standortbasierte Preisgestaltung",
        "live_updates": "Live WebSocket-Updates",
        "authentication": "Authentifizierung",
        "machine_learning": "Machine Learning Preisgestaltung",
        "push_notifications": "Push-Benachrichtigungen",
        "analytics": "Erweiterte Analysen"
    },
    "zh": {
        "welcome": "欢迎使用 Equilibrium",
        "get_price_estimate": "获取价格估算",
        "pickup_location": "上车地点",
        "dropoff_location": "下车地点",
        "driver_status": "司机状态",
        "online": "在线",
        "offline": "离线",
        "demand_heatmap": "需求热力图",
        "login": "登录",
        "logout": "登出",
        "mobile_app": "移动应用",
        "driver_app": "司机应用",
        "admin_portal": "管理门户",
        "real_time_pricing": "实时动态定价",
        "location_based_pricing": "基于位置的定价",
        "live_updates": "实时 WebSocket 更新",
        "authentication": "身份验证",
        "machine_learning": "机器学习定价",
        "push_notifications": "推送通知",
        "analytics": "高级分析"
    },
    "ja": {
        "welcome": "Equilibrium へようこそ",
        "get_price_estimate": "料金見積もりを取得",
        "pickup_location": "乗車場所",
        "dropoff_location": "降車場所",
        "driver_status": "ドライバー状態",
        "online": "オンライン",
        "offline": "オフライン",
        "demand_heatmap": "需要ヒートマップ",
        "login": "ログイン",
        "logout": "ログアウト",
        "mobile_app": "モバイルアプリ",
        "driver_app": "ドライバーアプリ",
        "admin_portal": "管理ポータル",
        "real_time_pricing": "リアルタイム動的価格設定",
        "location_based_pricing": "位置ベース価格設定",
        "live_updates": "ライブ WebSocket 更新",
        "authentication": "認証",
        "machine_learning": "機械学習価格設定",
        "push_notifications": "プッシュ通知",
        "analytics": "高度な分析"
    }
}

# Supported languages
supported_languages = {
    "en": {"name": "English", "rtl": False},
    "vi": {"name": "Tiếng Việt", "rtl": False},
    "es": {"name": "Español", "rtl": False},
    "fr": {"name": "Français", "rtl": False},
    "de": {"name": "Deutsch", "rtl": False},
    "zh": {"name": "中文", "rtl": False},
    "ja": {"name": "日本語", "rtl": False}
}

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "i18n-service",
        "version": "1.0.0",
        "supported_languages": len(supported_languages),
        "total_translations": sum(len(translations) for translations in translations_db.values())
    }

@app.get("/api/v1/i18n/languages")
async def get_supported_languages():
    """Get list of supported languages"""
    languages = []
    for code, info in supported_languages.items():
        languages.append({
            "language_code": code,
            "language_name": info["name"],
            "is_rtl": info["rtl"],
            "is_supported": True
        })
    
    return {
        "languages": languages,
        "total": len(languages)
    }

@app.get("/api/v1/i18n/translations/{language_code}")
async def get_translations(language_code: str):
    """Get all translations for a language"""
    if language_code not in translations_db:
        raise HTTPException(
            status_code=404,
            detail=f"Language {language_code} not supported"
        )
    
    return {
        "language_code": language_code,
        "language_name": supported_languages[language_code]["name"],
        "translations": translations_db[language_code],
        "total_keys": len(translations_db[language_code])
    }

@app.get("/api/v1/i18n/translate/{language_code}/{key}")
async def get_translation(language_code: str, key: str):
    """Get specific translation"""
    if language_code not in translations_db:
        raise HTTPException(
            status_code=404,
            detail=f"Language {language_code} not supported"
        )
    
    if key not in translations_db[language_code]:
        # Fallback to English if key not found
        if language_code != "en" and key in translations_db["en"]:
            return {
                "key": key,
                "translation": translations_db["en"][key],
                "language_code": language_code,
                "is_fallback": True
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Translation key '{key}' not found"
            )
    
    return {
        "key": key,
        "translation": translations_db[language_code][key],
        "language_code": language_code,
        "is_fallback": False
    }

@app.post("/api/v1/i18n/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """Translate text (simplified translation)"""
    if request.target_language not in supported_languages:
        raise HTTPException(
            status_code=400,
            detail=f"Target language {request.target_language} not supported"
        )
    
    # Simple translation logic (in production, use proper translation service)
    if request.text in translations_db.get(request.source_language, {}):
        source_key = request.text
        if source_key in translations_db.get(request.target_language, {}):
            translated_text = translations_db[request.target_language][source_key]
            confidence = 0.95
        else:
            # Fallback to English
            if source_key in translations_db.get("en", {}):
                translated_text = translations_db["en"][source_key]
                confidence = 0.7
            else:
                translated_text = request.text  # No translation available
                confidence = 0.1
    else:
        # Direct translation attempt (simplified)
        translated_text = request.text
        confidence = 0.3
    
    return TranslationResponse(
        original_text=request.text,
        translated_text=translated_text,
        source_language=request.source_language,
        target_language=request.target_language,
        confidence=confidence
    )

@app.get("/api/v1/i18n/keys")
async def get_all_translation_keys():
    """Get all available translation keys"""
    all_keys = set()
    for translations in translations_db.values():
        all_keys.update(translations.keys())
    
    return {
        "translation_keys": sorted(list(all_keys)),
        "total_keys": len(all_keys)
    }

@app.post("/api/v1/i18n/add-translation")
async def add_translation(
    language_code: str,
    key: str,
    translation: str
):
    """Add new translation"""
    if language_code not in supported_languages:
        raise HTTPException(
            status_code=400,
            detail=f"Language {language_code} not supported"
        )
    
    if language_code not in translations_db:
        translations_db[language_code] = {}
    
    translations_db[language_code][key] = translation
    
    return {
        "status": "success",
        "message": f"Translation added for {language_code}:{key}",
        "translation": translation
    }

@app.get("/api/v1/i18n/stats")
async def get_translation_stats():
    """Get translation statistics"""
    stats = {}
    for lang_code, translations in translations_db.items():
        stats[lang_code] = {
            "language_name": supported_languages[lang_code]["name"],
            "total_translations": len(translations),
            "coverage_percentage": round(len(translations) / len(translations_db["en"]) * 100, 2)
        }
    
    return {
        "statistics": stats,
        "total_languages": len(translations_db),
        "total_keys": len(translations_db["en"]) if "en" in translations_db else 0
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8009)
