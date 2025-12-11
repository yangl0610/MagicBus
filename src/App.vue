<template>
  <div class="app-container">
    
    <div 
      class="map-container" 
      ref="mapContainerRef"
      @pointerdown="onPointerDown"
      @pointermove="onPointerMove"
      @pointerup="onPointerUp"
      @pointerleave="onPointerUp"
      @wheel.prevent="onWheel"
    >
      <div 
        class="map-wrapper" 
        :class="{ 'is-animating': isAnimating, 'map-shifted': isPanelOpen }"
        :style="wrapperStyle"
      >
        <img 
          ref="mapImgRef"
          src="/zjgMap.png" 
          class="map-image" 
          alt="Map" 
          draggable="false" 
          @load="initMap"
        />
        
        <svg class="map-overlay" viewBox="0 0 1000 1000" preserveAspectRatio="none">
          <polyline 
            v-if="currentLinePoints.length > 0"
            :points="svgPolylinePoints"
            fill="none"
            stroke="#1989fa"
            stroke-width="8"
            stroke-opacity="0.6"
            stroke-linecap="round"
            stroke-linejoin="round"
            vector-effect="non-scaling-stroke" 
          />
        </svg>

        <div 
          v-if="userLocation"
          class="user-marker"
          :style="getMarkerStyle(userLocation.lat, userLocation.lng)"
        >
          <div class="user-dot-pulse"></div>
          <div class="user-dot"></div>
        </div>

        <div 
          v-for="(station, index) in currentStations" 
          :key="'map_st_' + index"
          class="station-marker"
          :style="getMarkerStyle(station.stationLat, station.stationLong)"
        >
          <div 
            class="station-dot"
            :class="{ 'is-selected': selectedStationIndex === index }"
          ></div>
        </div>

        <div 
          v-for="bus in busList" 
          :key="'map_bus_' + bus.vehiNum"
          class="bus-marker"
          :style="getMarkerStyle(bus.py, bus.px, bus.direction)"
          @click.stop="focusBus(bus)"
        >
          <div class="bus-rotate-container" :style="{ transform: `rotate(${bus.direction}deg)` }">
            <div 
              class="school-bus-icon" 
              :class="isSmallCar(bus.vehicleType) ? 'bus-white' : 'bus-red'"
            >
              <div class="bus-windshield"></div>
              <div class="bus-roof"></div>
              <div class="bus-lights-l"></div>
              <div class="bus-lights-r"></div>
            </div>
          </div>
          <div class="bus-label">{{ bus.vehiNum.slice(-3) }}</div>
        </div>
      </div>
      
      <div class="map-controls" :class="{ 'shifted': isPanelOpen }">
        <div class="control-btn" @click.stop="zoomIn"><van-icon name="plus" /></div>
        <div class="control-btn" @click.stop="zoomOut"><van-icon name="minus" /></div>
        <div class="control-btn" @click.stop="resetMap"><van-icon name="aim" /></div>
        <div class="control-btn" @click.stop="getUserLocation" :class="{ 'active': userLocation }">
          <van-icon name="location-o" />
        </div>
      </div>
    </div>

    <div 
      class="bottom-panel" 
      :class="{ 'is-collapsed': !isPanelOpen }"
    >
      <div 
        class="panel-handle-bar" 
        @click="togglePanel"
        @touchstart.stop="onPanelTouchStart"
        @touchmove.stop="onPanelTouchMove"
        @touchend.stop="onPanelTouchEnd"
      >
        <div class="handle"></div>
      </div>

      <div class="tabs-container">
        <van-tabs 
          v-model:active="activeTabId" 
          shrink
          color="#1989fa" 
          title-active-color="#1989fa"
          title-inactive-color="#999"
          line-width="20px"
          line-height="3px"
          @click-tab="onTabChange"
          background="#ffffff"
          class="custom-tabs"
        >
          <van-tab 
            v-for="line in busLineData" 
            :key="line.lid" 
            :title="line.lineAlias" 
            :name="line.lid"
          />
        </van-tabs>
      </div>

      <div class="panel-content">
        <div class="status-header">
           <div class="header-left">
             <span class="line-eta-text">{{ overallNearestETA }}</span>
             <div class="sub-info">
                <span class="line-direction-tag">
                  往 {{ getDestinationName() }}
                </span>
                <span class="time-tip" v-if="lastUpdateTime">
                  {{ lastUpdateTime }} 更新
                </span>
             </div>
           </div>
           
           <div class="header-right">
             <div class="nearest-bus-info" v-if="nearestBusToFocus">
                <span class="nb-label">最近车辆</span>
                <span class="nb-plate">{{ nearestBusToFocus }}</span>
             </div>
             <div class="nearest-bus-info empty" v-else>
                <span class="nb-label">暂无车辆</span>
             </div>
           </div>
        </div>

        <div 
          class="linear-route-scroll" 
          v-if="currentStations.length > 0"
          ref="routeScrollRef"
          @pointerdown="onListPointerDown"
          @pointermove="onListPointerMove"
          @pointerup="onListPointerUp"
          @pointerleave="onListPointerUp"
        >
          <div class="linear-route-track">
            <div class="route-line-bg"></div>
            <div 
              v-for="(station, index) in currentStations" 
              :key="'node_' + index" 
              class="route-node"
              :class="{ 
                'is-nearest': nearestStationToUser?.index === index, // 离人最近的站
                'is-selected': selectedStationIndex === index        // 选中的站
              }"
              :id="'station-node-' + index"
              @click="selectStation(index)"
            >
              <div class="node-dot-wrapper">
                <div class="node-dot"></div>
                <div class="node-dot-ring" v-if="selectedStationIndex === index"></div>
                <div class="user-location-badge" v-if="nearestStationToUser?.index === index && selectedStationIndex === null">
                  <van-icon name="location" />
                </div>
              </div>
              
              <div class="node-name">
                {{ station.stationAlias }}
              </div>

              <div class="node-buses-container-bottom">
                <div 
                  v-for="bus in getBusesNearStation(index)" 
                  :key="bus.vehiNum"
                  class="bus-on-route-icon"
                  @click.stop="focusBus(bus)"
                >
                  <div class="css-side-bus-mini" :class="isSmallCar(bus.vehicleType) ? 'side-white' : 'side-red'">
                    <div class="wheel wheel-f"></div>
                    <div class="wheel wheel-b"></div>
                  </div>
                  <div class="bus-plate-tiny">{{ bus.vehiNum.slice(-3) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <van-empty v-else description="暂无线路数据" class="empty-state" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, reactive, nextTick, watch } from 'vue';
import { showToast } from 'vant';
import type { bustype, linetype } from './datatype';

// [配置] 地图的经纬度边界 (左上角和右下角)，用于将GPS映射到图片百分比
const MAP_BOUNDS = { minLon: 120.0665, maxLon: 120.0961, minLat: 30.2910, maxLat: 30.3148 };
const activeTabId = ref<any>("L820"); // 当前选中的线路ID
const API_URLS = { LINE_DATA: '/bus_line_data.json', BUS_DATA_PREFIX: '/' };

// [状态] 核心数据 Refs
const busLineData = ref<linetype[]>([]); // 线路列表
const busList = ref<bustype[]>([]);      // 车辆实时数据
const lastUpdateTime = ref<string>('');  // 上次刷新时间
const isPanelOpen = ref(true);           // 底部面板是否展开
const userLocation = ref<{ lat: number, lng: number } | null>(null); // 用户GPS坐标
const cachedNearestStation = ref<{ station: any, index: number, distance: number } | null>(null); // 缓存的最近站点
const selectedStationIndex = ref<number | null>(null); // 用户手动点击选中的站点索引

// [引用] DOM元素引用，用于操作滚动条
const routeScrollRef = ref<HTMLElement | null>(null);

let timer: number | null = null; // 轮询定时器ID

// --- [核心逻辑 1] 地图引擎状态 ---
const mapContainerRef = ref<HTMLElement | null>(null);
const mapImgRef = ref<HTMLImageElement | null>(null);
// mapState 存储地图当前的变换状态：缩放比例(scale) 和 位移(x, y)
const mapState = reactive({ scale: 1, x: 0, y: 0 });

// 拖拽相关状态变量
const isDragging = ref(false); // 是否正在拖拽
const isAnimating = ref(false); // 是否正在进行CSS动画（如回弹时）
const dragStart = reactive({ x: 0, y: 0 }); // 拖拽开始时的鼠标坐标
const mapStart = reactive({ x: 0, y: 0 });  // 拖拽开始时的地图位置
const pointerDownPos = reactive({ x: 0, y: 0 }); // 用于区分是点击还是拖拽

let naturalWidth = 0; let naturalHeight = 0; // 图片原始尺寸
let containerWidth = 0; let containerHeight = 0; // 容器显示尺寸
let minScale = 1; // 最小缩放比例（填满屏幕）

// 底部面板触摸状态
const panelTouch = reactive({ startY: 0, moving: false });

// [计算属性] 生成最终应用到地图div上的CSS样式
const wrapperStyle = computed(() => ({
  // 使用 translate 移动，scale 缩放。calc(-50%) 是为了让原点在中心
  transform: `translate(calc(-50% + ${mapState.x}px), calc(-50% + ${mapState.y}px)) scale(${mapState.scale})`,
  // 如果处于动画状态（如回弹、重置），则添加 transition
  transition: isAnimating.value ? 'transform 0.4s cubic-bezier(0.25, 1, 0.5, 1)' : 'none' 
}));

// [地图方法] 初始化：图片加载完成后调用
const initMap = () => {
  if (!mapImgRef.value || !mapContainerRef.value) return;
  // 获取图片和容器尺寸
  naturalWidth = mapImgRef.value.naturalWidth;
  naturalHeight = mapImgRef.value.naturalHeight;
  updateContainerSize();
  // 计算最小缩放比，保证图片始终覆盖容器
  const scaleX = containerWidth / naturalWidth;
  const scaleY = containerHeight / naturalHeight;
  minScale = Math.max(scaleX, scaleY);
  mapState.scale = minScale;
  checkBoundsAndSnap(); // 检查边界
};

// 更新容器尺寸（窗口大小改变时）
const updateContainerSize = () => {
  if (mapContainerRef.value) {
    containerWidth = mapContainerRef.value.clientWidth;
    containerHeight = mapContainerRef.value.clientHeight;
  }
};

// 监听窗口 resize 事件
window.addEventListener('resize', () => {
  updateContainerSize();
  if (naturalWidth > 0) {
      // 重新计算最小缩放比，防止窗口变大后出现白边
     const scaleX = containerWidth / naturalWidth;
     const scaleY = containerHeight / naturalHeight;
     minScale = Math.max(scaleX, scaleY);
     if (mapState.scale < minScale) {
       mapState.scale = minScale;
       checkBoundsAndSnap();
     }
  }
});

// [地图方法] 计算拖拽边界限制
const getLimits = () => {
  const currentW = naturalWidth * mapState.scale;
  const currentH = naturalHeight * mapState.scale;
  // 计算允许滑动的最大距离
  const limitX = Math.max(0, (currentW - containerWidth) / 2);
  const limitY = Math.max(0, (currentH - containerHeight) / 2);
  const OVERSCROLL = 300; // 允许超出边界的弹性距离
  return { 
    limitX: limitX + OVERSCROLL, 
    limitY: limitY + OVERSCROLL 
  };
};

// [交互] 按下鼠标/手指
const onPointerDown = (e: PointerEvent) => {
  isDragging.value = true;
  isAnimating.value = false; // 拖拽时立刻停止动画，跟随手指
  dragStart.x = e.clientX;   // 记录起点
  dragStart.y = e.clientY;
  mapStart.x = mapState.x;   // 记录地图当前位置
  mapStart.y = mapState.y;
  pointerDownPos.x = e.clientX;
  pointerDownPos.y = e.clientY;
  // 捕获指针，防止鼠标移出浏览器失效
  (e.target as HTMLElement).setPointerCapture(e.pointerId);
};

// [交互] 移动鼠标/手指
const onPointerMove = (e: PointerEvent) => {
  if (!isDragging.value) return;
  e.preventDefault();
  const deltaX = e.clientX - dragStart.x;
  const deltaY = e.clientY - dragStart.y;
  let newX = mapStart.x + deltaX;
  let newY = mapStart.y + deltaY;
  
  // 阻尼效果：如果拖拽超出了边界，移动速度变慢 (Math.pow 0.7)
  const { limitX, limitY } = getLimits();
  if (newX > limitX) newX = limitX + Math.pow(newX - limitX, 0.7);
  else if (newX < -limitX) newX = -limitX - Math.pow(-limitX - newX, 0.7);
  if (newY > limitY) newY = limitY + Math.pow(newY - limitY, 0.7);
  else if (newY < -limitY) newY = -limitY - Math.pow(-limitY - newY, 0.7);
  
  mapState.x = newX;
  mapState.y = newY;
};

// [交互] 松开鼠标/手指
const onPointerUp = (e: PointerEvent) => {
  isDragging.value = false;
  (e.target as HTMLElement).releasePointerCapture(e.pointerId);
  checkBoundsAndSnap(); // 松开后，如果超出了边界，弹回去
  
  // 判断是点击还是拖拽：如果移动距离小于5px，视为点击
  const dist = Math.hypot(e.clientX - pointerDownPos.x, e.clientY - pointerDownPos.y);
  if (dist < 5) onMapClick();
};

const onMapClick = () => {
  // 点击地图空白处，收起面板并取消选中站点
  if (isPanelOpen.value) {
    isPanelOpen.value = false;
    selectedStationIndex.value = null; 
  }
};

// [核心算法] 检查边界并回弹（Snap效果）
const checkBoundsAndSnap = () => {
  const { limitX, limitY } = getLimits();
  // 此时的limit不包含 OVERSCROLL，是实际物理边界
  // 因为 getLimits 返回包含了 OVERSCROLL，这里需要重新算一下物理边界（简化逻辑：直接用不带offset的逻辑判断）
  // 注意：这里的代码逻辑其实利用了 getLimits 的 OVERSCROLL 进行阻尼，
  // 但回弹时应该回到真正的边界（limitX - OVERSCROLL）。
  // 原代码逻辑这里有些简化，直接判断 mapState 是否超过了 limitX (含OVERSCROLL中的一部分逻辑，这里不细究，理解为“回正”即可)
  
  // 修正：上面的 getLimits 包含了 OVERSCROLL。
  // 真正的物理边界应该是 (currentW - containerWidth) / 2。
  // 下面的逻辑其实是把地图限制在“不留白边”的范围内。
  const currentW = naturalWidth * mapState.scale;
  const currentH = naturalHeight * mapState.scale;
  const trueLimitX = Math.max(0, (currentW - containerWidth) / 2);
  const trueLimitY = Math.max(0, (currentH - containerHeight) / 2);

  let targetX = mapState.x;
  let targetY = mapState.y;
  let needsSnap = false;

  // 如果当前位置超出了真正的边界，需要弹回去
  if (mapState.x > trueLimitX) { targetX = trueLimitX; needsSnap = true; } 
  else if (mapState.x < -trueLimitX) { targetX = -trueLimitX; needsSnap = true; }
  
  if (mapState.y > trueLimitY) { targetY = trueLimitY; needsSnap = true; } 
  else if (mapState.y < -trueLimitY) { targetY = -trueLimitY; needsSnap = true; }

  if (needsSnap) {
    isAnimating.value = true; // 开启过渡动画
    requestAnimationFrame(() => { mapState.x = targetX; mapState.y = targetY; });
  }
};

const onWheel = (e: WheelEvent) => {
  const delta = e.deltaY < 0 ? 0.1 : -0.1;
  applyZoom(delta);
};

const applyZoom = (delta: number) => {
  isAnimating.value = true;
  let newScale = mapState.scale + delta;
  // 限制缩放范围
  if (newScale < minScale) newScale = minScale;
  if (newScale > 4.0) newScale = 4.0;
  mapState.scale = newScale;
  nextTick(() => { checkBoundsAndSnap(); }); // 缩放后可能会出现白边，需要检查边界
};

const zoomIn = () => applyZoom(0.2);
const zoomOut = () => applyZoom(-0.2);
const resetMap = () => {
  isAnimating.value = true;
  mapState.scale = minScale;
  mapState.x = 0;
  mapState.y = 0;
};

// --- [核心逻辑 2] GPS与定位 ---

const getUserLocation = () => {
  if (!navigator.geolocation) {
    showToast('浏览器不支持定位');
    return;
  }
  showToast('正在定位...');
  navigator.geolocation.getCurrentPosition(
    (position) => {
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;
      userLocation.value = { lat, lng };
      showToast('定位成功');
      recalculateNearestStation(); // 定位成功后，算一下离哪个站最近
      if (cachedNearestStation.value) {
        selectedStationIndex.value = cachedNearestStation.value.index;
      }
      jumpToUserLocation(); // 视野跳转到人所在的位置
    },
    (error) => {
      console.error(error);
      showToast('定位失败，请检查权限');
    }
  );
};

const jumpToUserLocation = () => {
  if (!userLocation.value) return;
  jumpToCoords(userLocation.value.lat, userLocation.value.lng);
};

// [算法] 将经纬度点移动到地图中心
const jumpToCoords = (lat: number, lng: number) => {
  const { x: percentX, y: percentY } = geoToPercent(lat, lng);
  // 如果坐标在地图外太远，就不跳转了
  if (percentX < -50 || percentX > 150 || percentY < -50 || percentY > 150) return;

  const currentW = naturalWidth * mapState.scale;
  const currentH = naturalHeight * mapState.scale;
  
  // 计算目标位移：目标点百分比 转换成 像素偏移量
  // (50 - percentX) 的意思是：把该点移动到中心(50%)所需的位移
  const targetX = ((50 - percentX) / 100) * currentW;
  const targetY = ((50 - percentY) / 100) * currentH;

  isAnimating.value = true;
  mapState.x = targetX;
  mapState.y = targetY;
  
  nextTick(() => { checkBoundsAndSnap(); });
};

const isSmallCar = (type: any) => String(type) === '3';

// --- 面板手势交互 ---
const onPanelTouchStart = (e: TouchEvent) => {
  panelTouch.startY = e.touches[0].clientY;
  panelTouch.moving = true;
};
const onPanelTouchMove = (e: TouchEvent) => { if (panelTouch.moving) e.preventDefault(); };
const onPanelTouchEnd = (e: TouchEvent) => {
  if (!panelTouch.moving) return;
  panelTouch.moving = false;
  const endY = e.changedTouches[0].clientY;
  const distance = endY - panelTouch.startY;
  // 向下滑动超过50px则关闭，向上滑动则打开
  if (distance > 50 && isPanelOpen.value) isPanelOpen.value = false;
  else if (distance < -50 && !isPanelOpen.value) isPanelOpen.value = true;
};
const togglePanel = () => { isPanelOpen.value = !isPanelOpen.value; };

// [核心算法] 经纬度转百分比坐标
// 原理：(当前经度 - 最小经度) / 总经度差 = 百分比
const geoToPercent = (lat: number, lon: number) => {
  const x = ((lon - MAP_BOUNDS.minLon) / (MAP_BOUNDS.maxLon - MAP_BOUNDS.minLon)) * 100;
  const y = ((MAP_BOUNDS.maxLat - lat) / (MAP_BOUNDS.maxLat - MAP_BOUNDS.minLat)) * 100; 
  return { x, y };
};

// 获取标记点的 style 对象 (top/left)
const getMarkerStyle = (lat: number, lon: number, direction?: number) => {
  const { x, y } = geoToPercent(lat, lon);
  // 如果有方向（是车），层级(z-index)高一点
  return { left: `${x}%`, top: `${y}%`, zIndex: direction !== undefined ? 20 : 10 };
};

// [数据计算] 当前选中的线路信息
const currentLineData = computed(() => busLineData.value.find(l => String(l.lid) === String(activeTabId.value)));
const currentStations = computed(() => currentLineData.value?.stationList || []);
const currentPoints = computed(() => currentLineData.value?.pointList || []);
const currentLinePoints = computed(() => currentPoints.value);

// 将线路点转换为 SVG polyline 需要的 "x,y x,y" 字符串格式
const svgPolylinePoints = computed(() => {
  return currentLinePoints.value.map(p => {
    const { x, y } = geoToPercent(p.py, p.px); 
    // SVG viewBox是1000x1000，所以百分比(0-100)要乘以10
    return `${x * 10},${y * 10}`;
  }).join(' ');
});

// 计算某个站点附近的车辆（用于在拓扑图上显示小车）
const getBusesNearStation = (stationIndex: number) => {
  const station = currentStations.value[stationIndex];
  if (!station) return [];
  return busList.value.filter(bus => {
    // 简单算法：遍历所有站点，看这辆车离哪个站最近
    let minD = Infinity;
    let closestIdx = -1;
    currentStations.value.forEach((st, idx) => {
      const d = Math.pow(bus.px - st.stationLong, 2) + Math.pow(bus.py - st.stationLat, 2);
      if (d < minD) { minD = d; closestIdx = idx; }
    });
    // 如果最近的站就是当前这个站，说明车在这里
    return closestIdx === stationIndex;
  });
};

const MINS_PER_STOP = 2.5; // 估算：每站平均2.5分钟
const getStationETA = (stationIndex: number) => {
  if (busList.value.length === 0) return null;
  let minStops = Infinity;
  // 遍历所有车，找出一辆离目标站最近且在它后面（即将到达）的车
  busList.value.forEach(bus => {
    let closestIdx = -1;
    let minDist = Infinity;
    // 找出这辆车当前在哪个站
    currentStations.value.forEach((st, idx) => {
      const d = Math.pow(bus.px - st.stationLong, 2) + Math.pow(bus.py - st.stationLat, 2);
      if (d < minDist) { minDist = d; closestIdx = idx; }
    });
    // 目标站索引 - 车辆当前站索引 = 还需要走几站
    const stopsDiff = stationIndex - closestIdx;
    if (stopsDiff >= 0 && stopsDiff < minStops) minStops = stopsDiff;
  });

  if (minStops === Infinity) return null;
  if (minStops === 0) return { text: '即将到站', isArriving: true };
  const mins = Math.ceil(minStops * MINS_PER_STOP);
  return { text: `${mins}分`, isArriving: false };
};

// 计算“最近车辆”的车牌号，用于Header显示
const nearestBusToFocus = computed(() => {
  let targetIndex = -1;
  // 优先级：选中的站 > 离用户最近的站
  if (selectedStationIndex.value !== null) {
    targetIndex = selectedStationIndex.value;
  } else if (nearestStationToUser.value) {
    targetIndex = nearestStationToUser.value.index;
  }

  if (targetIndex === -1 || busList.value.length === 0) return null;

  let minStops = Infinity;
  let targetBus = null;

  busList.value.forEach(bus => {
    // ... (同上的查找逻辑，找最近的车)
    let closestIdx = -1;
    let minDist = Infinity;
    currentStations.value.forEach((st, idx) => {
      const d = Math.pow(bus.px - st.stationLong, 2) + Math.pow(bus.py - st.stationLat, 2);
      if (d < minDist) { minDist = d; closestIdx = idx; }
    });

    const stopsDiff = targetIndex - closestIdx;
    if (stopsDiff >= 0) {
      if (stopsDiff < minStops) {
        minStops = stopsDiff;
        targetBus = bus;
      }
    }
  });

  return targetBus ? targetBus.vehiNum.slice(-3) : null;
});

// 重新计算离用户最近的站点
const recalculateNearestStation = () => {
  const stations = currentStations.value;
  if (!userLocation.value || stations.length === 0) {
    cachedNearestStation.value = null;
    return;
  }
  let minDist = Infinity;
  let nearestStation = null;
  let nearestIndex = -1;
  stations.forEach((st, index) => {
    const d = Math.pow(st.stationLong - userLocation.value!.lng, 2) + 
              Math.pow(st.stationLat - userLocation.value!.lat, 2);
    if (d < minDist) { minDist = d; nearestStation = st; nearestIndex = index; }
  });
  cachedNearestStation.value = { station: nearestStation, index: nearestIndex, distance: minDist };
  
  // [UX优化] 自动滚动底部列表，把最近的站居中
  nextTick(() => { autoScrollToStation(nearestIndex); });
};

const nearestStationToUser = computed(() => cachedNearestStation.value);

// 当切换线路时，清空选中状态并重新计算最近站点
watch(activeTabId, async () => {
  selectedStationIndex.value = null;
  await nextTick();
  recalculateNearestStation();
});

const selectStation = (index: number) => {
  selectedStationIndex.value = index;
  const st = currentStations.value[index];
  if (st) jumpToCoords(st.stationLat, st.stationLong); // 地图跳转
  
  // 底部列表也滚动居中
  autoScrollToStation(index);
};

// [DOM操作] 自动横向滚动列表到指定站点
const autoScrollToStation = (index: number) => {
  if (!routeScrollRef.value) return;
  
  // 找到对应的 DOM 元素 (依靠id)
  const targetEl = document.getElementById('station-node-' + index);
  if (targetEl) {
    // 浏览器原生API，behavior: 'smooth' 实现平滑滚动
    targetEl.scrollIntoView({ 
      behavior: 'smooth', 
      block: 'nearest', 
      inline: 'center'  // 核心：让该元素在横向视口中居中
    });
  }
};

// [新增] 列表拖拽逻辑（模拟PC端的触摸滑动）
const listDrag = reactive({ startX: 0, startScrollLeft: 0, isDragging: false });

const onListPointerDown = (e: PointerEvent) => {
  if (!routeScrollRef.value) return;
  listDrag.isDragging = true;
  listDrag.startX = e.clientX;
  listDrag.startScrollLeft = routeScrollRef.value.scrollLeft;
  (e.target as HTMLElement).setPointerCapture(e.pointerId);
};

const onListPointerMove = (e: PointerEvent) => {
  if (!listDrag.isDragging || !routeScrollRef.value) return;
  e.preventDefault();
  const deltaX = e.clientX - listDrag.startX;
  // 鼠标往左移(负)，滚动条应该往右滚(正)，所以是减号
  routeScrollRef.value.scrollLeft = listDrag.startScrollLeft - deltaX;
};

const onListPointerUp = (e: PointerEvent) => {
  listDrag.isDragging = false;
  (e.target as HTMLElement).releasePointerCapture(e.pointerId);
};

// 生成顶部的状态文案（如：距xx站约5分钟）
const overallNearestETA = computed(() => {
    if (busList.value.length === 0 || currentStations.value.length === 0) return '当前暂无车辆运行';

    // 1. 如果用户手动选中了站点，显示该站信息
    if (selectedStationIndex.value !== null) {
      const etaData = getStationETA(selectedStationIndex.value);
      const stationName = currentStations.value[selectedStationIndex.value].stationAlias;
      if (etaData) {
        if (etaData.isArriving) return `车辆即将到达 ${stationName}`;
        return `距 ${stationName} 约 ${etaData.text.replace('分', '')} 分钟`;
      } else {
        return `前往 ${stationName} 暂无班次`;
      }
    }

    // 2. 否则，显示离用户最近的站点信息
    if (nearestStationToUser.value) {
      const userStationIndex = nearestStationToUser.value.index;
      const etaData = getStationETA(userStationIndex);
      if (etaData) {
        const stationName = nearestStationToUser.value.station.stationAlias;
        if (etaData.isArriving) return `车辆即将到达 ${stationName}`;
        return `距 ${stationName} 约 ${etaData.text.replace('分', '')} 分钟`;
      }
    }

    // 3. 兜底逻辑：遍历所有站，找一个最近的显示
    let minMinutes = Infinity;
    let found = false;
    currentStations.value.forEach((_, index) => {
        const etaData = getStationETA(index);
        if (etaData) {
            found = true;
            if (etaData.isArriving) { minMinutes = 0; } else {
                const matches = etaData.text.match(/(\d+)/);
                if (matches) { const mins = parseInt(matches[0], 10); if (mins < minMinutes) minMinutes = mins; }
            }
        }
    });

    if (!found) return '等待发车';
    if (minMinutes === 0) return '有车辆即将到站';
    if (minMinutes === Infinity) return '车辆运行中';
    return `最近车辆约 ${minMinutes} 分钟到达`;
})

const getDestinationName = () => {
  const stations = currentStations.value;
  return stations.length > 0 ? stations[stations.length - 1].stationAlias : '终点';
};

const focusBus = (bus: bustype) => { console.log("选中车辆", bus.vehiNum); };

// [API] 获取线路列表
const fetchLinedata = async () => {
  try {
    const res = await fetch(API_URLS.LINE_DATA + '?t=' + Date.now()).then(r => r.json());
    busLineData.value = res.data || [];
    if (busLineData.value.length && activeTabId.value === "L820") {
       activeTabId.value = busLineData.value[0].lid;
    }
    await nextTick();
    recalculateNearestStation();
  } catch(e) {}
};

// [API] 获取车辆位置数据
const fetchBusData = async () => {
  if (activeTabId.value === 'loading') return;
  try {
    const res = await fetch(`${API_URLS.BUS_DATA_PREFIX}${activeTabId.value}.json?t=` + Date.now()).then(r => r.json());
    busList.value = res.data || [];
    lastUpdateTime.value = new Date().toLocaleTimeString('zh-CN', { hour12: false });
  } catch(e) { busList.value = []; }
};

const onTabChange = ({ name }: any) => {
  activeTabId.value = name;
  busList.value = [];
  fetchBusData();
  isPanelOpen.value = true;
};

// 生命周期：挂载后启动轮询
onMounted(() => {
  fetchLinedata();
  fetchBusData();
  getUserLocation(); 
  timer = setInterval(fetchBusData, 3000); // 每3秒刷新一次车辆位置
});
onUnmounted(() => { if (timer) clearInterval(timer); });
</script>

<style scoped>
:deep(.van-tab--active) {
  font-weight: 800 !important;
  font-size: 17px !important;
  transform: scale(1.05);
  transition: all 0.3s ease;
}
:deep(.van-tabs__line) {
  background: linear-gradient(to right, #1989fa, #72c6ff) !important;
  bottom: 6px !important;
  height: 4px !important;
  border-radius: 4px !important;
}
</style>