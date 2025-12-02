
type bustype ={
  vehiNum: string,
  px: number,
  py: number,
  speedTime: string,
  vehicleType: string,
  direction: number
}

type Position={
    px:number,
    py:number
}

type stationtype={
    stationAlias:string,
    stationAliasNo:number,
    stationPosition:Position,
}

/**
 * something like this
 * @lid L820(线路唯一标识码)
 * @lineAlias n号线
 * @lineTypeName 线路中文全称
 * @stationIds 线路所经站点的id,用-连接
 * @color 线路可视化在官网上的颜色
 * @stationList 线路所经站点详情信息
 * @positionList 
 * 
 * s
 */
type linetype={
    lid: number,
    lineAlias: string,
    lineTypeName: string,
    stationIds: number,
    color: string,
    stationList: stationtype[],
    pointList: Position[],
    vehicleType: number
}