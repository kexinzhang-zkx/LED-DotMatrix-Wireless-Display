from machine import Pin
from neopixel import NeoPixel
from time import sleep
import random
import network
import socket

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
    for y in range(0,7):
        w=14-y*2
        l=(16-w)//2
        outline[y][l]=outline[y][l+w]=1
    outline[7][7]=outline[7][9]=outline[8][7]=outline[8][9]=1
    for y in range(9,16):
        w=(y-8)*2
        l=(16-w)//2
        outline[y][l]=outline[y][l+w]=1
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
    if mirror: pat=mirror_digit_pattern(pat)
    for y in range(6):
        for x in range(4):
            if pat[y][x]==1:
                px,py=x_pos+x,y_pos+y
                if 0<=px<16 and 0<=py<16:
                    pattern[py][px]=color

def generate_hourglass_with_digit(seconds, mirror=True):
    pattern = [[0]*16 for _ in range(16)]
    outline=generate_custom_outline()
    for y in range(16):
        for x in range(16):
            if outline[y][x]==1: pattern[y][x]=1

    inner=[]
    for y in range(16):
        l=r=None
        for x in range(16):
            if outline[y][x]==1:
                l=x if l is None else l
                r=x
        if l is not None and r is not None and l<r:
            inner.append((y,l+1,r))

    max_upper=sum(r-l for y,l,r in inner if y<8)
    total=max(0,int(max_upper*seconds/15))
    sand=[[False]*16 for _ in range(16)]

    upper=[row for row in inner if row[0]<8]
    rem=total
    for y in range(6,-1,-1):
        if rem<=0: break
        for (yy,l,r) in upper:
            if yy==y:
                avail=[]
                for x in range(l,r):
                    if not (12<=x<=15 and 5<=y<=10) and not (0<=x<=3 and 5<=y<=10):
                        if not sand[y][x]: avail.append(x)
                while avail and rem>0:
                    x=avail.pop(random.randint(0,len(avail)-1))
                    sand[y][x]=True
                    rem-=1

    if seconds>0 and random.random()<0.7: sand[8][8]=True

    bottom=[row for row in inner if row[0]>=9]
    bot_sand=max_upper-total
    rem=bot_sand
    for y in range(15,8,-1):
        if rem<=0: break
        for (yy,l,r) in bottom:
            if yy==y:
                for x in range(l,r):
                    if (12<=x<=15 and 5<=y<=10) or (0<=x<=3 and 5<=y<=10):
                        continue
                    if rem<=0: break
                    if y+1>=16 or sand[y+1][x]:
                        sand[y][x]=True
                        rem-=1

    for y in range(16):
        for x in range(16):
            if sand[y][x]: pattern[y][x]=2

    if seconds>=0:
        tens,units=(str(seconds//10),str(seconds%10)) if seconds>9 else ('0',str(seconds))
        draw_digit(pattern,tens,12,5,mirror=mirror)
        draw_digit(pattern,units,0,5,mirror=mirror)
    return pattern

def display_pattern(pattern):
    pixels.fill((0,0,0))
    for y in range(16):
        for x in range(16):
            if pattern[y][x]==1:
                idx=get_pixel_index(x,y)
                pixels[idx]=(0,0,255)
            elif pattern[y][x]==2:
                idx=get_pixel_index(x,y)
                pixels[idx]=(255,255,0)
    pixels.write()

# -------------------------- WiFi + 无线控制 --------------------------
# 全局状态
running=True
current_sec=15

# 1. 开热点（AP模式）
def wifi_start_ap():
    ap=network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(ssid='ESP32_Hourglass',password='12345678')
    while not ap.active():
        sleep(0.5)
    print('WiFi热点已开启：ESP32_Hourglass')
    print('IP地址：',ap.ifconfig()[0])
    return ap.ifconfig()[0]

# 2. 网页控制
def web_server(ip):
    addr=socket.getaddrinfo(ip,80)[0][-1]
    s=socket.socket()
    s.bind(addr)
    s.listen(1)
    print('Web服务器启动，浏览器访问：http://',ip)
    while True:
        conn,addr=s.accept()
        req=conn.recv(1024).decode()
        global running,current_sec
        if '/start' in req:
            running=True
        elif '/pause' in req:
            running=False
        elif '/reset' in req:
            running=True
            current_sec=15
        html="""
        <html>
            <body style="text-align:center;font-size:30px;">
                <h1>ESP32 无线沙漏控制</h1>
                <a href="/start"><button style="font-size:30px;padding:10px 20px;">开始</button></a>
                <a href="/pause"><button style="font-size:30px;padding:10px 20px;">暂停</button></a>
                <a href="/reset"><button style="font-size:30px;padding:10px 20px;">重置</button></a>
            </body>
        </html>
        """
        conn.send(html)
        conn.close()

# -------------------------- 主循环（无线+沙漏） --------------------------
try:
    ip=wifi_start_ap()
    import _thread
    _thread.start_new_thread(web_server,(ip,))  # 网页后台运行

    print("沙漏动画循环开始...")
    while True:
        if running:
            pattern=generate_hourglass_with_digit(current_sec)
            display_pattern(pattern)
            print(f"剩余时间: {current_sec:02d}秒 (无线控制中)")
            if current_sec>0:
                current_sec-=1
            else:
                sleep(0.5)
                current_sec=15
            sleep(1)
        else:
            sleep(0.1)

except KeyboardInterrupt:
    print("程序已中断")
finally:
    pixels.fill((0,0,0))
    pixels.write()
    print("所有LED已关闭")
