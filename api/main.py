from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from core.model import HybridSpamFilter
from core.adaptive import AdaptiveSystem
from core.adaptive import AdaptiveSystem
from api.schemas import EmailRequest, SensitivityRequest
import os

app = FastAPI(
    title="Adaptive E-mail Spam Filter API",
    description="Hibrit (Bloom Filter + DistilBERT) ve Adaptif Spam Filtresi"
)

# Servisler global olarak başlatılıyor
filter_system = HybridSpamFilter()
adaptive_system = AdaptiveSystem(filter_system=filter_system)

# UI dizinini tanımla
ui_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui")
# Static dosyaları sunmak için mount et
app.mount("/static", StaticFiles(directory=ui_dir), name="static")

@app.get("/")
def read_root():
    """Ana sayfaya (index.html) yönlendirir."""
    index_path = os.path.join(ui_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Adaptive E-mail Spam Filter API Çalışıyor! Ancak UI dosyası bulunamadı."}

@app.post("/predict")
def predict_email(request: EmailRequest):
    """Gelen e-postanın spam olup olmadığını tahmin eder."""
    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="E-posta metni boş olamaz.")
        
    result = filter_system.predict(request.text)
    return result

@app.post("/report/spam")
def report_spam(request: EmailRequest):
    """Gözden kaçan Spam (False Negative) e-postayı bildirir."""
    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="E-posta metni boş olamaz.")
        
    result = adaptive_system.report_spam(request.text)
    return result

@app.post("/report/ham")
def report_ham(request: EmailRequest):
    """Yanlışlıkla Spam klasörüne düşmüş (False Positive) e-postayı Ham olarak bildirir."""
    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="E-posta metni boş olamaz.")
        
    result = adaptive_system.report_ham(request.text)
    return result

@app.get("/admin/sensitivity")
def get_sensitivity():
    """Mevcut spam hassasiyet eşiğini (threshold) döndürür."""
    return {"threshold": filter_system.threshold}

@app.post("/admin/sensitivity")
def set_sensitivity(request: SensitivityRequest):
    """Yöneticilerin spam hassasiyet eşiğini (threshold) ayarlamasını sağlar."""
    try:
        filter_system.set_threshold(request.threshold)
        return {"status": "success", "message": f"Hassasiyet eşiği {request.threshold} olarak güncellendi."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
