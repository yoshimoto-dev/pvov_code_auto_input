import uiautomator2 as u2
import subprocess
import time

min_wifi_speed = 0.5 # 最低网速

def check_wifi_speed():
    """speedtest CLI を使用して Wi-Fi 速度をチェックし、ダウンロード速度 (Mbps) を返します。"""
    try:
        result = subprocess.run(["/opt/homebrew/bin/speedtest", "--format=json"], capture_output=True, text=True)
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            download_speed = data['download']['bandwidth'] / 125000  # Mbpsに変換
            return download_speed
        else:
            print("Speedtest CLI エラー:", result.stderr)
            return 0
    except Exception as e:
        print(f"エラー: {e}")
        return 0

def get_code_from_file():
    """code.txt ファイルから最初のコードを取得し、返します。"""
    try:
        with open("code.txt", "r") as file:
            lines = file.readlines()
            promo_code = lines[0].strip()
        return promo_code
    except IndexError:
        print("ファイルにコードがありません。")
        return None

def remove_code_from_file(promo_code):
    """code.txt ファイルから指定されたコードを削除します。"""
    with open("code.txt", "r") as file:
        lines = file.readlines()
    with open("code.txt", "w") as file:
        for line in lines:
            if line.strip() != promo_code:
                file.write(line)

def input_code_log(promo_code, wifi_speed, result):
    """入力コードの結果をログファイルに記録します。"""
    with open(f"logs/input-{time.strftime('%Y-%m-%d_%H-%M-%S')}.log", "a") as file:
        file.write(promo_code + ", " + wifi_speed + ", " + result + "\n")

def execute_promo_code(device):
    """プロモコード入力ロジックを実行します。"""
    # アプリをフォアグラウンドにする
    device.app_start("com.kddi.kdla.jp")
    # アプリがロードされるのを待つ
    time.sleep(15)

    # ポップアップを閉じる
    if device(resourceId="com.kddi.kdla.jp:id/interstitial_image_relative_layout").exists:
        device(resourceId="com.kddi.kdla.jp:id/interstitial_image_relative_layout").click()
        print("広告ポップアップを閉じる")

    # 現在のページを印刷
    print(device.dump_hierarchy())
    
    time.sleep(10)

    # ボタンが表示されているか確認
    if not device(text="プロモコード", resourceId="com.kddi.kdla.jp:id/manageTileTitle").exists:
        # fling方法でページをスクロールし、ボタンが表示されるまで最大5回試行
        device(scrollable=True).fling(max_swipes=5)
        time.sleep(3)
    # ボタンが表示されているか確認
    if device(text="プロモコード", resourceId="com.kddi.kdla.jp:id/manageTileTitle").exists:
        # ボタンをクリック
        device(text="プロモコード", resourceId="com.kddi.kdla.jp:id/manageTileTitle").click()
        print("ボタンをクリックしました")
        time.sleep(3)

        # "プロモコードを入力"を探す
        device(text="プロモコードを入力", resourceId="com.kddi.kdla.jp:id/promo_code_input_text").click()
        
        promo_code = get_code_from_file()
        if promo_code is None:
            print("ファイルに使用可能なコードがありません。実行を終了します")
            # アプリを閉じる
            device.app_stop("com.kddi.kdla.jp")
            return
        print("promo_code: " + promo_code)
        device.send_keys(promo_code)
        time.sleep(3)

        # "利用する"を探す
        device(text="利用する", resourceId="com.kddi.kdla.jp:id/validate_button").click()
        print("利用するをクリックしました")
        time.sleep(3)

        result = "成功"
        # "エラー"を探す
        if device(text="エラー", resourceId="com.kddi.kdla.jp:id/dialog_discover_title").exists:
            result = "失敗"
            print("エラーが見つかりました。利用失敗。OKボタンをクリックします")
            device(text="OK", resourceId="com.kddi.kdla.jp:id/action_positive").click()
        else:
            remove_code_from_file(promo_code)
            print("利用するが成功しました")
        input_code_log(promo_code, f"{wifi_speed:.2f} Mbps", result)
    else:
        print("ボタンが見つかりません。インターフェースの状態を確認してください！")

    # 3秒待つ
    time.sleep(3)

    # アプリを閉じる
    device.app_stop("com.kddi.kdla.jp")

# メインプログラム
if __name__ == "__main__":
    # デバイスに接続 - ローカルエミュレータ接続に変更
    try:
        subprocess.run(["adb", "kill-server"])
        subprocess.run(["adb", "start-server"])
        time.sleep(5)  # Wait for the emulator to start
        device = u2.connect('emulator-5554')  # デフォルトのエミュレータアドレス
        print("エミュレータに接続しました")
    except Exception as e:
        print(f"エミュレータ接続に失敗しました: {e}")
        exit(1)
    # アプリを閉じる
    if device.app_current() == "com.kddi.kdla.jp":
        device.app_stop("com.kddi.kdla.jp")
    # Wi-Fi速度をチェック
    print("Wi-Fi 速度をチェックしています...")
    wifi_speed = check_wifi_speed()
    print(f"現在の速度: {wifi_speed:.2f} Mbps")

    # 速度が1 Mbps未満の場合、povoのコード入力ロジックを実行
    if wifi_speed < min_wifi_speed:
        print("速度が " + str(min_wifi_speed) + " Mbps 未満です。プロモコード入力を実行します...")
        execute_promo_code(device)
    else:
        print("速度が正常です。" + str(min_wifi_speed) + " Mbps 以上です。プロモコード入力は不要です。")
