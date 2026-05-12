"""
WhatsApp Router - Twilio Webhook Handler
Müşteriden gelen WhatsApp mesajlarını alır, Gemini AI ile cevap üretir,
ChromaDB'den veri çeker ve Twilio üzerinden WhatsApp'a yanıt gönderir.
"""

import os
import logging
from fastapi import APIRouter, Request, Form
from fastapi.responses import PlainTextResponse
from twilio.rest import Client as TwilioClient
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai
from shared_utils import get_context

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Twilio ayarları ──────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

# ── Gemini ayarları ──────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# ── Sistem prompt'u ──────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
Sen KOBİ'lere yardımcı olan bir yapay zeka iş asistanısın.
Müşteri mesajlarını Türkçe olarak anlayıp kısa, net ve samimi cevaplar verirsin.

Görevin:
- Sipariş durumu soruları → veritabanından bak, bilgi ver
- Stok soruları → mevcut stok bilgisini aktar
- Genel sorular → nazikçe yardımcı ol

Kurallar:
- Cevapların maksimum 3-4 cümle olsun
- Resmi ama samimi bir dil kullan
- Bilmediğin bir şeyi uydurma, "Bu konuda size yardımcı olamıyorum" de
- Türkçe yaz

Aşağıdaki veritabanı bağlamını kullanarak cevap ver:
{context}
"""


def build_ai_response(user_message: str) -> str:
    """
    Kullanıcı mesajına göre ChromaDB'den bağlam çeker,
    Gemini AI ile akıllı bir cevap üretir.
    """
    try:
        # 1) ChromaDB'den ilgili verileri çek
        context_data = get_context(user_message, n_results=5)

        if context_data["success"] and context_data["documents"]:
            context_text = "\n".join([
                f"- {doc} | Metadata: {meta}"
                for doc, meta in zip(context_data["documents"], context_data["metadatas"])
            ])
        else:
            context_text = "Veritabanında ilgili kayıt bulunamadı."

        # 2) Gemini'ye prompt gönder
        prompt = SYSTEM_PROMPT.format(context=context_text)
        full_prompt = f"{prompt}\n\nMüşteri mesajı: {user_message}"

        response = gemini_model.generate_content(full_prompt)
        return response.text.strip()

    except Exception as e:
        logger.error(f"AI response generation failed: {e}")
        return "Şu an teknik bir sorun yaşıyoruz. Lütfen daha sonra tekrar deneyin."


@router.post("/webhook", response_class=PlainTextResponse)
async def whatsapp_webhook(
    Body: str = Form(...),
    From: str = Form(...),
):
    """
    Twilio'nun WhatsApp webhook'u buraya POST gönderir.
    Gelen mesajı işler ve TwiML formatında cevap döner.
    """
    logger.info(f"📱 WhatsApp mesajı alındı | Gönderen: {From} | Mesaj: {Body}")

    # AI'dan cevap al
    ai_reply = build_ai_response(Body)
    logger.info(f"🤖 AI cevabı: {ai_reply}")

    # TwiML formatında cevap oluştur (Twilio bunu WhatsApp'a iletir)
    twiml = MessagingResponse()
    twiml.message(ai_reply)

    return PlainTextResponse(str(twiml), media_type="application/xml")


@router.post("/send")
async def send_whatsapp_message(to: str, message: str):
    """
    Manuel WhatsApp mesajı gönderme endpoint'i (test/admin için).
    Örnek: POST /api/whatsapp/send?to=+905XXXXXXXXX&message=Merhaba
    """
    try:
        twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        msg = twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            to=f"whatsapp:{to}",
            body=message
        )
        logger.info(f"✅ Mesaj gönderildi: {msg.sid}")
        return {"success": True, "message_sid": msg.sid}

    except Exception as e:
        logger.error(f"Mesaj gönderilemedi: {e}")
        return {"success": False, "error": str(e)}
