import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pandas as pd

# 1. الاتصال بـ Supabase من Secrets
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="نظام إدارة التنبيهات والعقود", layout="wide")

# 2. إدارة جلسة المستخدم
if "user" not in st.session_state:
    st.session_state.user = None

def login_page():
    st.title("🔐 نظام التذكير الذكي - تسجيل الدخول")
    
    tab1, tab2 = st.tabs(["تسجيل الدخول", "إنشاء حساب جديد"])
    
    with tab1:
        email = st.text_input("البريد الإلكتروني", key="login_email")
        password = st.text_input("كلمة السر", type="password", key="login_pass")
        if st.button("دخول"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.success("تم تسجيل الدخول بنجاح!")
                st.rerun()
            except Exception as e:
                st.error(f"خطأ في البيانات: {str(e)}")

    with tab2:
        new_email = st.text_input("البريد الإلكتروني", key="reg_email")
        new_pass = st.text_input("كلمة السر", type="password", key="reg_pass")
        if st.button("إنشاء حساب"):
            try:
                res = supabase.auth.sign_up({"email": new_email, "password": new_pass})
                st.success("تم إنشاء الحساب بنجاح! يمكنكِ الآن تسجيل الدخول.")
            except Exception as e:
                st.error(f"فشل إنشاء الحساب: {str(e)}")

# إذا لم يكن تسجيل الدخول مكتملًا
if not st.session_state.user:
    login_page()
else:
    # الشريط الجانبي لتسجيل الخروج
    user_email = st.session_state.user.email
    user_id = st.session_state.user.id
    st.sidebar.write(f"👤 مرحباً بك: **{user_email}**")
    if st.sidebar.button("تسجيل الخروج"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

    st.title("📋 إدارة العقود الخاصة بك")

    tab_view, tab_add = st.tabs(["📑 عقودي", "➕ إضافة عقد جديد"])

    # إضافة عقد جديد مرتبط بالمستخدم الحالي
    with tab_add:
        st.subheader("إضافة عقد جديد لحسابك")
        with st.form("add_contract_form"):
            title = st.text_input("عنوان العقد / المهمة")
            due_date = st.date_input("تاريخ الانتهاء")
            emp_email = st.text_input("بريد الموظف المسؤول للتنبيهات")
            priority = st.selectbox("الأهمية", ["منخفضة", "متوسطة", "عالية"])
            submit = st.form_submit_button("حفظ العقد")

            if submit:
                if title and emp_email:
                    data = {
                        "user_id": user_id,
                        "title": title,
                        "due_date": str(due_date),
                        "employee_email": emp_email,
                        "priority": priority,
                        "status": 1
                    }
                    supabase.table("contracts").insert(data).execute()
                    st.success("تمت إضافة العقد بنجاح إلى حسابك!")
                else:
                    st.warning("يرجى تعبئة كافة الحقول المطلوبة.")

    # عرض العقود الخاصة بالمستخدم الحالي فقط
    with tab_view:
        st.subheader("قائمة عقودك المسجلة")
        response = supabase.table("contracts").select("*").eq("user_id", user_id).execute()
        contracts = response.data

        if contracts:
            df = pd.DataFrame(contracts)
            st.dataframe(df[['title', 'due_date', 'employee_email', 'priority']], use_container_width=True)
        else:
            st.info("لا توجد عقود مسجلة في حسابك حالياً.")
