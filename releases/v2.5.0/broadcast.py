#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔══════════════════════════════════════════════════════════════╗
║   ⚠️  Telegram 群发工具 - 使用须知                          ║
╠══════════════════════════════════════════════════════════════╣
║  1. 频繁群发可能导致账号被限制或封禁                         ║
║  2. 建议先小批量测试（3-5个对话）                            ║
║  3. 每条消息间隔 5-15 秒（已内置随机延迟）                   ║
║  4. 如遇 FloodWait 错误，程序会自动暂停                      ║
║  5. 请勿用于垃圾信息或违法用途                               ║
╚══════════════════════════════════════════════════════════════╝
"""

import asyncio
import os
import sys
import random
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.functions.messages import GetDialogFiltersRequest
from telethon.tl.types import DialogFilter
from telethon.errors import PeerFloodError, FloodWaitError
from dotenv import load_dotenv

# 解决 Windows 控制台编码问题
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# 加载环境变量
load_dotenv()

TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')

if not all([TELEGRAM_API_ID, TELEGRAM_API_HASH]):
    print("❌ 错误：请检查 .env 文件，缺少 TELEGRAM_API_ID 或 TELEGRAM_API_HASH")
    sys.exit(1)

# 使用与 main.py 相同的 session（避免重复登录）
client = TelegramClient('userbot_session', int(TELEGRAM_API_ID), TELEGRAM_API_HASH)


async def get_folders():
    """获取所有聊天分组（Chat Folders）"""
    try:
        result = await client(GetDialogFiltersRequest())
        folders = []
        
        for folder in result:
            if isinstance(folder, DialogFilter):
                folders.append({
                    'id': folder.id,
                    'title': folder.title,
                    'folder': folder
                })
        
        return folders
    except Exception as e:
        print(f"❌ 获取分组失败: {e}")
        return []


async def get_chats_in_folder(folder):
    """获取指定分组中的所有对话"""
    chats = []
    all_dialogs = await client.get_dialogs()
    
    # 收集分组中包含的 peer IDs
    included_peer_ids = set()
    
    # 处理 pinned_peers
    if hasattr(folder, 'pinned_peers') and folder.pinned_peers:
        for peer in folder.pinned_peers:
            try:
                entity = await client.get_entity(peer)
                included_peer_ids.add(entity.id)
            except:
                pass
    
    # 处理 include_peers
    if hasattr(folder, 'include_peers') and folder.include_peers:
        for peer in folder.include_peers:
            try:
                entity = await client.get_entity(peer)
                included_peer_ids.add(entity.id)
            except:
                pass
    
    # 从所有对话中筛选出属于该分组的
    for dialog in all_dialogs:
        if dialog.entity.id in included_peer_ids:
            chats.append(dialog)
    
    return chats


async def send_broadcast(chats, message):
    """
    执行群发任务
    
    Args:
        chats: 目标对话列表
        message: 要发送的消息内容
    """
    total = len(chats)
    success_count = 0
    failed_count = 0
    
    print(f"\n{'='*60}")
    print(f"📤 开始群发任务")
    print(f"目标数量: {total}")
    print(f"预计耗时: {total * 10 / 60:.1f} 分钟（平均 10 秒/条）")
    print(f"{'='*60}\n")
    
    for idx, dialog in enumerate(chats, 1):
        try:
            # 获取对话名称
            if hasattr(dialog.entity, 'title'):
                name = dialog.entity.title  # 群组/频道
            elif hasattr(dialog.entity, 'first_name'):
                name = dialog.entity.first_name  # 用户
            else:
                name = "Unknown"
            
            print(f"[{idx}/{total}] 正在发送到: {name}", end=" ... ")
            
            # 发送消息
            await client.send_message(dialog.entity, message)
            success_count += 1
            print("✅ 成功")
            
            # 随机延迟 5-15 秒（防止被检测为机器人）
            if idx < total:  # 最后一条不需要延迟
                delay = random.uniform(5, 15)
                print(f"   ⏳ 等待 {delay:.1f} 秒...")
                await asyncio.sleep(delay)
        
        except FloodWaitError as e:
            # Telegram 限流错误，需要等待指定秒数
            wait_time = e.seconds
            print(f"⚠️ 触发限流！需要等待 {wait_time} 秒")
            print(f"   暂停时间: {datetime.now().strftime('%H:%M:%S')}")
            await asyncio.sleep(wait_time)
            print(f"   继续发送...")
            # 重试当前消息
            try:
                await client.send_message(dialog.entity, message)
                success_count += 1
                print("✅ 重试成功")
            except Exception as retry_error:
                print(f"❌ 重试失败: {retry_error}")
                failed_count += 1
        
        except PeerFloodError:
            # 严重的刷屏限制，建议停止任务
            print(f"\n❌ 检测到 PeerFlood 错误（账号被临时限制）")
            print(f"   建议停止群发，等待 24 小时后再试")
            print(f"   已成功: {success_count}, 失败: {failed_count}, 剩余: {total - idx}")
            
            choice = input("\n是否继续尝试？(y/N): ").strip().lower()
            if choice != 'y':
                print("任务已中止")
                break
            else:
                print("等待 60 秒后继续...")
                await asyncio.sleep(60)
                failed_count += 1
        
        except Exception as e:
            print(f"❌ 失败: {e}")
            failed_count += 1
    
    # 任务总结
    print(f"\n{'='*60}")
    print(f"📊 群发任务完成")
    print(f"✅ 成功: {success_count}")
    print(f"❌ 失败: {failed_count}")
    print(f"📈 成功率: {success_count/total*100:.1f}%")
    print(f"{'='*60}\n")


async def main():
    print("\n🚀 Telegram 群发工具启动中...\n")
    
    # 启动客户端
    await client.start()
    
    # 获取用户信息
    me = await client.get_me()
    print(f"✅ 已登录: {me.first_name} (@{me.username or 'N/A'})\n")
    
    # 第一步：获取并显示所有分组
    print("📁 正在获取聊天分组...")
    folders = await get_folders()
    
    if not folders:
        print("❌ 未找到任何聊天分组，请先在 Telegram 中创建分组")
        return
    
    print(f"\n找到 {len(folders)} 个分组：\n")
    for idx, folder in enumerate(folders, 1):
        print(f"  [{idx}] {folder['title']}")
    
    # 第二步：选择目标分组
    print()
    while True:
        try:
            choice = input("请输入要群发的分组序号 (输入 0 取消): ").strip()
            choice_num = int(choice)
            
            if choice_num == 0:
                print("已取消")
                return
            
            if 1 <= choice_num <= len(folders):
                selected_folder = folders[choice_num - 1]
                break
            else:
                print(f"❌ 请输入 1-{len(folders)} 之间的数字")
        except ValueError:
            print("❌ 请输入有效的数字")
    
    print(f"\n✅ 已选择: {selected_folder['title']}")
    print("📝 正在获取分组中的对话...")
    
    chats = await get_chats_in_folder(selected_folder['folder'])
    
    if not chats:
        print("❌ 该分组中没有对话")
        return
    
    print(f"✅ 找到 {len(chats)} 个对话\n")
    
    # 显示前几个对话作为预览
    print("📋 预览前 5 个目标：")
    for i, dialog in enumerate(chats[:5], 1):
        if hasattr(dialog.entity, 'title'):
            name = dialog.entity.title
        elif hasattr(dialog.entity, 'first_name'):
            name = dialog.entity.first_name
        else:
            name = "Unknown"
        print(f"  {i}. {name}")
    
    if len(chats) > 5:
        print(f"  ... 还有 {len(chats) - 5} 个")
    
    # 第三步：输入消息内容
    print("\n" + "="*60)
    print("请输入要群发的消息内容（输入完成后按回车，再输入单独一行的 'END' 结束）：")
    print("="*60)
    
    message_lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        message_lines.append(line)
    
    message = "\n".join(message_lines).strip()
    
    if not message:
        print("❌ 消息内容不能为空")
        return
    
    # 第四步：确认发送
    print(f"\n{'='*60}")
    print("📝 消息预览：")
    print("-"*60)
    print(message)
    print("-"*60)
    print(f"将发送到 {len(chats)} 个对话")
    print(f"{'='*60}\n")
    
    confirm = input("⚠️ 确认发送？(输入 YES 确认): ").strip()
    
    if confirm != "YES":
        print("已取消")
        return
    
    # 执行群发
    await send_broadcast(chats, message)
    
    print("🎉 所有任务完成！")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断，任务已停止")
    except Exception as e:
        print(f"\n❌ 程序错误: {e}")


