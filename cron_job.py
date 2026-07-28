import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from supabase import create_client, Client

# جلب المفاتيح من متغيرات البيئة
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_email(to_email, title, due_date):
    subject = f"🚨 تنبيه: العقد '{title}' يستحق القرب من الانتهاء"
    body = f"""
    مرحباً،
    
    نود تذكيرك بأن العقد/المهمة: ({title})
    تاريخ انتهاء الصلاحية المحدد هو: {due_date}
    
    يرجى اتخاذ الإجراء اللازم.
    """
    
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"تم إرسال إيميل إلى {to_email}")
    except Exception as e:
        print(f"فشل إرسال الإيميل: {e}")

def check_contracts():
    response = supabase.table("contracts").select("*").eq("status", 1).execute()
    contracts = response.data
    
    today = datetime.now().date()
    
    for c in contracts:
        due_date = datetime.strptime(c['due_date'], "%Y-%m-%d").date()
        # التنبيه إذا كان متبقي 3 أيام أو اليوم
        if 0 <= (due_date - today).days <= 3:
            send_email(c['employee_email'], c['title'], c['due_date'])

if __name__ == "__main__":
    check_contracts()
