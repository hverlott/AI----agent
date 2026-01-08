import os
from PIL import Image, ImageDraw, ImageFont

def draw_arrow(draw, start, end, color=(0,0,0), width=3, arrow_size=8):
    draw.line([start, end], fill=color, width=width)
    # arrow head
    import math
    angle = math.atan2(end[1]-start[1], end[0]-start[0])
    p1 = (end[0]-arrow_size*math.cos(angle - math.pi/6),
          end[1]-arrow_size*math.sin(angle - math.pi/6))
    p2 = (end[0]-arrow_size*math.cos(angle + math.pi/6),
          end[1]-arrow_size*math.sin(angle + math.pi/6))
    draw.polygon([end, p1, p2], fill=color)

def main(output_path):
    W, H = 2000, 1200
    img = Image.new('RGB', (W, H), (246, 243, 236))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    participants = [
        ("用户", 100),
        ("Telethon", 300),
        ("Handler(main.py)", 500),
        ("KeywordManager", 700),
        ("AuditManager", 900),
        ("QA", 1100),
        ("知识库KB", 1300),
        ("AI API", 1500),
        ("日志/统计", 1700),
        ("Telegram", 1900),
    ]
    top = 80
    # Draw participant headers and lifelines
    for name, x in participants:
        draw.rectangle([(x-90, top-30), (x+90, top+30)], outline=(15,107,109), width=2, fill=(255,255,255))
        bbox = draw.textbbox((0,0), name, font=font)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        draw.text((x - tw/2, top - th/2), name, fill=(31,35,40), font=font)
        draw.line([(x, top+30), (x, H-60)], fill=(200, 190, 175), width=2)

    y = top + 120
    # 用户 -> Telethon
    draw_arrow(draw, (participants[0][1], y), (participants[1][1], y), color=(0,0,0))
    draw.text((participants[0][1]+10, y-20), "发送消息", fill=(0,0,0), font=font)
    y += 50
    # Telethon -> Handler
    draw_arrow(draw, (participants[1][1], y), (participants[2][1], y), color=(0,0,0))
    draw.text((participants[1][1]+10, y-20), "NewMessage事件", fill=(0,0,0), font=font)
    y += 60
    # Handler 自检
    draw.text((participants[2][1]-60, y-15), "触发检查：私聊/被@/关键词/上下文/白名单", fill=(80,80,80), font=font)
    y += 50
    # 分支：QA 命中
    draw.text((60, y-25), "分支A：QA命中", fill=(13,94,13), font=font)
    draw_arrow(draw, (participants[2][1], y), (participants[5][1], y), color=(13,94,13))
    draw_arrow(draw, (participants[5][1], y+40), (participants[2][1], y+40), color=(13,94,13))
    draw.text((participants[5][1]-60, y+20), "返回固定答案", fill=(13,94,13), font=font)
    draw_arrow(draw, (participants[2][1], y+80), (participants[9][1], y+80), color=(13,94,13))
    draw.text((participants[2][1]+10, y+60), "发送QA回复", fill=(13,94,13), font=font)
    draw_arrow(draw, (participants[2][1], y+120), (participants[8][1], y+120), color=(120,120,120))
    draw.text((participants[2][1]+10, y+100), "记录日志/更新统计", fill=(120,120,120), font=font)
    y += 170
    # 分支：QA未命中
    draw.text((60, y-25), "分支B：QA未命中", fill=(155,88,0), font=font)
    # Handler -> KB
    draw_arrow(draw, (participants[2][1], y), (participants[6][1], y), color=(155,88,0))
    draw.text((participants[2][1]+10, y-20), "检索Top-2上下文", fill=(155,88,0), font=font)
    y += 50
    # Handler -> AI (生成草稿)
    draw_arrow(draw, (participants[2][1], y), (participants[7][1], y), color=(0,0,160))
    draw.text((participants[2][1]+10, y-20), "注入上下文调用AI", fill=(0,0,160), font=font)
    draw_arrow(draw, (participants[7][1], y+40), (participants[2][1], y+40), color=(0,0,160))
    draw.text((participants[7][1]-80, y+20), "返回草稿回复", fill=(0,0,160), font=font)
    y += 80
    # 关键词前置拦截
    draw_arrow(draw, (participants[2][1], y), (participants[3][1], y), color=(160,0,0))
    draw.text((participants[2][1]+10, y-20), "关键词检测(draft)", fill=(160,0,0), font=font)
    draw_arrow(draw, (participants[3][1], y+40), (participants[2][1], y+40), color=(160,0,0))
    draw.text((participants[3][1]-80, y+20), "allow优先/命中block或敏感→拒绝", fill=(160,0,0), font=font)
    # 拦截兜底
    draw_arrow(draw, (participants[2][1], y+80), (participants[9][1], y+80), color=(160,0,0))
    draw.text((participants[2][1]+10, y+60), "若命中违禁/敏感→兜底话术", fill=(160,0,0), font=font)
    y += 120
    # 审核员AI（双机拦截）
    draw_arrow(draw, (participants[2][1], y), (participants[4][1], y), color=(0,120,0))
    draw.text((participants[2][1]+10, y-20), "审核(本地/远程集群)", fill=(0,120,0), font=font)
    draw_arrow(draw, (participants[4][1], y+40), (participants[2][1], y+40), color=(0,120,0))
    draw.text((participants[4][1]-120, y+20), "返回PASS/FAIL与建议", fill=(0,120,0), font=font)
    y += 80
    # 重试与兜底
    draw.text((participants[2][1]-120, y-20), "FAIL→重试至上限; 超限→兜底", fill=(120,0,0), font=font)
    draw_arrow(draw, (participants[2][1], y), (participants[9][1], y), color=(120,0,0))
    y += 50
    # 发送AI回复（PASS）
    draw_arrow(draw, (participants[2][1], y), (participants[9][1], y), color=(0,0,0))
    draw.text((participants[2][1]+10, y-20), "PASS→发送AI回复", fill=(0,0,0), font=font)
    y += 50
    # 日志/统计
    draw_arrow(draw, (participants[2][1], y), (participants[8][1], y), color=(120,120,120))
    draw.text((participants[2][1]+10, y-20), "写入审核/系统日志、更新统计", fill=(120,120,120), font=font)

    # Title
    title = "客户来消息到 AI 回复的完整时序（含双机拦截与关键词前置）"
    tbbox = draw.textbbox((0,0), title, font=font)
    tw = tbbox[2]-tbbox[0]
    draw.text(((W - tw)//2, 20), title, fill=(15,107,109), font=font)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, format="JPEG", quality=92)
    # 同步生成PNG版本，便于在页面或文档中引用
    png_out = os.path.splitext(output_path)[0] + ".png"
    img.save(png_out, format="PNG", optimize=True)

if __name__ == "__main__":
    out = os.path.join("docs", "CustomerToAI-Sequence.jpg")
    main(out)
    # 额外输出到 docs/images 目录
    img_dir = os.path.join("docs", "images")
    os.makedirs(img_dir, exist_ok=True)
    alt_out = os.path.join(img_dir, "10-客户到AI完整时序.png")
    main(alt_out)
