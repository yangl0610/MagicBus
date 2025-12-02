// 车辆数据结构 (对应 L820.json 等)
export type bustype = {
  vehiNum: string;
  px: number;      // 经度
  py: number;      // 纬度
  speedTime: string;
  vehicleType: string; // "2" 或 "3"
  direction: number;   // 0-360
};

export type Position = {
  px: number;
  py: number;
};

export type stationtype = {
  stationAlias: string;
  stationAliasNo: string | number;
  stationLong: number;
  stationLat: number;
};

// 线路数据结构 (对应 bus_line_data.json)
export type linetype = {
  lid: string | number;
  lineAlias: string;
  lineTypeName: string;
  stationIds: string;
  color: string;
  stationList: stationtype[];
  pointList: Position[]; // 轨迹点列表
  vehicleType: string | number;
};
```

### 3. 如何验证

1.  **文件位置**：确保 `bus_line_data.json` 以及 `L820.json`, `L821.json` 等文件都在项目的 `public/` 目录下。
2.  **数据加载**：刷新页面，打开 Network 面板，你应该能看到浏览器请求了 `/bus_line_data.json`。
3.  **轨迹显示**：如果一切正常，地图上应该会出现一条深蓝色的轨迹线，完美贴合你在 Python 脚本中生成的那些道路点。
4.  **站点显示**：轨迹线上应该会有一些白色的圆点，那是站点。
5.  **车辆显示**：如果 `/L820.json` 中有数据，地图上应该会出现红色的或白色的小车图标在移动。

这样修改后，前端就完全是在消费你上传的这份真实数据包了。