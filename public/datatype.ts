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
