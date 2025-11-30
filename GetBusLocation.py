import requests
import json
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
    
    # ==========================================
    # TODO: 把你在 Headers 里复制的那一大串 Cookie 粘贴在下面引号里
    # 注意：不要包含 "Cookie:" 这几个字，只要后面的内容
    # ==========================================
    "Cookie": "_pm0=6EJkTkSXxsGR0psHQQqbIYePxFEW2x%2Fdlzuu8ELyogM%3D; _ga=GA1.1.1847613122.1763388298; JWTUser=%7B%22account%22%3A%223250102105%22%2C%22id%22%3A724459%2C%22tenant_id%22%3A112%7D; Hm_lvt_35da6f287722b1ee93d185de460f8ba2=1763552545,1763663559,1763904252,1763907334; _pf0=KnirxtmW1bgJcKudBcwbjGRdd32SFAJd1iONVQJNmjE%3D; iPlanetDirectoryPro=txuNyOoYPicyHrF%2F6pCKc2OsJX34JInSG15eT9XYoN1wem5nLcys9iGc8NBizL7Bc4Jffl4RsW%2BTtZkJdaxGmkfMJz1NfO1uWU7wgopm9ZnWiZY7cCJIQoP9wkOURpGtVOZ5eg%2FLaPcmnUHdjiX67%2BlWLbaVdKjLTFxPhcqL7X6aj8hVj9TyclyQoEdSsaKxp4R%2BiamwHyqzBN03oWU3vhFn0%2BY5kWF3%2FEeZiQprxB%2BQ0Gto%2BISBjSIKGIY6qdBDdP8BZDjFGG%2BQBazqywmFYwHVHX2%2BCq2fDEPm8PB%2FrmCdi4CJKHZBsm565%2BV%2Bomhz2Iplaf6NQW%2FXCV%2BxGNB9YGeT1SHf35h52EPZ4D1v1SaM2NBEYJy%2FQAohIRip0wwv; _ga_H5QC8W782Q=GS2.1.s1764473292$o11$g1$t1764473681$j52$l0$h0" 
}
# 实时车辆接口
url = "https://bccx.zju.edu.cn/schoolbus_wx/xbc/getXbcVehicleByLine"

def get_live_bus():
    try:
        with open("bus_line_data.json", "r", encoding="utf-8") as f:
            lines_data = json.load(f)
            lines = lines_data.get('data', [])
    except FileNotFoundError:
        print("错误：找不到 bus_line_data.json，请先运行 GetBusLine.py")
        return

    print(f"--- 开始查询 {len(lines)} 条线路的实时车辆 ---")

    # 2. 遍历每一条线路
    for line in lines:
        line_id = line.get('lid') 
        RouteNumber = line.get('vehicleType') 
        if not line_id:
            continue

        # 3. 构造请求参数 (Payload)
        # !!! 这里就是在模仿浏览器发送的数据 !!!
        # ... 上面的代码保持不变 ...

        if not line_id:
            continue

        # 3. 构造请求参数 (Payload)
        # 🛠️ 关键修改：加上 int() 强制转换为整数
        try:
            payload = {
                "lid": line_id,
                "vehicleType": int(RouteNumber)
            }
        except Exception as e:
            print(f"出错了: {e}")

        try:
            # 发送请求
            # print(f"正在查询: {payload}") # 可以把这行注释打开，看看发出去的是不是数字
            resp = requests.post(url, headers=headers, data=payload)
            
            # ... 下面的代码保持不变 ...
            
            # 检查是不是 200 OK
            resp.raise_for_status()
            
            # 解析数据
            data = resp.json()
            print(payload) 
            with open(f"zju_busline_data{line_id}.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    print("数据已保存为 zju_bus_data.json")
        except Exception as e:
            print(f"出错了: {e}")


if __name__ == "__main__":
    get_live_bus()