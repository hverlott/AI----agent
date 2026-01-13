import asyncio
import uuid
import random
import json
import httpx
import os
from openai import AsyncOpenAI, APIConnectionError
from telethon import events
from src.modules.telegram.utils import record_group, load_selected_group_ids, get_chat_history, get_prev_incoming_message
from src.utils.text import normalize_text, calculate_similarity
from src.modules.audit.manager import AuditManager
from src.modules.orchestrator.state_manager import ConversationStateManager
from src.modules.orchestrator.supervisor import SupervisorAgent
from src.modules.orchestrator.runtime import StageAgentRuntime
from src.core.ai import create_client_from_config

def register_handlers(app):
    @app.client.on(events.NewMessage(incoming=True))
    async def handler(event):
        if not event.message.text:
            return

        trace_id = str(uuid.uuid4())
        msg = event.message.text
        sender = await event.get_sender()
        user_id = str(event.chat_id)
        name = getattr(sender, 'first_name', '朋友')
        last_name = getattr(sender, 'last_name', '') or ''
        username = getattr(sender, 'username', '') or ''
        display_name = " ".join([p for p in [name, last_name, username] if p]).strip()

        # Update stats
        app.stats['total_messages'] += 1
        if event.is_private:
            app.stats['private_messages'] += 1
        elif event.is_group:
            app.stats['group_messages'] += 1
        app.save_stats()

        # Load config
        config = app.cfg.load_config()
        # Optimize: Use cached keywords from app initialization
        keywords = getattr(app, 'keywords', [])
        if not keywords:
             # Fallback if not initialized or empty (reload to be safe or just empty)
             keywords = app.cfg.load_keywords()
             
        orch_enabled = bool(config.get('CONV_ORCHESTRATION', False))

        if orch_enabled:
            app.logger.log_trace_event(trace_id, "MSG_RECEIVED", {
                "user_id": user_id, "content_len": len(msg), "platform": "telegram"
            })

        # --- Check Switches ---
        if event.is_private and not config['PRIVATE_REPLY']:
            app.logger.log_private(f"[trace:{trace_id}] 🔕 私聊回复已关闭，忽略消息 [{name}]: {msg}")
            return

        if event.is_group:
            await record_group(event, app.cfg, app.logger)
            selected_ids = load_selected_group_ids(app.cfg)
            chat_id = getattr(event, 'chat_id', None)
            
            # Sender Name Filter (Legacy Config Support)
            if bool(config.get('SENDER_FILTER_ENABLED', False)):
                raw = str(config.get('SENDER_NAME_FILTER_KEYWORDS', '') or '')
                name_keys = [k.strip() for k in raw.split(',') if k.strip()]
                if name_keys and any(k.lower() in display_name.lower() for k in name_keys):
                    app.logger.log_group(f"🛡️ 昵称过滤命中（{display_name}），跳过回复：{msg}")
                    return

            # Passive Recording
            if selected_ids and chat_id and int(chat_id) in selected_ids:
                try:
                    app.db.record_message_event(app.tenant_id, "telegram", str(chat_id), "inbound", "observed", user_content=msg, bot_response="")
                except Exception as e:
                    app.logger.log_system(f"⚠️ Passive record failed: {e}")

            if not config['GROUP_REPLY']:
                app.logger.log_group(f"🔕 群聊回复已关闭，忽略消息 [{name}]: {msg}")
                return

            # Requirement 2: Non-whitelist groups should keep existing keyword trigger mechanism.
            # So we do NOT return here if not in whitelist.
            # if selected_ids:
            #    if chat_id is None or int(chat_id) not in selected_ids:
            #        app.logger.log_group(f"🛑 群聊 [{chat_id}] 不在白名单，跳过回复")
            #        return

        # --- Should Reply? ---
        should_reply = False
        if event.is_private:
            should_reply = True
            app.logger.log_private(f"[trace:{trace_id}] 📩 收到私聊 [{name}]: {msg}")
        elif event.is_group:
            # Check whitelist status
            is_whitelisted = False
            if chat_id and selected_ids and int(chat_id) in selected_ids:
                is_whitelisted = True
                app.logger.log_group(f"WHITELIST_CHECK pass chat_id={chat_id}")
            else:
                app.logger.log_group(f"WHITELIST_CHECK fail chat_id={chat_id} selected_count={len(selected_ids)}")

            if is_whitelisted:
                should_reply = True
                app.logger.log_group(f"✅ 白名单群组自动触发 [{name}]: {msg}")
            elif event.mentioned:
                should_reply = True
                app.logger.log_group(f"📩 群聊被 @ [{name}]: {msg}")
            elif keywords:
                for kw in keywords:
                    if kw.lower() in msg.lower():
                        should_reply = True
                        app.logger.log_group(f"📩 群聊触发关键词 [{kw}] [{name}]: {msg}")
                        break
            elif config.get('GROUP_CONTEXT', False):
                should_reply = True
                app.logger.log_group(f"📩 群聊上下文触发 [{name}]: {msg}")

        # Check if Orchestrator is enabled but stage is invalid
        # This handles the case where CONV_ORCHESTRATION=on but no binding/model is configured
        # causing silence.
        
        if not should_reply:
            return

        # --- Handoff Logic ---
        def _handoff_intent_detect(user_msg):
            if not user_msg: return False
            s = (user_msg or "").strip().lower()
            keys_raw = str(config.get('HANDOFF_KEYWORDS', '') or '')
            keys = [k.strip().lower() for k in keys_raw.split(',') if k.strip()]
            if keys and any(k in s for k in keys):
                return True
            return False

        if _handoff_intent_detect(msg):
            reply = (config.get('HANDOFF_MESSAGE') or "").strip()
            if not reply:
                app.logger.log_system("⚠️ HANDOFF_MESSAGE 未配置")
                return
            await _send_reply(app, event, reply, config, delay=True)
            app.logger.log_system(f"HANDOFF_REPLY: {reply}")
            # Record Handoff
            app.db.record_message_event(app.tenant_id, "telegram", str(event.chat_id), "outbound", "sent", model="handoff", stage="handoff", user_content=msg, bot_response=reply)
            return

        async with app.client.action(event.chat_id, 'typing'):
            system_prompt = app.cfg.load_system_prompt()
            history = await get_chat_history(app.client, event.chat_id, max_id=event.id)
            
            # QA Match
            qa_file = app.cfg.get_platform_path('qa.txt')
            qa_pairs = app.kb_engine.load_qa_pairs(qa_file)
            qa_reply = app.kb_engine.match_qa_reply(msg, qa_pairs)
            
            if qa_reply:
                app.logger.log_trace_event(trace_id, "QA_HIT", {"reply_len": len(qa_reply)})
                await event.reply(qa_reply)
                app.logger.log_system(f"QA_REPLY: {qa_reply}")
                app.db.record_message_event(app.tenant_id, "telegram", str(event.chat_id), "outbound", "sent", model="qa_match", stage="qa", user_content=msg, bot_response=qa_reply)
                return

            # KB Context
            kb_items = app.kb_loader.load_kb_entries()
            kb_context = ""
            system_with_kb = system_prompt

            # KB Only Logic
            if config.get('KB_ONLY_REPLY', False):
                kb_hits = app.kb_engine.retrieve_kb_context(msg, kb_items, topn=3)
                reply = ""
                if kb_hits:
                    context_text = "\n\n".join([f"--- Doc {i+1} ---\n{it.get('content','')}" for i, it in enumerate(kb_hits)])
                    conv_mode = str(config.get('CONVERSATION_MODE', 'ai_visible') or 'ai_visible').lower()
                    if conv_mode == 'human_simulated':
                        sys_prompt = (
                            "你是一个专业但语气自然的智能助手，负责基于知识库内容回答用户问题。\n"
                            "要求：\n"
                            "1. 语气可以亲切、口语化，但仍要保证信息准确。\n"
                            "2. 可以适度拟人表达，但注意不要夸张或虚构事实。\n"
                            "3. 如果知识库中没有相关信息，请直接回复: NO_ANSWER_FOUND\n"
                            "\n"
                            f"【参考资料】\n{context_text}"
                        )
                    else:
                        sys_prompt = (
                            "你是企业官方的技术支持客服助手，请根据以下知识库内容准确回答用户的问题。\n"
                            "要求：\n"
                            "1. 使用专业、说明型表达，语气正式、克制。\n"
                            "2. 仅围绕当前问题给出结论和必要说明，禁止扩展额外场景或泛泛建议。\n"
                            "3. 避免使用“我查了一下”“如果您需要了解更多”“我可以再给您详细说明”等口语化引导语。\n"
                            "4. 尽量控制在200字以内，禁止重复或无关铺垫。\n"
                            "5. 如果知识库中没有相关信息，请直接回复: NO_ANSWER_FOUND\n"
                            "\n"
                            f"【参考资料】\n{context_text}"
                        )
                    
                    try:
                        ai = app.ai_manager.get_client()
                        resp = await ai.chat.completions.create(
                            model=app.ai_model_name,
                            messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": msg}],
                            temperature=0.3
                        )
                        ans = resp.choices[0].message.content.strip()
                        if "NO_ANSWER_FOUND" not in ans:
                            reply = ans
                    except Exception as e:
                        app.logger.log_system(f"⚠️ KB_ONLY LLM Error: {e}")

                if not reply:
                    reply = (config.get('KB_FALLBACK_MESSAGE') or "").strip()
                    if not reply: return

                await _send_reply(app, event, reply, config, delay=True)
                app.db.record_message_event(app.tenant_id, "telegram", str(event.chat_id), "outbound", "sent", model="kb_only", stage="kb_only", user_content=msg, bot_response=reply)
                return

            # Orchestrator Logic
            decision = {}
            state = {}
            model_override = app.ai_model_name
            temp_override = config.get('AI_TEMPERATURE', 0.7)
            current_client = app.ai_manager.get_client()

            if orch_enabled:
                try:
                    mgr = ConversationStateManager(app.tenant_id)
                    state = mgr.get_state("tg", str(event.chat_id))
                    
                    # Supervisor Client Setup
                    sup_model_id = config.get("MODEL_SUPERVISOR")
                    sup_client = current_client
                    sup_model_name = app.ai_model_name
                    
                    if sup_model_id and sup_model_id != "default":
                         sup_conf = app.cfg.get_model_config(sup_model_id)
                         if sup_conf:
                             sup_client = create_client_from_config(sup_conf)
                             sup_model_name = sup_conf.get("model") or sup_model_id
                    
                    sup = SupervisorAgent(app.tenant_id, config)
                    decision = await sup.decide(state, history, sup_client, sup_model_name)
                    
                    # Update State
                    state["current_stage"] = decision.get("next_stage", state.get("current_stage"))
                    state["persona_id"] = decision.get("persona_id", state.get("persona_id"))
                    state["handoff_required"] = bool(decision.get("need_human", False))
                    mgr.update_state("tg", str(event.chat_id), state)

                    if state["handoff_required"]:
                        handoff_msg = "转接人工中..." # Simplify
                        await event.reply(handoff_msg)
                        return

                    # Stage Agent
                    current_stage = state.get("current_stage", "S0")
                    filtered_kb = [it for it in kb_items if not it.get("tags") or "all" in it.get("tags") or current_stage in it.get("tags")]
                    kb_hits = app.kb_engine.retrieve_kb_context(msg, filtered_kb, topn=2)
                    
                    stager = StageAgentRuntime(app.tenant_id)
                    rdec = stager.route_decision(state, history, filtered_kb)
                    
                    # Override Client for Orchestrator
                    worker_model_id = config.get("MODEL_WORKER")
                    worker_model_default = app.ai_model_name
                    
                    if worker_model_id and worker_model_id != "default":
                        w_conf = app.cfg.get_model_config(worker_model_id)
                        if w_conf:
                            worker_model_default = w_conf.get("model") or worker_model_id
                            # Set default client to configured worker model
                            current_client = create_client_from_config(w_conf) or current_client

                    if rdec.get("base_url"):
                        http_client2 = httpx.AsyncClient(verify=app.ai_manager._ssl_verify_default(), timeout=30.0)
                        current_client = AsyncOpenAI(api_key=app.ai_manager.api_key, base_url=rdec.get("base_url"), http_client=http_client2)
                    
                    model_override = rdec.get("model") or worker_model_default
                    temp_override = float(rdec.get("temperature") or temp_override)
                    
                    system_with_kb = stager.build_system_prompt(state, system_prompt, kb_hits)
                    
                except Exception as e:
                    app.logger.log_system(f"⚠️ Orchestration failed: {e}")

            # Fallback KB Logic
            if not orch_enabled and not kb_context:
                kb_hits = app.kb_engine.retrieve_kb_context(msg, kb_items, topn=2)
                if kb_hits:
                    parts = [f"[{it.get('title')}]\n{it.get('content')[:800]}" for it in kb_hits]
                    kb_context = "\n\n".join(parts)
                    system_with_kb = system_prompt + "\n\n【知识库参考】\n" + kb_context

            # Generate Response
            messages = [{"role": "system", "content": system_with_kb}] + history + [{"role": "user", "content": msg}]
            
            try:
                # Mock load_config wrapper for AuditManager
                def _load_cfg_wrapper(): return config
                
                # Audit Clients Setup
                audit_p_model = config.get("MODEL_AUDIT_PRIMARY")
                audit_s_model = config.get("MODEL_AUDIT_SECONDARY")
                audit_p_client = None
                audit_s_client = None
                
                if audit_p_model and audit_p_model != "default":
                     c = app.cfg.get_model_config(audit_p_model)
                     if c: audit_p_client = create_client_from_config(c)
                     
                if audit_s_model and audit_s_model != "default":
                     c = app.cfg.get_model_config(audit_s_model)
                     if c: audit_s_client = create_client_from_config(c)

                audit_manager = AuditManager(
            current_client, 
            model_override, 
            _load_cfg_wrapper, 
            platform="telegram",
            primary_client=audit_p_client,
            secondary_client=audit_s_client,
            primary_model=audit_p_model,
            secondary_model=audit_s_model,
            log_dir=app.cfg.get_platform_path("logs"),
            fallback_path=app.cfg._get_readable_path("audit_fallback.txt")
        )
                
                gen_result = await audit_manager.generate_with_audit(
                    messages=messages,
                    user_input=msg,
                    history=history,
                    temperature=temp_override
                )
                
                reply = gen_result if isinstance(gen_result, str) else gen_result.get("content", "")
                
                await _send_reply(app, event, reply, config, delay=True)
                
                # Record
                app.db.record_message_event(
                    app.tenant_id, "telegram", str(event.chat_id), "outbound", "sent",
                    model=model_override, stage=state.get("current_stage"), user_content=msg, bot_response=reply
                )
                
                app.stats['total_replies'] += 1
                app.stats['success_count'] += 1
                app.save_stats()

            except Exception as e:
                app.logger.log_system(f"❌ AI Gen Failed: {e}")
                app.stats['error_count'] += 1
                app.save_stats()
                
                # Safeguard: Send Fallback Message if AI fails
                fallback_msg = (config.get('KB_FALLBACK_MESSAGE') or config.get('HANDOFF_MESSAGE') or "").strip()
                if fallback_msg:
                     app.logger.log_system(f"⚠️ Triggering Safeguard Reply: {fallback_msg}")
                     await _send_reply(app, event, fallback_msg, config, delay=True)

async def _send_reply(app, event, reply, config, delay=True):
    if delay:
        dmin = float(config.get('REPLY_DELAY_MIN_SECONDS', 3.0))
        dmax = float(config.get('REPLY_DELAY_MAX_SECONDS', 10.0))
        await asyncio.sleep(random.uniform(dmin, dmax))
    
    use_quote = False
    if config.get('AUTO_QUOTE', False):
        prev = await get_prev_incoming_message(app.client, event.chat_id, max_id=event.id)
        if prev:
            sim = calculate_similarity(event.message.text or "", prev.text or "")
            if sim >= 0.25:
                use_quote = True
    
    if use_quote:
        await event.reply(reply)
    else:
        await app.client.send_message(event.chat_id, reply)
