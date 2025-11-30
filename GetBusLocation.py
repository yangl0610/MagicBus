import requests
import json

# 接口地址
url = "https://bccx.zju.edu.cn/schoolbus_wx/xbc/getXbcLine"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    
    # ==========================================
    # TODO: 把你在 Headers 里复制的那一大串 Cookie 粘贴在下面引号里
    # 注意：不要包含 "Cookie:" 这几个字，只要后面的内容
    # ==========================================
    "Cookie": "在这里粘贴你复制的长字符串_pm0=6EJkTkSXxsGR0psHQQqbIYePxFEW2x%2Fdlzuu8ELyogM%3D; _ga=GA1.1.1847613122.1763388298; JWTUser=%7B%22account%22%3A%223250102105%22%2C%22id%22%3A724459%2C%22tenant_id%22%3A112%7D; Hm_lvt_35da6f287722b1ee93d185de460f8ba2=1763552545,1763663559,1763904252,1763907334; _pf0=KnirxtmW1bgJcKudBcwbjGRdd32SFAJd1iONVQJNmjE%3D; iPlanetDirectoryPro=txuNyOoYPicyHrF%2F6pCKc2OsJX34JInSG15eT9XYoN1wem5nLcys9iGc8NBizL7Bc4Jffl4RsW%2BTtZkJdaxGmkfMJz1NfO1uWU7wgopm9ZnWiZY7cCJIQoP9wkOURpGtVOZ5eg%2FLaPcmnUHdjiX67%2BlWLbaVdKjLTFxPhcqL7X6aj8hVj9TyclyQoEdSsaKxp4R%2BiamwHyqzBN03oWU3vhFn0%2BY5kWF3%2FEeZiQprxB%2BQ0Gto%2BISBjSIKGIY6qdBDdP8BZDjFGG%2BQBazqywmFYwHVHX2%2BCq2fDEPm8PB%2FrmCdi4CJKHZBsm565%2BV%2Bomhz2Iplaf6NQW%2FXCV%2BxGNB9YGeT1SHf35h52EPZ4D1v1SaM2NBEYJy%2FQAohIRip0wwv; _ga_H5QC8W782Q=GS2.1.s1764473292$o11$g1$t1764473681$j52$l0$h0" 
}

try:
    # 发送请求
    print("正在尝试连接浙大校车服务器...")
    resp = requests.post(url, headers=headers)
    
    # 检查是不是 200 OK
    resp.raise_for_status()
    
    # 解析数据
    data = resp.json()
    
    # 简单检查一下是不是拿到数据了
    if 'data' in data and len(data['data']) > 0:
        print(f"成功！获取到了 {len(data['data'])} 条线路信息。")
        print("第一条线路名为:", data['data'][0].get('xclx')) # 猜测字段名为 xclx (校车路线) 或 line_name
        
        # 保存到文件，这就是我们做网站的“原料”
        with open("zju_bus_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            print("数据已保存为 zju_bus_data.json")
    else:
        print("请求成功，但没有数据，可能是 Cookie 过期了，或者字段不对。")
        print(data)

except Exception as e:
    print(f"出错了: {e}")