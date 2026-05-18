from machine import Pin
from neopixel import NeoPixel
from time import sleep
import random
import network
import socket
import _thread

# -------------------------- LED屏幕显示模块 --------------------------
WIDTH = 16
HEIGHT = 16
NUM_PIXELS = WIDTH * HEIGHT
pixels = NeoPixel(Pin(18), NUM_PIXELS)

# 蛇形映射
def get_pixel_index(x, y):
    return y * WIDTH + x if y % 2 == 0 else y * WIDTH + (WIDTH - 1 - x)

# 沙漏轮廓
def generate_custom_outline():
    outline = [[0]*16 for _ in range(16)]
    for y in range(0, 7):
        w = 14 - y * 2
        l = (16 - w) // 2
        outline[y][l] = outline[y][l + w] = 1
    outline[7][7] = outline[7][9] = outline[8][7] = outline[8][9] = 1
    for y in range(9, 16):
        w = (y - 8) * 2
        l = (16 - w) // 2
        outline[y][l] = outline[y][l + w] = 1
    return outline

# 数字字库
DIGITS = {
    '0':[[1,1,1,1],[1,0,0,1],[1,0,0,1],[1,0,0,1],[1,0,0,1],[1,1,1,1]],
    '1':[[0,0,1,1],[0,1,1,1],[0,0,1,1],[0,0,1,1],[0,0,1,1],[0,0,1,1]],
    '2':[[1,1,1,1],[0,0,0,1],[0,0,1,1],[0,1,0,0],[1,0,0,0],[1,1,1,1]],
    '3':[[1,1,1,1],[0,0,0,1],[0,1,1,1],[0,0,0,1],[0,0,0,1],[1,1,1,1]],
    '4':[[1,0,0,1],[1,0,0,1],[1,0,0,1],[1,1,1,1],[0,0,0,1],[0,0,0,1]],
    '5':[[1,1,1,1],[1,0,0,0],[1,1,1,1],[0,0,0,1],[0,0,0,1],[1,1,1,1]],
    '6':[[1,1,1,1],[1,0,0,0],[1,1,1,1],[1,0,0,1],[1,0,0,1],[1,1,1,1]],
    '7':[[1,1,1,1],[0,0,0,1],[0,0,1,1],[0,1,0,0],[0,1,0,0],[0,1,0,0]],
    '8':[[1,1,1,1],[1,0,0,1],[1,1,1,1],[1,0,0,1],[1,0,0,1],[1,1,1,1]],
    '9':[[1,1,1,1],[1,0,0,1],[1,1,1,1],[0,0,0,1],[0,0,0,1],[1,1,1,1]]
}

def mirror_digit_pattern(pat):
    return [r[::-1] for r in pat]

def draw_digit(pattern, digit, x_pos, y_pos, color=2, mirror=False):
    if digit not in DIGITS: return
    pat = DIGITS[digit]
    if mirror: pat = mirror_digit_pattern(pat)
    for y in range(6):
        for x in range(4):
            if pat[y][x] == 1:
                px, py = x_pos + x, y_pos + y
                if 0 <= px < 16 and 0 <= py < 16:
                    pattern[py][px] = color

def generate_hourglass_with_digit(seconds, mirror=True):
    pattern = [[0]*16 for _ in range(16)]
    outline = generate_custom_outline()
    for y in range(16):
        for x in range(16):
            if outline[y][x] == 1: pattern[y][x] = 1

    inner = []
    for y in range(16):
        l = r = None
        for x in range(16):
            if outline[y][x] == 1:
                l = x if l is None else l
                r = x
        if l is not None and r is not None and l < r:
            inner.append((y, l + 1, r))

    max_upper = sum(r - l for y, l, r in inner if y < 8)
    total = max(0, int(max_upper * seconds / 15))
    sand = [[False]*16 for _ in range(16)]

    upper = [row for row in inner if row[0] < 8]
    rem = total
    for y in range(6, -1, -1):
        if rem <= 0: break
        for (yy, l, r) in upper:
            if yy == y:
                avail = []
                for x in range(l, r):
                    if not (12 <= x <= 15 and 5 <= y <= 10) and not (0 <= x <= 3 and 5 <= y <= 10):
                        if not sand[y][x]: avail.append(x)
                while avail and rem > 0:
                    x = avail.pop(random.randint(0, len(avail) - 1))
                    sand[y][x] = True
                    rem -= 1

    if seconds > 0 and random.random() < 0.7: sand[8][8] = True

    bottom = [row for row in inner if row[0] >= 9]
    bot_sand = max_upper - total
    rem = bot_sand
    for y in range(15, 8, -1):
        if rem <= 0: break
        for (yy, l, r) in bottom:
            if yy == y:
                for x in range(l, r):
                    if (12 <= x <= 15 and 5 <= y <= 10) or (0 <= x <= 3 and 5 <= y <= 10):
                        continue
                    if rem <= 0: break
                    if y + 1 >= 16 or sand[y + 1][x]:
                        sand[y][x] = True
                        rem -= 1

    for y in range(16):
        for x in range(16):
            if sand[y][x]: pattern[y][x] = 2

    if seconds >= 0:
        tens, units = (str(seconds // 10), str(seconds % 10)) if seconds > 9 else ('0', str(seconds))
        draw_digit(pattern, tens, 12, 5, mirror=mirror)
        draw_digit(pattern, units, 0, 5, mirror=mirror)
    return pattern

def display_pattern(pattern):
    pixels.fill((0, 0, 0))
    for y in range(16):
        for x in range(16):
            if pattern[y][x] == 1:
                idx = get_pixel_index(x, y)
                pixels[idx] = (0, 0, 255) # 蓝色轮廓
            elif pattern[y][x] == 2:
                idx = get_pixel_index(x, y)
                pixels[idx] = (255, 255, 0) # 黄色沙子和数字
    pixels.write()

# -------------------------- WiFi + 无线控制 --------------------------
running = True
current_sec = 15

# 1. 开热点（AP模式）
def wifi_start_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(ssid='ESP32_Hourglass', password='12345678')
    while not ap.active():
        sleep(0.5)
    print('WiFi热点已开启：ESP32_Hourglass')
    print('IP地址：', ap.ifconfig()[0])
    return ap.ifconfig()[0]

# 2. 网页控制服务器（已修复 HTTP 响应问题）
def web_server(ip):
    global running, current_sec
    addr = socket.getaddrinfo(ip, 80)[0][-1]
    s = socket.socket()
    # 允许端口复用，防止重启程序时报 OSError: [Errno 98] EADDRINUSE
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(2)
    print('Web服务器启动，浏览器访问：http://' + ip)
    
    while True:
        try:
            conn, addr = s.accept()
            req = conn.recv(1024).decode('utf-8')
            
            # 如果是空请求，直接跳过
            if not req:
                conn.close()
                continue
                
            # 处理指令并进行页面重定向（防止刷新网页时重复触发动作）
            if '/start' in req:
                running = True
                # 标准 HTTP 303 重定向响应头
                conn.send('HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n')
            elif '/pause' in req:
                running = False
                conn.send('HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n')
            elif '/reset' in req:
                current_sec = 15
                running = True
                conn.send('HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n')
            else:
                # 正常的首页 HTML 响应，带有标准的 HTTP/1.1 200 OK 响应头
                html = """<!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>ESP32 沙漏控制</title>
                </head>
                <body style="text-align:center; font-family: sans-serif; padding-top: 50px;">
                    <h1>ESP32 无线沙漏控制</h1>
                    <p style="font-size:20px;">当前状态: """ + ("运行中" if running else "已暂停") + """</p>
                    <div style="margin-top: 30px;">
                        <a href="/start"><button style="font-size:25px; padding:15px 30px; margin:10px; background-color:#4CAF50; color:white; border:none; border-radius:5px;">开始</button></a>
                        <a href="/pause"><button style="font-size:25px; padding:15px 30px; margin:10px; background-color:#f44336; color:white; border:none; border-radius:5px;">暂停</button></a>
                        <a href="/reset"><button style="font-size:25px; padding:15px 30px; margin:10px; background-color:#008CBA; color:white; border:none; border-radius:5px;">重置</button></a>
                    </div>
                </body>
                </html>
                """
                conn.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n')
                conn.send(html)
            
            conn.close()
        except Exception as e:
            print("网络线程异常:", e)
            try:
                conn.close()
            except:
                pass

# -------------------------- 主循环（无线+沙漏） --------------------------
try:
    ip = wifi_start_ap()
    # 启动网页后台运行线程
    _thread.start_new_thread(web_server, (ip,))  

    print("沙漏动画循环开始...")
    while True:
        if running:
            pattern = generate_hourglass_with_digit(current_sec)
            display_pattern(pattern)
            print("剩余时间: {:02d}秒".format(current_sec))
            
            if current_sec > 0:
                current_sec -= 1
            else:
                sleep(0.5)
                current_sec = 15 # 倒计时结束，重置为15秒
            
            # 拆分 sleep，让后台网页控制响应更灵敏
            for _ in range(10):
                sleep(0.1)
        else:
            sleep(0.1) # 暂停状态，低功耗等待

except KeyboardInterrupt:
    print("程序已中断")
finally:
    pixels.fill((0, 0, 0))
    pixels.write()
    print("所有LED已关闭")
