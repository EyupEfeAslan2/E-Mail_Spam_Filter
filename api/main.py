from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from core.model import HybridSpamFilter
from core.adaptive import AdaptiveSystem
from core.config import settings
from core.rate_limit import SlidingWindowRateLimiter
from core.retrain import retrain_queue
from core.security import verify_admin_token
from api.schemas import BatchEmailRequest, EmailRequest, SensitivityRequest
import os

app = FastAPI(
    title="Adaptive E-mail Spam Filter API",
    description="Hibrit (Bloom Filter + DistilBERT) ve Adaptif Spam Filtresi"
)

# Servisler global olarak başlatılıyor
filter_system = HybridSpamFilter()
adaptive_system = AdaptiveSystem(filter_system=filter_system)
feedback_limiter = SlidingWindowRateLimiter(
    max_requests=settings.rate_limit_feedback,
    window_seconds=settings.rate_limit_window_seconds,
)
admin_limiter = SlidingWindowRateLimiter(
    max_requests=settings.rate_limit_admin,
    window_seconds=settings.rate_limit_window_seconds,
)

# UI dizinini tanımla
ui_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui")
# Static dosyaları sunmak için mount et
app.mount("/static", StaticFiles(directory=ui_dir), name="static")

def require_admin_token(token: str | None):
    """Data structure: Hash/token. Admin işlemleri sabit-zamanlı token kontrolüyle korunur."""
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Yönetici yetkisi gerekli.")


def client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def require_feedback_quota(request: Request):
    if not feedback_limiter.allow(client_key(request)):
        raise HTTPException(status_code=429, detail="Geri bildirim limiti aşıldı.")


def require_admin_quota(request: Request):
    if not admin_limiter.allow(client_key(request)):
        raise HTTPException(status_code=429, detail="Yönetici istek limiti aşıldı.")


@app.get("/")
def read_root():
    """Ana sayfaya (index.html) yönlendirir."""
    index_path = os.path.join(ui_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Adaptive E-mail Spam Filter API Çalışıyor! Ancak UI dosyası bulunamadı."}

@app.get("/health/live")
def live_health():
    """Process liveness check for orchestration systems."""
    return {"status": "ok"}

@app.get("/health/ready")
def ready_health():
    """Readiness requires a fine-tuned model and passing evaluation metrics."""
    health = filter_system.health()
    if not health["ready"]:
        raise HTTPException(status_code=503, detail=health)
    return health

@app.post("/predict")
def predict_email(request: EmailRequest):
    """Gelen e-postanın spam olup olmadığını tahmin eder."""
    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="E-posta metni boş olamaz.")
        
    result = filter_system.predict(request.text)
    return result

@app.post("/predict/batch")
def predict_batch(request: BatchEmailRequest):
    """Yüksek hacimli çağrılar için sıralı toplu tahmin döndürür."""
    if not request.emails:
        raise HTTPException(status_code=400, detail="E-posta listesi boş olamaz.")
    if len(request.emails) > 100:
        raise HTTPException(status_code=400, detail="Tek istekte en fazla 100 e-posta gönderilebilir.")
    return {"results": filter_system.batch_predict(request.emails)}

@app.post("/report/spam")
def report_spam(request: EmailRequest, raw_request: Request):
    """Gözden kaçan Spam (False Negative) e-postayı bildirir."""
    require_feedback_quota(raw_request)
    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="E-posta metni boş olamaz.")
        
    result = adaptive_system.report_spam(request.text)
    return result

@app.post("/report/ham")
def report_ham(request: EmailRequest, raw_request: Request):
    """Yanlışlıkla Spam klasörüne düşmüş (False Positive) e-postayı Ham olarak bildirir."""
    require_feedback_quota(raw_request)
    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="E-posta metni boş olamaz.")
        
    result = adaptive_system.report_ham(request.text)
    return result

@app.get("/admin/sensitivity")
def get_sensitivity(request: Request, x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    """Mevcut spam hassasiyet eşiğini (threshold) döndürür."""
    require_admin_quota(request)
    require_admin_token(x_admin_token)
    return {"threshold": filter_system.threshold}

@app.post("/admin/sensitivity")
def set_sensitivity(request: SensitivityRequest, raw_request: Request, x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    """Yöneticilerin spam hassasiyet eşiğini (threshold) ayarlamasını sağlar."""
    require_admin_quota(raw_request)
    require_admin_token(x_admin_token)
    try:
        filter_system.set_threshold(request.threshold)
        return {"status": "success", "message": f"Hassasiyet eşiği {request.threshold} olarak güncellendi."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/admin/health")
def admin_health(request: Request, x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    """Model, eşik ve veri yapısı durumunu yöneticiye gösterir."""
    require_admin_quota(request)
    require_admin_token(x_admin_token)
    health = filter_system.health()
    health["retrain"] = retrain_queue.read()
    return health

@app.post("/admin/retrain")
def request_retrain(
    request: Request,
    background_tasks: BackgroundTasks,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
):
    """Yöneticinin modeli feedback kuyruğuyla yeniden eğitmesini tetikler."""
    require_admin_quota(request)
    require_admin_token(x_admin_token)
    state = retrain_queue.enqueue(reason="manual_admin_request")
    background_tasks.add_task(retrain_queue.run_if_requested)
    return {"status": "queued", "retrain": state}
