<template>
  <div class="app-container">

    <!-- 下拉切片容器 ,类is-collapsed表示下拉切片缩回时的样式-->
    <div ref="bottomPanelRef" class="bottom-panel" :class="{ 'is-collapsed': !isPanelOpen }">
      <div class="panel-handle-bar" @click="togglePanel" @touchstart.stop="onPanelTouchStart"
        @touchmove.stop="onPanelTouchMove" @touchend.stop="onPanelTouchEnd">
        <div class="handle"></div>
      </div>

      <div class="tabs-container">
        <van-tabs v-model:active="activeTabId" shrink color="#1989fa" title-active-color="#1989fa"
          title-inactive-color="#999" line-width="20px" line-height="3px" @click-tab="onTabChange" background="#ffffff"
          class="custom-tabs">
          <van-tab v-for="line in busLineData" :key="line.lid" :title="line.lineAlias" :name="line.lid" />
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
            <!-- 校车到达闹钟 -->
            <div class="alarm-controls">
              <label style="display:inline-flex;align-items:center;gap:6px;">
                <input type="checkbox" v-model="alarmEnabled" />
                <span>到站闹钟</span>
              </label>
              <select v-model.number="alarmOffset" style="margin-left:8px;">
                <option :value="0">到站时</option>
                <option :value="1">提前1分钟</option>
                <option :value="3">提前3分钟</option>
                <option :value="5">提前5分钟</option>
                <option :value="10">提前10分钟</option>
              </select>
              <div class="alarm-scheduled" v-if="alarmScheduledText" style="font-size:12px;color:#666;margin-top:4px;">{{ alarmScheduledText }}</div>
            </div>
          </div>
        </div>

        <div class="linear-route-scroll" v-if="currentStations.length > 0" ref="routeScrollRef"
          @pointerdown="onListPointerDown" @pointermove="onListPointerMove" @pointerup="onListPointerUp"
          @pointerleave="onListPointerUp">
          <div class="linear-route-track">
            <div class="route-line-bg"></div>
            <div v-for="(station, index) in currentStations" :key="'node_' + index" class="route-node" :class="{
              'is-nearest': nearestStationToUser?.index === index, // 离人最近的站
              'is-selected': selectedStationIndex === index        // 选中的站
            }" :id="'station-node-' + index" @click="selectStation(index)">
              <div class="node-dot-wrapper">
                <div class="node-dot"></div>
                <div class="node-dot-ring" v-if="selectedStationIndex === index"></div>
                <div class="user-location-badge"
                  v-if="nearestStationToUser?.index === index && selectedStationIndex === null">
                  <van-icon name="location" />
                </div>
              </div>

              <div class="node-name">
                {{ station.stationAlias }}
              </div>

              <div class="node-buses-container-bottom">
                <div v-for="bus in getBusesNearStation(index)" :key="bus.vehiNum" class="bus-on-route-icon"
                  @click.stop="focusBus(bus)">
                  <div class="css-side-bus-mini" :class="isSmallCar(bus.vehicleType) ? 'side-red' : 'side-white'">
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
    <!-- 地图容器 -->
    <div class="map-container" ref="mapContainerRef" :style="getMapContainerHeight" @pointerdown="onPointerDown"
      @pointermove="onPointerMove" @pointerup="onPointerUp" @pointerleave="onPointerUp" @wheel.prevent="onWheel">

      <div v-if="debugLocation" class="location-debug-panel" style="position: absolute; right: 12px; top: 12px; background: rgba(0,0,0,0.6); color: #fff; padding: 8px 10px; border-radius: 6px; font-size: 12px; z-index:200; min-width:180px;">
        <div style="font-weight:600; margin-bottom:6px;">定位调试</div>
        <div>支持定位: <strong>{{ locationDebug.supported ? '✓' : '✗' }}</strong></div>
        <div>请求已发送: <strong>{{ locationDebug.requestSent ? '✓' : '✗' }}</strong></div>
        <div>定位成功: <strong>{{ locationDebug.success ? '✓' : '✗' }}</strong></div>
        <div>定位失败: <strong>{{ locationDebug.failure ? '✓' : '✗' }}</strong></div>
        <div>坐标转换: <strong>{{ locationDebug.conversionDone ? '✓' : '✗' }}</strong></div>
        <div>重算最近站: <strong>{{ locationDebug.recalcDone ? '✓' : '✗' }}</strong></div>
        <div>已跳转视野: <strong>{{ locationDebug.jumped ? '✓' : '✗' }}</strong></div>
        <div v-if="locationDebug.lastError" style="margin-top:6px;color:#ffcccc;word-break:break-word;">错误: {{ locationDebug.lastError }}</div>
      </div>

      <!-- 背景图层 -->
      <div class="map-wrapper" :class="{ 'is-animating': isAnimating }" :style="wrapperStyle">
        <img ref="mapImgRef" src="/zjgMap.png" class="map-image" alt="Map" draggable="false" @load="initMap" />

        <svg class="map-overlay" viewBox="0 0 1000 1000" preserveAspectRatio="none">
          <polyline v-if="currentLinePoints.length > 0" :points="svgPolylinePoints" fill="none" stroke="#1989fa"
            stroke-width="8" stroke-opacity="0.6" stroke-linecap="round" stroke-linejoin="round"
            vector-effect="non-scaling-stroke" />
        </svg>

        <div v-if="userLocation" class="user-marker" :style="getMarkerStyle(userLocation.lat, userLocation.lng, userHeading)">
          <div class="user-rotate" :style="{ transform: `rotate(${userHeading}deg)` }">
            <svg class="user-arrow" viewBox="0 0 24 24" width="36" height="36" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2 L20 20 L12 16 L4 20 Z" fill="#1989fa" stroke="#ffffff" stroke-width="0.6" stroke-linejoin="round" />
            </svg>
          </div>
        </div>

        <!-- 生成站点 -->
        <div v-for="(station, index) in currentStations" :key="'map_st_' + index" class="station-marker"
          :style="getMarkerStyle(station.stationLat, station.stationLong)" >
          <div class="station-dot" :class="{ 'is-selected': selectedStationIndex === index }" @click.stop="selectStation(index)"></div>
        </div>
        <!-- 生成车辆图标 -->
        <div v-for="bus in busList" :key="'map_bus_' + bus.vehiNum" class="bus-marker"
          :style="getMarkerStyle(bus.py, bus.px, bus.direction)" @click.stop="focusBus(bus)">
          <div class="bus-rotate-container" :style="{ transform: `rotate(${bus.direction}deg)` }">
            <div class="school-bus-icon" :class="isSmallCar(bus.vehicleType) ? 'bus-red' : 'bus-white'">
              <div class="bus-windshield"></div>
              <div class="bus-roof"></div>
              <div class="bus-lights-l"></div>
              <div class="bus-lights-r"></div>
            </div>
          </div>
          <!-- 显示车牌号后三位 -->
          <div class="bus-label">{{ bus.vehiNum.slice(-3) }}</div>
        </div>
      </div>
      <!-- 地图控件:缩放以及重置地图,重新定位 -->
      <div class="map-controls" :class="{ 'shifted': isPanelOpen }">
        <div class="control-btn" @click.stop="zoomIn"><van-icon name="plus" /></div>
        <div class="control-btn" @click.stop="zoomOut"><van-icon name="minus" /></div>
        <div class="control-btn" @click.stop="resetMap"><van-icon name="aim" /></div>
        <div class="control-btn" @click.stop="getUserLocation" :class="{ 'active': userLocation }">
          <van-icon name="location-o" />
        </div>
          <div class="control-btn debug-toggle" @click.stop="debugLocation = !debugLocation" :class="{ 'active': debugLocation }" title="Toggle location debug">
            <van-icon name="info-o" />
          </div>
      </div>
    </div>



  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, reactive, nextTick, watch } from 'vue';
import { showToast } from 'vant';
import type { bustype, linetype } from './datatype';
import { get } from 'vant/lib/utils';

// [配置] 地图的经纬度边界 (左上角和右下角)，用于将GPS映射到图片百分比
const MAP_BOUNDS = { minLon: 120.064, maxLon: 120.097, minLat: 30.28765, maxLat: 30.315849 };
const activeTabId = ref<any>("L820"); // 当前选中的线路ID
const API_URLS = { LINE_DATA: '/bus_line_data.json', BUS_DATA_PREFIX: '/' };

const defaultUserLocation = { lat: 30.2975, lng: 120.0800 }; // 出生点:马院
// [状态] 核心数据 Refs
const busLineData = ref<linetype[]>([]); // 线路列表
const busList = ref<bustype[]>([]);      // 车辆实时数据
const lastUpdateTime = ref<string>('');  // 上次刷新时间
const isPanelOpen = ref(true);           // 底部面板是否展开
const userLocation = ref<{ lat: number, lng: number }>(defaultUserLocation); // 用户GPS坐标
// 朝向相关：raw->offset->平滑 -> 展示
const userHeading = ref<number>(0); // 最终用于模板显示的朝向（度）
const initialHeadingOffset = ref<number>(0); // 不同设备可能需要的初始偏移（度），可根据UA设定
const _smoothedHeading = { value: 0 }; // 内部平滑缓存（避免频繁触发 ref 更改开销）
const HEADING_SMOOTHING_ALPHA = 0.28; // EMA 平滑系数，0-1，越小越平滑

// 根据 userAgent 做一个简单设备型号->偏移的映射（经验值，可扩展）
const determineInitialOffsetFromUA = (ua: string) => {
  const u = ua.toLowerCase();
  // 常见厂商示例（仅经验性调整）：
  if (/huawei|honor/.test(u)) return -90;
  if (/xiaomi|mi |redmi/.test(u)) return -90;
  if (/oppo|realme|oneplus/.test(u)) return -90;
  if (/iphone|ipad|ipod/.test(u)) return 0; // iOS 通常 alpha 定义与安卓不同，保守使用0
  // 默认不偏移
  return -90;
};

// 设备朝向处理函数：读取 e.alpha，应用偏移并做 EMA 平滑，写入 userHeading
const handleDeviceOrientation = (e: DeviceOrientationEvent) => {
  if (typeof e.alpha !== 'number' || isNaN(e.alpha)) return;
  // 原始 alpha 表示设备绕 Z 轴的角度（0-360），不同浏览器参考系差异很大
  // 把 alpha 转为页面上希望的指向角：先取反（360 - alpha），再加上经验偏移
  let raw = (360 - e.alpha + 360) % 360; // 规范到 [0,360)
  raw = (raw + initialHeadingOffset.value + 360) % 360;

  // EMA 平滑（避免抖动）
  const prev = _smoothedHeading.value || raw;
  const alpha = HEADING_SMOOTHING_ALPHA;
  const sm = prev * (1 - alpha) + raw * alpha;
  _smoothedHeading.value = sm;
  userHeading.value = Math.round(sm * 100) / 100; // 保留两位小数
};
// Debug: whether to show location debug overlay
const debugLocation = ref(false);
const locationDebug = reactive({
  supported: false,
  requestSent: false,
  success: false,
  failure: false,
  conversionDone: false,
  recalcDone: false,
  jumped: false,
  lastError: '' as string
});
const cachedNearestStation = ref<{ station: any, index: number, distance: number } | null>(null); // 缓存的最近站点
const selectedStationIndex = ref<number | null>(null); // 用户手动点击选中的站点索引
const bottomPanelRef = ref<HTMLElement | null>(null);

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
// 用于双指缩放的状态
const activePointers = new Map<number, { x: number, y: number }>();
let initialDistance = 0;
let initialScale = 1;
let initialPinchMidpoint = { x: 0, y: 0 }; // 记录缩放开始时，中心点在地图上的坐标

let naturalWidth = 0; let naturalHeight = 0; // 图片原始尺寸
let containerWidth = 0; let containerHeight = 0; // 容器显示尺寸
let minScale = 1; // 最小缩放比例（填满屏幕）

const bottomPanelHeight = ref(0);

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
  // 获取图片和容器尺寸
  naturalWidth = mapImgRef.value.naturalWidth;
  naturalHeight = mapImgRef.value.naturalHeight;
  containerWidth = window.innerWidth;
  containerHeight = window.innerHeight - 280.98 + 25; // 初始时减去底部面板高度
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
  updateBottomPanelHeight();
  updateContainerSize();

  if (naturalWidth > 0) {
    // 重新计算最小缩放比，防止窗口变大后出现白边
    updateBoundary();
  }
});




// 更新底部面板高度
const updateBottomPanelHeight = async () => {
  // 等待 DOM 更新（特别是涉及到 v-if 或 class 切换导致的动画）
  await nextTick();

  if (bottomPanelRef.value) {
    // 使用 offsetHeight 获取当前元素在屏幕上的实际高度
    bottomPanelHeight.value = bottomPanelRef.value.offsetHeight;
  }
};
const getMapContainerHeight = computed(() => ({
  height: `calc(100% - ${bottomPanelHeight.value}px + 25px)`
}));





// [地图方法] 计算拖拽边界限制
const getLimits = () => {
  const currentW = naturalWidth * mapState.scale;
  const currentH = naturalHeight * mapState.scale;
  // 计算允许滑动的最大距离
  const limitX = Math.max(0, (currentW - containerWidth) / 2);
  const limitY = Math.max(0, (currentH - containerHeight) / 2);
  const OVERSCROLL = 0; // 允许超出边界的弹性距离
  
  return {
    limitX: limitX + OVERSCROLL,
    limitY: limitY + OVERSCROLL
  };
};

// [交互] 按下鼠标/手指
const onPointerDown = (e: PointerEvent) => {
  activePointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
  (e.target as HTMLElement).setPointerCapture(e.pointerId);

  if (activePointers.size === 1) {
    // 单指逻辑：记录起始点用于拖拽
    isDragging.value = true;
    isAnimating.value = false;
    dragStart.x = e.clientX;
    dragStart.y = e.clientY;
    mapStart.x = mapState.x;
    mapStart.y = mapState.y;
    pointerDownPos.x = e.clientX;
    pointerDownPos.y = e.clientY;
  } else if (activePointers.size === 2) {
    // 双指逻辑：记录初始间距和地图参考中心点
    isDragging.value = false;
    const points = Array.from(activePointers.values());
    initialDistance = Math.hypot(points[0].x - points[1].x, points[0].y - points[1].y);
    initialScale = mapState.scale;

    // 计算双指中点在屏幕上的坐标
    const screenMidX = (points[0].x + points[1].x) / 2;
    const screenMidY = (points[0].y + points[1].y) / 2;

    // 计算该中点在地图图片内容上的相对坐标（以地图中心为原点）
    initialPinchMidpoint = {
      x: (screenMidX - containerWidth / 2 - mapState.x) / mapState.scale,
      y: (screenMidY - containerHeight / 2 - mapState.y) / mapState.scale
    };
  }
};
/**
 * 阻尼计算函数
 * @param current 当前计算出的位移值 (newX 或 newY)
 * @param limit 允许的最大物理边界 (limitX 或 limitY)
 * @returns 经过阻尼处理后的位移值
 */
const applyDamping = (current: number, limit: number): number => {
  if (current > limit) {
    return limit + Math.pow(current - limit, 0.7);
  } else if (current < -limit) {
    return -limit - Math.pow(-limit - current, 0.7);
  }
  return current;
};
// [交互] 移动鼠标/手指
const onPointerMove = (e: PointerEvent) => {
  if (!activePointers.has(e.pointerId)) return;
  activePointers.set(e.pointerId, { x: e.clientX, y: e.clientY });

  // --- 双指缩放逻辑 ---
  if (activePointers.size === 2) {
    e.preventDefault();
    const points = Array.from(activePointers.values());
    const currentDistance = Math.hypot(points[0].x - points[1].x, points[0].y - points[1].y);
    
    let newScale = initialScale * (currentDistance / initialDistance);
    newScale = Math.max(minScale, Math.min(newScale, 4.0));

    const currentScreenMidX = (points[0].x + points[1].x) / 2;
    const currentScreenMidY = (points[0].y + points[1].y) / 2;

    // 更新坐标，使中心点对齐
    mapState.x = currentScreenMidX - containerWidth / 2 - initialPinchMidpoint.x * newScale;
    mapState.y = currentScreenMidY - containerHeight / 2 - initialPinchMidpoint.y * newScale;
    
    mapState.scale = newScale;
    isAnimating.value = false;
  } 
  // --- 单指拖拽逻辑 ---
  else if (activePointers.size === 1 && isDragging.value) {
    e.preventDefault();
    const { limitX, limitY } = getLimits();

    // 1. 计算原始目标位移
    const targetX = mapStart.x + (e.clientX - dragStart.x);
    const targetY = mapStart.y + (e.clientY - dragStart.y);

    // 2. 调用拆分出的阻尼函数
    mapState.x = applyDamping(targetX, limitX);
    mapState.y = applyDamping(targetY, limitY);
  }
};

// [交互] 松开鼠标/手指
const onPointerUp = (e: PointerEvent) => {
  activePointers.delete(e.pointerId);

  if (activePointers.size === 0) {
    isDragging.value = false;
    (e.target as HTMLElement).releasePointerCapture(e.pointerId);
    checkBoundsAndSnap(); // 抬起时进行最终边界回弹

    const dist = Math.hypot(e.clientX - pointerDownPos.x, e.clientY - pointerDownPos.y)
  } else if (activePointers.size === 1) {
    // 关键：如果从双指变为单指，需要重置单指拖拽的起点，否则画面会闪跳
    const remaining = activePointers.values().next().value;
    dragStart.x = remaining.x;
    dragStart.y = remaining.y;
    mapStart.x = mapState.x;
    mapStart.y = mapState.y;
    isDragging.value = true;
  }
};


const updateBoundary = () => {
  const scaleX = containerWidth / naturalWidth;
  const scaleY = containerHeight / naturalHeight;
  minScale = Math.max(scaleX, scaleY);
  if (mapState.scale < minScale) {
    mapState.scale = minScale;
    checkBoundsAndSnap();
  }
}
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
// 坐标系转换：WGS-84 <-> GCJ-02（中国）
// 这里实现 WGS-84 -> GCJ-02 的转换，用于把浏览器返回的坐标（通常为 WGS-84）
// 转换为与后端/底图一致的坐标系（若后端/底图使用 GCJ-02）。
const PI = 3.14159265358979324;
const a = 6378245.0;
const ee = 0.00669342162296594323;
const outOfChina = (lat: number, lon: number) => {
  return lon < 72.004 || lon > 137.8347 || lat < 0.8293 || lat > 55.8271;
};
const transformLat = (x: number, y: number) => {
  let ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * Math.sqrt(Math.abs(x));
  ret += (20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0 / 3.0;
  ret += (20.0 * Math.sin(y * PI) + 40.0 * Math.sin(y / 3.0 * PI)) * 2.0 / 3.0;
  ret += (160.0 * Math.sin(y / 12.0 * PI) + 320 * Math.sin(y * PI / 30.0)) * 2.0 / 3.0;
  return ret;
};
const transformLon = (x: number, y: number) => {
  let ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * Math.sqrt(Math.abs(x));
  ret += (20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0 / 3.0;
  ret += (20.0 * Math.sin(x * PI) + 40.0 * Math.sin(x / 3.0 * PI)) * 2.0 / 3.0;
  ret += (150.0 * Math.sin(x / 12.0 * PI) + 300.0 * Math.sin(x / 30.0 * PI)) * 2.0 / 3.0;
  return ret;
};
const wgs84ToGcj02 = (lon: number, lat: number): [number, number] => {
  if (outOfChina(lat, lon)) return [lon, lat];
  let dLat = transformLat(lon - 105.0, lat - 35.0);
  let dLon = transformLon(lon - 105.0, lat - 35.0);
  const radLat = lat / 180.0 * PI;
  let magic = Math.sin(radLat);
  magic = 1 - ee * magic * magic;
  const sqrtMagic = Math.sqrt(magic);
  dLat = (dLat * 180.0) / ((a * (1 - ee)) / (magic * sqrtMagic) * PI);
  dLon = (dLon * 180.0) / (a / sqrtMagic * Math.cos(radLat) * PI);
  const mgLat = lat + dLat;
  const mgLon = lon + dLon;
  return [mgLon, mgLat];
};

const getUserLocation = async () => {
  // reset debug statuses
  locationDebug.supported = false;
  locationDebug.requestSent = false;
  locationDebug.success = false;
  locationDebug.failure = false;
  locationDebug.conversionDone = false;
  locationDebug.recalcDone = false;
  locationDebug.jumped = false;
  locationDebug.lastError = '';

  locationDebug.supported = !!navigator.geolocation;
  if (!locationDebug.supported) {
    showToast('浏览器不支持定位');
    locationDebug.failure = true;
    return;
  }

  // 如果需要，在用户手势内请求 DeviceOrientation 权限（iOS 13+）
  try {
    const req = (DeviceOrientationEvent as any)?.requestPermission;
    if (typeof req === 'function') {
      try {
        const perm = await req();
        if (perm === 'granted') {
          try { window.addEventListener('deviceorientation', handleDeviceOrientation as EventListener, true); } catch (e) { }
        } else {
          locationDebug.lastError = 'DeviceOrientation 权限未授予';
        }
      } catch (e) {
        // requestPermission 可能在某些浏览器抛错
      }
    }
  } catch (e) { }

  showToast('正在定位...');
  locationDebug.requestSent = true;
  navigator.geolocation.getCurrentPosition(
    (position) => {
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;
      // 浏览器通常返回 WGS-84，经常需要转换为 GCJ-02（中国范围）以和后端/底图对齐
      const [convLng, convLat] = wgs84ToGcj02(lng, lat);
      locationDebug.conversionDone = true;
      userLocation.value = { lat: convLat, lng: convLng };
      locationDebug.success = true;
      showToast('定位成功');
      recalculateNearestStation(); // 定位成功后，算一下离哪个站最近
      locationDebug.recalcDone = true;
      if (cachedNearestStation.value) {
        selectedStationIndex.value = cachedNearestStation.value.index;
      }
      // 跳转到用户位置并记录
      jumpToUserLocation();
    },
    (error) => {
      console.error(error);
      locationDebug.failure = true;
      // Map GeolocationPositionError codes to friendly messages
      let friendly = '定位失败';
      try {
        if (error && typeof error.code === 'number') {
          // 1: PERMISSION_DENIED, 2: POSITION_UNAVAILABLE, 3: TIMEOUT
          if (error.code === 1) friendly = '定位被拒绝，请允许定位权限';
          else if (error.code === 2) friendly = '位置信息不可用';
          else if (error.code === 3) friendly = '定位超时，请重试';
        }
      } catch (e) { /* ignore */ }

      const detailed = error?.message ? `${friendly}: ${error.message}` : friendly;
      locationDebug.lastError = detailed;
      // show a more informative toast for the user
      showToast(detailed);
    },
    { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 }
  );
};

const jumpToUserLocation = () => {
  if (!userLocation.value) return;
  jumpToCoords(userLocation.value.lat, userLocation.value.lng);
  // record that a jump happened (for debug overlay)
  locationDebug.jumped = true;
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
  if (distance > 50 && isPanelOpen.value) changePanelState();
  else if (distance < -50 && !isPanelOpen.value) changePanelState();

};
const changePanelState = () => {
  isPanelOpen.value = !isPanelOpen.value;
};
const togglePanel = () => {
  changePanelState();
};
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

  if(nearestIndex!=-1)
  selectStation(nearestIndex)
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
  // 1. 更新选中索引，触发 CSS 高亮
  selectedStationIndex.value = index;
  
  const st = currentStations.value[index];
  if (st) {
    // 2. 地图跳转：将该站点移动到视野中心
    jumpToCoords(st.stationLat, st.stationLong);
  }

  // 3. 面板连动：确保面板处于展开状态，并滚动到对应位置
  isPanelOpen.value = true;
  
  // 使用 nextTick 确保 DOM 更新（比如面板展开动画）后再执行滚动
  nextTick(() => {
    updateBottomPanelHeight(); // 更新容器高度计算
    autoScrollToStation(index); // 调用你已有的 scrollIntoView 逻辑
  });
};

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

// --- 校车到达闹钟 (Alarm) ---
const alarmEnabled = ref<boolean>(false);
const alarmOffset = ref<number>(3); // minutes before arrival
let alarmTimerId: number | null = null;
const alarmScheduledAt = ref<number | null>(null);

const getTargetStationIndex = () => {
  if (selectedStationIndex.value !== null) return selectedStationIndex.value;
  if (nearestStationToUser.value) return nearestStationToUser.value.index;
  return null;
};

const computeEtaMinutes = (): number | null => {
  const idx = getTargetStationIndex();
  if (idx === null || idx === undefined) return null;
  const eta = getStationETA(idx as number);
  if (!eta) return null;
  if (eta.isArriving) return 0;
  const matches = eta.text.match(/(\d+)/);
  return matches ? parseInt(matches[0], 10) : null;
};

const clearAlarmTimer = () => {
  if (alarmTimerId !== null) {
    clearTimeout(alarmTimerId);
    alarmTimerId = null;
  }
  alarmScheduledAt.value = null;
};

const playAlarmSound = () => {
  try {
    const AC = (window.AudioContext || (window as any).webkitAudioContext);
    if (!AC) return;
    const ac = new AC();
    const o = ac.createOscillator();
    const g = ac.createGain();
    o.type = 'sine';
    o.frequency.value = 880;
    o.connect(g);
    g.connect(ac.destination);
    g.gain.value = 0.0001;
    o.start();
    g.gain.exponentialRampToValueAtTime(0.2, ac.currentTime + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, ac.currentTime + 2.0);
    setTimeout(() => { try { o.stop(); ac.close(); } catch (e) { } }, 2100);
  } catch (e) { }
};

const triggerAlarm = (message?: string) => {
  const msg = message || '校车即将到站，请准备乘车';
  try {
    if (Notification && Notification.permission === 'granted') {
      new Notification('校车提醒', { body: msg });
    } else {
      showToast(msg);
    }
  } catch (e) { showToast(msg); }
  try { if (navigator.vibrate) navigator.vibrate([200, 100, 200]); } catch (e) {}
  playAlarmSound();
  // disable after trigger
  alarmEnabled.value = false;
  clearAlarmTimer();
};

const scheduleAlarm = () => {
  clearAlarmTimer();
  if (!alarmEnabled.value) return;
  const etaMin = computeEtaMinutes();
  if (etaMin === null) return;
  const delayMs = Math.max(0, etaMin * 60 * 1000 - alarmOffset.value * 60 * 1000);
  const scheduledAt = Date.now() + delayMs;
  alarmScheduledAt.value = scheduledAt;
  if (delayMs <= 0) {
    // already within offset window -> trigger immediately
    setTimeout(() => triggerAlarm(), 200);
    return;
  }
  alarmTimerId = window.setTimeout(() => {
    triggerAlarm();
  }, delayMs) as unknown as number;
};

const requestNotificationIfNeeded = async () => {
  try {
    if (!('Notification' in window)) return;
    if (Notification.permission === 'default') {
      await Notification.requestPermission();
    }
  } catch (e) { }
};

const alarmScheduledText = computed(() => {
  if (!alarmScheduledAt.value) return '';
  const d = new Date(alarmScheduledAt.value);
  return `提醒时间: ${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}`;
});

// watch for changes to reschedule
watch([() => alarmEnabled.value, () => alarmOffset.value, () => selectedStationIndex.value, () => nearestStationToUser.value, () => busList.value.length], async () => {
  if (alarmEnabled.value) await requestNotificationIfNeeded();
  scheduleAlarm();
});

onUnmounted(() => {
  clearAlarmTimer();
});

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
  } catch (e) { }
};

// [API] 获取车辆位置数据
const fetchBusData = async () => {
  if (activeTabId.value === 'loading') return;
  try {
    const res = await fetch(`${API_URLS.BUS_DATA_PREFIX}${activeTabId.value}.json?t=` + Date.now()).then(r => r.json());
    busList.value = res.data || [];
    lastUpdateTime.value = new Date().toLocaleTimeString('zh-CN', { hour12: false });
  } catch (e) { busList.value = []; }
};

const onTabChange = ({ name }: any) => {
  activeTabId.value = name;
  busList.value = [];
  fetchBusData();
  isPanelOpen.value = true;
};

// 生命周期：挂载后启动轮询
onMounted(() => {
  // 根据 UA 设定初始偏移（经验值）
  try { initialHeadingOffset.value = determineInitialOffsetFromUA(navigator.userAgent || ''); } catch (e) { initialHeadingOffset.value = 0; }
  fetchLinedata();
  fetchBusData();
  getUserLocation();
  updateBottomPanelHeight();
  if (mapImgRef.value && mapImgRef.value.complete) {
    initMap();
  }
  // 核心：使用 ResizeObserver 自动监听 面板高度 变化
  // 这样无论你是展开面板、内容变多、还是切换 Tab，高度都会自动同步
  if (bottomPanelRef.value) {
    const observer = new ResizeObserver(() => {
      updateBottomPanelHeight();
    });
    observer.observe(bottomPanelRef.value);
  }
  if (mapContainerRef.value) {
    const MapObserver = new ResizeObserver(() => {
      updateContainerSize();
      updateBoundary();
    });
    MapObserver.observe(mapContainerRef.value);
  }
  timer = setInterval(fetchBusData, 3000); // 每3秒刷新一次车辆位置
  // 只有在非 iOS requestPermission 场景下直接注册监听，iOS 13+ 需要在用户手势内 requestPermission
  try {
    if (!(DeviceOrientationEvent as any)?.requestPermission) {
      window.addEventListener('deviceorientation', handleDeviceOrientation as EventListener, true);
    }
  } catch (err) { }
});
onUnmounted(() => {
  if (timer) clearInterval(timer);
  try { window.removeEventListener('deviceorientation', handleDeviceOrientation as EventListener, true); } catch (e) { }
});
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

/* User arrow marker styles */
.user-marker {
  position: absolute;
  transform: translate(-50%, -50%);
  pointer-events: none;
}
.user-rotate {
  transform-origin: 50% 60%; /* lower than center so arrow pivot feels natural */
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.user-arrow {
  filter: drop-shadow(0 1px 4px rgba(0,0,0,0.25));
}
</style>