import os
from PIL import Image, ImageDraw, ImageFont
import math

def draw_arrow(draw, start, end, color=(0,0,0), width=2, arrow_size=10):
    draw.line([start, end], fill=color, width=width)
    angle = math.atan2(end[1]-start[1], end[0]-start[0])
    p1 = (end[0]-arrow_size*math.cos(angle - math.pi/6),
          end[1]-arrow_size*math.sin(angle - math.pi/6))
    p2 = (end[0]-arrow_size*math.cos(angle + math.pi/6),
          end[1]-arrow_size*math.sin(angle + math.pi/6))
    draw.polygon([end, p1, p2], fill=color)

def draw_box(draw, x, y, w, h, text, bg_color, border_color, font, text_color=(0,0,0)):
    draw.rectangle([x, y, x+w, y+h], fill=bg_color, outline=border_color, width=2)
    # Centered text logic
    lines = text.split('\n')
    
    # Calculate total text height
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0,0), line, font=font)
        line_heights.append(bbox[3] - bbox[1] + 5) # +5 padding
    
    total_text_h = sum(line_heights)
    current_y = y + (h - total_text_h) / 2
    
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0,0), line, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((x + (w - tw) / 2, current_y), line, fill=text_color, font=font)
        current_y += line_heights[i]

def main(output_path):
    W, H = 1600, 1000
    img = Image.new('RGB', (W, H), (246, 243, 236)) # Off-white background
    draw = ImageDraw.Draw(img)
    
    # Load Font (Chinese)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 24)
        font_title = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 36)
        font_small = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 18)
    except:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 24)
            font_title = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 36)
            font_small = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 18)
        except:
            print("Warning: Chinese font not found, using default.")
            font = ImageFont.load_default()
            font_title = font
            font_small = font

    # Title
    draw.text((50, 30), "Telegram AI Bot 系统功能全景图", fill=(30,30,30), font=font_title)

    # --- Areas ---
    # 1. Management Area (Left)
    draw.rectangle([50, 100, 500, 900], outline=(200,200,200), width=2)
    draw.text((70, 110), "管理后台 (Web Admin)", fill=(100,100,100), font=font)

    # 2. Core System (Center)
    draw.rectangle([550, 100, 1050, 900], outline=(200,200,200), width=2)
    draw.text((570, 110), "核心引擎 (Core Engine)", fill=(100,100,100), font=font)

    # 3. External & Data (Right)
    draw.rectangle([1100, 100, 1550, 900], outline=(200,200,200), width=2)
    draw.text((1120, 110), "外部服务与数据 (External & Data)", fill=(100,100,100), font=font)

    # --- Nodes ---
    
    # Left: Admin
    draw_box(draw, 100, 200, 300, 80, "管理员\n(Admin User)", (230,240,255), (0,100,200), font)
    draw_box(draw, 100, 350, 300, 200, "Streamlit UI\n- 机器人开关 (Start/Stop)\n- 参数热配置 (Config)\n- 知识库管理 (KB/PDF)\n- 仪表盘/日志 (Stats)\n- 群发工具 (Broadcast)", (255,255,255), (0,100,200), font_small)
    draw_arrow(draw, (250, 280), (250, 350), color=(0,100,200))
    
    # Center: Core
    draw_box(draw, 600, 200, 400, 80, "Telegram Server\n(Cloud API)", (220,220,220), (50,50,50), font)
    draw_box(draw, 650, 350, 300, 400, "Bot Client Process\n(Telethon Async Loop)", (255,250,240), (200,100,0), font)
    
    # Inside Bot Client
    draw_box(draw, 680, 420, 240, 50, "Event Listener\n(监听消息)", (255,255,255), (200,100,0), font_small)
    draw_box(draw, 680, 490, 240, 50, "Filter & Router\n(过滤/路由)", (255,255,255), (200,100,0), font_small)
    draw_box(draw, 680, 560, 240, 50, "Business Logic\n(业务逻辑处理)", (255,255,255), (200,100,0), font_small)
    draw_box(draw, 680, 630, 240, 50, "Response Queue\n(发送队列)", (255,255,255), (200,100,0), font_small)
    
    draw_arrow(draw, (800, 280), (800, 350), color=(50,50,50), width=3) # Server <-> Client
    draw_arrow(draw, (800, 350), (800, 280), color=(50,50,50), width=3)
    
    # Right: Services
    draw_box(draw, 1150, 200, 350, 100, "AI LLM API\n(DeepSeek/OpenAI)\n- 智能回复/意图识别", (230,255,230), (0,150,0), font_small)
    draw_box(draw, 1150, 350, 350, 100, "Audit System\n(内容风控)\n- 敏感词/合规检测", (255,230,230), (200,0,0), font_small)
    draw_box(draw, 1150, 500, 350, 150, "Knowledge Base\n(FAISS/Vector)\n- PDF/Docx/Txt 导入\n- 语义检索 (RAG)", (255,255,240), (200,200,0), font_small)
    draw_box(draw, 1150, 700, 350, 100, "Data Storage\n- SQLite (Logs/Stats)\n- JSON (Config/Keywords)\n- User Content (Learning)", (240,240,240), (100,100,100), font_small)

    # --- Cross Connections ---
    
    # Admin -> Data (Conceptual)
    draw_arrow(draw, (400, 550), (1150, 750), color=(150,150,150), width=1)
    
    # Core -> AI
    draw_arrow(draw, (950, 585), (1150, 250), color=(0,150,0)) # Logic -> AI
    
    # Core -> Audit
    draw_arrow(draw, (950, 585), (1150, 400), color=(200,0,0)) # Logic -> Audit
    
    # Core -> KB
    draw_arrow(draw, (950, 585), (1150, 575), color=(200,200,0)) # Logic -> KB
    
    # Core -> DB
    draw_arrow(draw, (950, 655), (1150, 750), color=(100,100,100)) # Logic -> DB
    
    # Admin -> Core (Control)
    draw_arrow(draw, (400, 380), (650, 380), color=(0,100,200)) # Admin Start/Stop
    draw.text((450, 355), "进程守护/监控", fill=(0,100,200), font=font_small)

    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, format="PNG")
    print(f"Generated {output_path}")

if __name__ == "__main__":
    out = os.path.join("docs", "images", "11-Telegram系统功能全景.png")
    main(out)
