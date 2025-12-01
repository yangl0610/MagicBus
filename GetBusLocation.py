import requests
import json
import time
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
}
# 实时车辆接口
url = "https://bccx.zju.edu.cn/schoolbus_wx/xbc/getXbcVehicleByLine"

def get_live_bus():
    

    print(f"--- 开始查询 {len(lines)} 条线路的实时车辆 ---")

    # 2. 遍历每一条线路
    for line in lines:
        line_id = line.get('lid') 
        RouteNumber = line.get('vehicleType') 
        if not line_id:
            continue

        try:
            payload = {
                "lid": line_id,
                "vehicleType": int(RouteNumber)
            }
        except Exception as e:
            print(f"出错了: {e}")

        try:
            resp = requests.post(url, headers=headers, data=payload)
            
            
            # 检查是不是 200 OK
            resp.raise_for_status()
            
            # 解析数据
            data = resp.json()
            print(payload) 
            with open(f"public/{line_id}.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f"数据已保存为 {line_id}.json")
        except Exception as e:
            print(f"出错了: {e}")

if __name__ == "__main__":
    try:
        with open("public/bus_line_data.json", "r", encoding="utf-8") as f:
            lines_data = json.load(f)
            lines = lines_data.get('data', [])
        while True:
            try:
                print("⏳ 开始新一轮抓取...")
                get_live_bus()
            except Exception as e:
                print(f"💥 发生严重错误: {e}")
            
            # 休息 5 秒再抓下一次 (实时性控制在这里)
            time.sleep(5)
    except FileNotFoundError:
        print("错误：找不到 bus_line_data.json，请先运行 GetBusLine.py")

       