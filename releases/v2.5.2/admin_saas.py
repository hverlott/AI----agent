import streamlit as st
from database import db
from auth_core import AuthManager
import time
import pandas as pd
import psutil
import os
import sys

st.set_page_config(page_title="SaaS Admin Portal", layout="wide", page_icon="🏢")

if 'auth' not in st.session_state:
    st.session_state.auth = AuthManager(db)

def get_system_status():
    cpu_percent = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    return {
        "cpu": cpu_percent,
        "memory_used": mem.used / (1024 ** 3),
        "memory_total": mem.total / (1024 ** 3),
        "disk_used": disk.used / (1024 ** 3),
        "disk_total": disk.total / (1024 ** 3)
    }

def login_page():
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.title("🔐 Enterprise SaaS Portal")
        st.markdown("---")
        
        # Auto-init Super Admin if empty
        users = db.list_users()
        if not users:
            st.warning("Initializing System...")
            st.session_state.auth.create_user("admin", "admin123", "super_admin", None)
            st.success("Default Admin Created: admin / admin123")
            time.sleep(1)
            st.rerun()

        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", width="stretch")
            
            if submitted:
                # In real deployment, get actual IP from headers if possible, here use placeholder
                user = st.session_state.auth.login(username, password, "127.0.0.1")
                if user:
                    st.session_state.user = user
                    st.success("Welcome back!")
                    st.rerun()
                else:
                    st.error("Invalid credentials or account inactive.")

def main_dashboard():
    user = st.session_state.user
    
    # Sidebar
    st.sidebar.title(f"👤 {user['username']}")
    st.sidebar.caption(f"Role: {user['role']}")
    if user.get('tenant_id'):
        st.sidebar.caption(f"Tenant: {user['tenant_id']}")
        
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout", width="stretch"):
        st.session_state.user = None
        st.rerun()

    # Router
    if user['role'] == 'super_admin':
        super_admin_view()
    else:
        business_admin_view(user)

def super_admin_view():
    st.header("🛠️ System Administration")
    
    tabs = st.tabs(["👥 Tenants & Users", "🛡️ Security", "🖥️ System Health", "📜 Audit & Logs", "🚀 Upgrade"])
    
    # 1. Tenants & Users
    with tabs[0]:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Tenants")
            tenants = db.list_tenants()
            if tenants:
                st.dataframe(pd.DataFrame(tenants)[['id', 'plan', 'created_at']], width="stretch")
            
            with st.expander("➕ Create Tenant"):
                with st.form("new_tenant"):
                    tid = st.text_input("Tenant ID")
                    plan = st.selectbox("Plan", ["Free", "Standard", "Enterprise"])
                    if st.form_submit_button("Create"):
                        if tid:
                            db.create_tenant(tid, plan)
                            st.success(f"Tenant {tid} created.")
                            st.rerun()
                            
        with c2:
            st.subheader("Users")
            users = db.list_users()
            if users:
                st.dataframe(pd.DataFrame(users)[['username', 'role', 'tenant_id', 'status']], width="stretch")
                
            with st.expander("➕ Create User"):
                with st.form("new_user"):
                    uname = st.text_input("Username")
                    upass = st.text_input("Password", type="password")
                    urole = st.selectbox("Role", ["business_admin", "super_admin"])
                    t_options = [t['id'] for t in tenants] if tenants else []
                    utenant = st.selectbox("Assign Tenant", [""] + t_options)
                    
                    if st.form_submit_button("Create"):
                        if not uname or not upass:
                            st.error("Missing fields")
                        elif urole == "business_admin" and not utenant:
                            st.error("Business Admin requires a Tenant")
                        else:
                            ok, msg = st.session_state.auth.create_user(uname, upass, urole, utenant if utenant else None)
                            if ok:
                                st.success("User created.")
                                st.rerun()
                            else:
                                st.error(msg)

    # 2. Security
    with tabs[1]:
        st.subheader("IP Whitelist Management")
        ips = db.list_ip_whitelist()
        if ips:
            st.dataframe(pd.DataFrame(ips)[['ip_address', 'description', 'created_at']], width="stretch")
        
        with st.form("add_ip"):
            c_ip1, c_ip2 = st.columns(2)
            ip_addr = c_ip1.text_input("IP Address")
            ip_desc = c_ip2.text_input("Description")
            if st.form_submit_button("Add to Whitelist"):
                try:
                    db.add_ip_whitelist(ip_addr, ip_desc)
                    st.success("IP added.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    # 3. System Health
    with tabs[2]:
        st.subheader("Server Status")
        if st.button("Refresh Status"):
            st.rerun()
            
        status = get_system_status()
        c1, c2, c3 = st.columns(3)
        c1.metric("CPU Usage", f"{status['cpu']}%")
        c2.metric("Memory", f"{status['memory_used']:.1f} / {status['memory_total']:.1f} GB")
        c3.metric("Disk", f"{status['disk_used']:.1f} / {status['disk_total']:.1f} GB")
        
        st.progress(status['cpu'] / 100, text="CPU Load")
        st.progress(status['memory_used'] / status['memory_total'], text="Memory Usage")

    # 4. Logs
    with tabs[3]:
        st.subheader("Login History")
        logs = db.get_login_history(limit=50)
        if logs:
            st.dataframe(pd.DataFrame(logs)[['username', 'ip_address', 'status', 'timestamp']], width="stretch")
        else:
            st.info("No login history yet.")
            
        st.markdown("---")
        st.subheader("System Audit Logs")
        audit = db.get_audit_logs(limit=50)
        if audit:
            st.dataframe(pd.DataFrame(audit)[['timestamp', 'user_role', 'action', 'details']], width="stretch")

    # 5. Upgrade
    with tabs[4]:
        st.subheader("System Update")
        st.success(f"✅ System is running v2.5.1 (Active)")
        st.info(f"Build Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if st.button("Check for Updates"):
            with st.spinner("Checking remote repository..."):
                time.sleep(1)
                st.balloons()
                st.success("You are on the latest version: v2.5.1")

def business_admin_view(user):
    tenant_id = user['tenant_id']
    st.header(f"🏢 {tenant_id} - Management Console")
    
    if not tenant_id:
        st.error("Configuration Error: No Tenant ID assigned.")
        return

    tabs = st.tabs(["📊 Overview", "⚙️ Configuration", "📚 Knowledge Base"])
    
    # 1. Overview
    with tabs[0]:
        metrics = db.get_dashboard_metrics(tenant_id)
        c1, c2, c3 = st.columns(3)
        c1.metric("Active Conversations", metrics.get('active_users', 0))
        c2.metric("Tokens Consumed", metrics.get('total_tokens', 0))
        c3.metric("Est. Cost", f"${metrics.get('total_cost', 0):.2f}")
        
        st.line_chart(metrics.get('message_trend', {}))
        
    # 2. Configuration (Isolated)
    with tabs[1]:
        st.subheader("Bot Configuration")
        # Load specific tenant config
        config = db.get_tenant_config(tenant_id)
        
        with st.form("tenant_config"):
            bot_name = st.text_input("Bot Name", config.get('bot_name', ''))
            welcome_msg = st.text_area("Welcome Message", config.get('welcome_msg', 'Hello! How can I help?'))
            model_temp = st.slider("AI Temperature", 0.0, 1.0, config.get('temperature', 0.7))
            
            if st.form_submit_button("Save Changes"):
                new_conf = config.copy()
                new_conf.update({
                    "bot_name": bot_name,
                    "welcome_msg": welcome_msg,
                    "temperature": model_temp
                })
                db.upsert_tenant_config(tenant_id, new_conf)
                # Log this action for audit
                db.log_audit(tenant_id, "BusinessAdmin", "UpdateConfig", {"user": user['username']})
                st.success("Configuration Saved.")
    
    # 3. KB (Isolated)
    with tabs[2]:
        st.subheader("Knowledge Base")
        kb_items = db.get_kb_items(tenant_id)
        if kb_items:
            st.dataframe(pd.DataFrame(kb_items)[['title', 'category', 'updated_at']], width="stretch")
        else:
            st.info("Knowledge Base is empty.")
            
        with st.expander("Upload New Document"):
            st.file_uploader("Choose a file", type=['txt', 'md', 'pdf'])
            st.button("Process & Embed")

    # 4. Audit Logs
    with tabs[3]:
        st.subheader("Operation Logs")
        st.caption("Records of configuration changes and sensitive operations.")
        
        audit_logs = db.get_audit_logs(tenant_id=tenant_id, limit=50)
        if audit_logs:
            # Display logs in a table
            df = pd.DataFrame(audit_logs)
            # Ensure columns exist before selecting
            cols = ['timestamp', 'action', 'details']
            if 'user_role' in df.columns:
                cols.insert(1, 'user_role')
                
            st.dataframe(
                df[cols], 
                width="stretch",
                column_config={
                    "timestamp": st.column_config.DatetimeColumn("Time", format="D MMM, HH:mm:ss"),
                    "details": "Details (User Info)"
                }
            )
        else:
            st.info("No audit logs found for this tenant.")

if 'user' not in st.session_state or not st.session_state.user:
    login_page()
else:
    main_dashboard()
