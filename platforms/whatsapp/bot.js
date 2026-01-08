#!/usr/bin/env node
/**
 * WhatsApp AI Bot - 自动回复机器人
 * 基于 whatsapp-web.js 和 OpenAI API
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const QRCode = require('qrcode');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: '../../.env' });

// 配置
const CONFIG = {
    AI_API_KEY: process.env.AI_API_KEY,
    AI_BASE_URL: process.env.AI_BASE_URL || 'https://api.55.ai/v1',
    AI_MODEL: process.env.AI_MODEL_NAME || 'deepseek-v3.1',
    PRIVATE_REPLY: true,
    GROUP_REPLY: true,
    KEYWORDS: []
};

// 加载统计数据
function loadStats() {
    const statsPath = path.join(__dirname, 'stats.json');
    const defaultStats = {
        total_messages: 0,
        total_replies: 0,
        private_messages: 0,
        group_messages: 0,
        success_count: 0,
        error_count: 0,
        start_time: new Date().toISOString(),
        last_active: null
    };
    
    try {
        if (fs.existsSync(statsPath)) {
            const data = fs.readFileSync(statsPath, 'utf-8');
            const stats = JSON.parse(data);
            if (!stats.start_time) {
                stats.start_time = new Date().toISOString();
            }
            return stats;
        }
        return defaultStats;
    } catch {
        return defaultStats;
    }
}

// 保存统计数据
function saveStats(stats) {
    const statsPath = path.join(__dirname, 'stats.json');
    try {
        stats.last_active = new Date().toISOString();
        fs.writeFileSync(statsPath, JSON.stringify(stats, null, 2), 'utf-8');
    } catch (error) {
        console.error('⚠️ 保存统计失败:', error.message);
    }
}

// 加载配置
function loadConfig() {
    try {
        // 读取功能开关
        const configPath = path.join(__dirname, 'config.txt');
        if (fs.existsSync(configPath)) {
            const content = fs.readFileSync(configPath, 'utf-8');
            content.split('\n').forEach(line => {
                line = line.trim();
                if (line && !line.startsWith('#') && line.includes('=')) {
                    const [key, value] = line.split('=').map(s => s.trim());
                    if (key === 'PRIVATE_REPLY') {
                        CONFIG.PRIVATE_REPLY = value.toLowerCase() === 'on';
                    } else if (key === 'GROUP_REPLY') {
                        CONFIG.GROUP_REPLY = value.toLowerCase() === 'on';
                    }
                }
            });
        }

        // 读取关键词
        const keywordsPath = path.join(__dirname, 'keywords.txt');
        if (fs.existsSync(keywordsPath)) {
            const content = fs.readFileSync(keywordsPath, 'utf-8');
            CONFIG.KEYWORDS = content
                .split('\n')
                .map(line => line.trim())
                .filter(line => line && !line.startsWith('#'));
        }

        // 读取系统提示词
        const promptPath = path.join(__dirname, 'prompt.txt');
        if (fs.existsSync(promptPath)) {
            CONFIG.SYSTEM_PROMPT = fs.readFileSync(promptPath, 'utf-8').trim();
        } else {
            CONFIG.SYSTEM_PROMPT = '你是一个幽默、专业的个人助理，帮机主回复消息。';
        }

        console.log('✅ 配置加载成功');
        console.log(`   私聊回复: ${CONFIG.PRIVATE_REPLY ? '开启' : '关闭'}`);
        console.log(`   群聊回复: ${CONFIG.GROUP_REPLY ? '开启' : '关闭'}`);
        console.log(`   关键词数量: ${CONFIG.KEYWORDS.length}`);
    } catch (error) {
        console.error('⚠️ 配置加载失败:', error.message);
    }
}

// AI 请求函数
async function getAIReply(message, chatHistory = []) {
    try {
        const messages = [
            { role: 'system', content: CONFIG.SYSTEM_PROMPT },
            ...chatHistory,
            { role: 'user', content: message }
        ];

        const response = await axios.post(
            `${CONFIG.AI_BASE_URL}/chat/completions`,
            {
                model: CONFIG.AI_MODEL,
                messages: messages,
                temperature: 0.7,
                max_tokens: 500
            },
            {
                headers: {
                    'Authorization': `Bearer ${CONFIG.AI_API_KEY}`,
                    'Content-Type': 'application/json'
                },
                timeout: 30000,
                // 忽略 SSL 证书验证错误（适用于自签名证书或内网环境）
                httpsAgent: new (require('https').Agent)({
                    rejectUnauthorized: false
                })
            }
        );

        return response.data.choices[0].message.content;
    } catch (error) {
        console.error('❌ AI API 调用失败:', error.message);
        return null;
    }
}

// 获取聊天历史（简化版）
async function getChatHistory(chat, limit = 5) {
    try {
        const messages = await chat.fetchMessages({ limit: limit });
        const history = [];
        
        messages.reverse().forEach(msg => {
            if (msg.body && msg.body.trim()) {
                history.push({
                    role: msg.fromMe ? 'assistant' : 'user',
                    content: msg.body
                });
            }
        });
        
        return history.slice(-5); // 最多保留5条
    } catch (error) {
        console.error('⚠️ 获取历史失败:', error.message);
        return [];
    }
}

// 延迟函数
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// 主程序
async function main() {
    console.log('╔═══════════════════════════════════════════════════╗');
    console.log('║   💬 WhatsApp AI Bot - 自动回复机器人            ║');
    console.log('╚═══════════════════════════════════════════════════╝');
    console.log('');
    
    // 加载配置
    loadConfig();
    
    // 创建客户端
    const client = new Client({
        authStrategy: new LocalAuth({
            clientId: 'whatsapp-ai-bot'
        }),
        puppeteer: {
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        }
    });

    // QR 码登录
    client.on('qr', async (qr) => {
        console.log('\n📱 请使用 WhatsApp 扫描二维码登录：\n');
        qrcode.generate(qr, { small: true });
        console.log('\n提示：打开 WhatsApp > 设置 > 已连接的设备 > 连接设备\n');
        
        // 保存二维码为图片（供 Web 管理后台显示）
        try {
            const qrImagePath = path.join(__dirname, 'qr_code.png');
            await QRCode.toFile(qrImagePath, qr, {
                width: 400,
                margin: 2,
                color: {
                    dark: '#000000',
                    light: '#FFFFFF'
                }
            });
            
            // 创建状态文件
            const statusPath = path.join(__dirname, 'login_status.json');
            fs.writeFileSync(statusPath, JSON.stringify({
                status: 'waiting',
                qr_available: true,
                timestamp: new Date().toISOString()
            }));
            
            console.log('✅ 二维码已保存到 qr_code.png（可在 Web 管理后台查看）\n');
        } catch (error) {
            console.error('⚠️ 保存二维码失败:', error.message);
        }
    });

    // 登录成功
    client.on('ready', () => {
        console.log('\n✅ WhatsApp 已连接！');
        console.log('🤖 AI 机器人已启动，开始监听消息...\n');
        console.log('提示：按 Ctrl+C 停止运行\n');
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
        
        // 更新登录状态
        try {
            const statusPath = path.join(__dirname, 'login_status.json');
            const qrImagePath = path.join(__dirname, 'qr_code.png');
            
            fs.writeFileSync(statusPath, JSON.stringify({
                status: 'connected',
                qr_available: false,
                timestamp: new Date().toISOString()
            }));
            
            // 删除二维码图片
            if (fs.existsSync(qrImagePath)) {
                fs.unlinkSync(qrImagePath);
            }
        } catch (error) {
            console.error('⚠️ 更新状态失败:', error.message);
        }
    });

    // 认证失败
    client.on('auth_failure', (msg) => {
        console.error('❌ 认证失败:', msg);
    });

    // 断开连接
    client.on('disconnected', (reason) => {
        console.log('⚠️ 已断开连接:', reason);
    });

    // 消息处理
    client.on('message', async (msg) => {
        try {
            // 忽略自己的消息
            if (msg.fromMe) return;
            
            // 忽略状态更新等
            if (!msg.body || msg.isStatus) return;
            
            // 加载统计数据
            const stats = loadStats();
            stats.total_messages++;
            
            // 重新加载配置（热更新）
            loadConfig();
            
            const chat = await msg.getChat();
            // 简化获取联系人名称，避免 API 兼容性问题
            const contactName = msg._data.notifyName || chat.name || msg.from.split('@')[0];
            
            // 统计消息类型
            if (!chat.isGroup) {
                stats.private_messages++;
            } else {
                stats.group_messages++;
            }
            
            // 检查功能开关
            if (!chat.isGroup && !CONFIG.PRIVATE_REPLY) {
                console.log(`🔕 私聊回复已关闭，忽略消息 [${contactName}]: ${msg.body.substring(0, 30)}`);
                return;
            }
            
            if (chat.isGroup && !CONFIG.GROUP_REPLY) {
                console.log(`🔕 群聊回复已关闭，忽略消息 [${chat.name}]: ${msg.body.substring(0, 30)}`);
                return;
            }
            
            // 判断是否应该回复
            let shouldReply = false;
            
            if (!chat.isGroup) {
                // 私聊直接回复
                shouldReply = true;
                console.log(`📩 收到私聊 [${contactName}]: ${msg.body}`);
            } else {
                // 群聊：检查是否被 @ 或包含关键词
                const mentionedIds = await msg.getMentions();
                const isMentioned = mentionedIds.length > 0;
                
                if (isMentioned) {
                    shouldReply = true;
                    console.log(`📩 群聊被 @ [${chat.name}] [${contactName}]: ${msg.body}`);
                } else if (CONFIG.KEYWORDS.length > 0) {
                    const lowerBody = msg.body.toLowerCase();
                    const matchedKeyword = CONFIG.KEYWORDS.find(kw => 
                        lowerBody.includes(kw.toLowerCase())
                    );
                    
                    if (matchedKeyword) {
                        shouldReply = true;
                        console.log(`📩 群聊触发关键词 [${matchedKeyword}] [${chat.name}] [${contactName}]: ${msg.body}`);
                    }
                }
            }
            
            if (!shouldReply) {
                return;
            }
            
            // 显示"正在输入"状态
            chat.sendStateTyping();
            
            // 获取聊天历史
            const history = await getChatHistory(chat);
            
            // 调用 AI
            console.log('🤖 AI 正在思考...');
            const reply = await getAIReply(msg.body, history);
            
            if (reply) {
                // 模拟真人思考和打字延迟（3-10秒）
                const typingDelay = Math.floor(Math.random() * (10000 - 3000 + 1)) + 3000;
                console.log(`⏳ 延迟 ${(typingDelay/1000).toFixed(1)} 秒后回复（模拟真人）`);
                await delay(typingDelay);
                
                // 发送回复
                await msg.reply(reply);
                console.log(`📤 已回复: ${reply}\n`);
                
                // 统计成功回复
                stats.total_replies++;
                stats.success_count++;
                saveStats(stats);
            } else {
                console.log('❌ AI 回复失败，跳过\n');
                // 统计失败
                stats.error_count++;
                saveStats(stats);
            }
            
        } catch (error) {
            console.error('❌ 处理消息时出错:', error.message);
            // 统计错误
            const stats = loadStats();
            stats.error_count++;
            saveStats(stats);
        }
    });

    // 启动客户端
    console.log('🔄 正在初始化 WhatsApp 客户端...\n');
    client.initialize();

    // 优雅退出
    process.on('SIGINT', async () => {
        console.log('\n\n⚠️ 正在停止机器人...');
        await client.destroy();
        console.log('✅ 机器人已停止\n');
        process.exit(0);
    });
}

// 运行
main().catch(error => {
    console.error('❌ 程序错误:', error);
    process.exit(1);
});

