import uiautomator2 as u2
import subprocess
import time

min_wifi_speed = 0.5 # 最低网速

def check_wifi_speed():
    """使用 speedtest CLI 检测 Wi-Fi 网速，返回下载速度 (Mbps)。"""
    try:
        result = subprocess.run(["/opt/homebrew/bin/speedtest", "--format=json"], capture_output=True, text=True)
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            download_speed = data['download']['bandwidth'] / 125000  # 转换为 Mbps
            return download_speed
        else:
            print("Speedtest CLI 出现错误:", result.stderr)
            return 0
    except Exception as e:
        print(f"无法检测网速: {e}")
        return 0

def get_code_from_file():
    """从 code.txt 文件中获取第一个代码，并返回。"""
    try:
        with open("code.txt", "r") as file:
            lines = file.readlines()
            promo_code = lines[0].strip()
        return promo_code
    except IndexError:
        print("文件中没有代码。")
        return None

def remove_code_from_file(promo_code):
    """从 code.txt 文件中删除指定代码。"""
    with open("code.txt", "r") as file:
        lines = file.readlines()
    with open("code.txt", "w") as file:
        for line in lines:
            if line.strip() != promo_code:
                file.write(line)

def input_code_log(promo_code, wifi_speed, result):
    """将输入代码的结果记录到日志文件中。"""
    with open(f"logs/input-{time.strftime('%Y-%m-%d_%H-%M-%S')}.log", "a") as file:
        file.write(promo_code + ", " + wifi_speed + ", " + result + "\n")

def execute_promo_code(device):
    """执行プロモコード输入逻辑。"""
    # 确保应用在前台
    device.app_start("com.kddi.kdla.jp")
    # 等待应用加载完成
    time.sleep(15)

    # 关闭弹框
    if device(resourceId="com.kddi.kdla.jp:id/interstitial_image_relative_layout").exists:
        device(resourceId="com.kddi.kdla.jp:id/interstitial_image_relative_layout").click()
        print("关闭广告弹框")

    # 打印当前页面
    print(device.dump_hierarchy())
    
    time.sleep(10)

    # 检查按钮是否可见
    if not device(text="プロモコード", resourceId="com.kddi.kdla.jp:id/manageTileTitle").exists:
        # 使用fling方法滚动页面直到按钮出现在可见区域，指定最大尝试次数为5
        device(scrollable=True).fling(max_swipes=5)
        time.sleep(3)
    # 检查按钮是否可见
    if device(text="プロモコード", resourceId="com.kddi.kdla.jp:id/manageTileTitle").exists:
        # 点击按钮
        device(text="プロモコード", resourceId="com.kddi.kdla.jp:id/manageTileTitle").click()
        print("按钮已点击")
        time.sleep(3)

        # 查找"プロモコードを入力"
        device(text="プロモコードを入力", resourceId="com.kddi.kdla.jp:id/promo_code_input_text").click()
        
        promo_code = get_code_from_file()
        if promo_code is None:
            print("文件中没有可用的代码，终止执行")
            # 关闭应用
            device.app_stop("com.kddi.kdla.jp")
            return
        print("promo_code: " + promo_code)
        device.send_keys(promo_code)
        time.sleep(3)

        # 查找"利用する"
        device(text="利用する", resourceId="com.kddi.kdla.jp:id/validate_button").click()
        print("利用する已点击")
        time.sleep(3)

        result = "成功"
        # 查找"エラー"
        if device(text="エラー", resourceId="com.kddi.kdla.jp:id/dialog_discover_title").exists:
            result = "失敗"
            print("エラー已找到, 利用失敗。点击关闭 OK 按钮")
            device(text="OK", resourceId="com.kddi.kdla.jp:id/action_positive").click()
        else:
            remove_code_from_file(promo_code)
            print("利用する已经成功")
        input_code_log(promo_code, f"{wifi_speed:.2f} Mbps", result)
    else:
        print("按钮未找到，请检查界面状态！")

    # 等待3秒
    time.sleep(3)

    # 关闭应用
    device.app_stop("com.kddi.kdla.jp")

# 主程序
if __name__ == "__main__":
    # 连接设备 - 修改为本地模拟器连接
    try:
        subprocess.run(["adb", "kill-server"])
        subprocess.run(["adb", "start-server"])
        time.sleep(5)  # Wait for the emulator to start
        device = u2.connect('emulator-5554')  # 默认模拟器地址
        print("成功连接到模拟器")
    except Exception as e:
        print(f"连接模拟器失败: {e}")
        exit(1)
    # 关闭应用
    if device.app_current() == "com.kddi.kdla.jp":
        device.app_stop("com.kddi.kdla.jp")
    # 检查 Wi-Fi 网速
    print("正在检测 Wi-Fi 网速...")
    wifi_speed = check_wifi_speed()
    print(f"当前网速: {wifi_speed:.2f} Mbps")

    # 如果网速低于 1 Mbps，执行 povo 的代码输入逻辑
    if wifi_speed < min_wifi_speed:
        print("网速低于 " + str(min_wifi_speed) + " Mbps，执行プロモコード输入...")
        execute_promo_code(device)
    else:
        print("网速正常，大于" + str(min_wifi_speed) + " Mbps，无需执行プロモコード输入。")