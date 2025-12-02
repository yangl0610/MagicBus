<template>
  <div class="app-container">
    
    <!-- 1. 地图层 -->
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

        <!-- 用户定位点 -->
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
          <!-- 地图上的站点点 -->
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

    <!-- 2. 底部悬浮面板 -->
    <div 
      class="bottom-panel" 
      :class="{ 'is-collapsed': !isPanelOpen }"
      @touchstart="onPanelTouchStart"
      @touchmove="onPanelTouchMove"
      @touchend="onPanelTouchEnd"
    >
      <div class="panel-handle-bar" @click="togglePanel">
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
        <!-- 线路信息头 -->
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
             <!-- [修改] 替换了换向按钮，显示最近车辆信息 -->
             <div class="nearest-bus-box" v-if="nearestBusInfo">
               <span class="nb-label">最近车辆</span>
               <span class="nb-plate">{{ nearestBusInfo }}</span>
             </div>
             <div class="nearest-bus-box empty" v-else>
               <span class="nb-label">暂无车辆</span>
             </div>
           </div>
        </div>

        <div class="linear-route-scroll" v-if="currentStations.length > 0">
          <div class="linear-route-track">
            <div class="route-line-bg"></div>
            <div 
              v-for="(station, index) in currentStations" 
              :key="'node_' + index" 
              class="route-node"
              :class="{ 
                'is-nearest': nearestStationToUser?.index === index,
                'is-selected': selectedStationIndex === index
              }"
              @click="selectStation(index)"
            >
              <div class="node-dot-wrapper">
                <div class="node-dot"></div>
                <!-- 定位图标：仅当没有手动选择站点时，才显示定位标，避免视觉冲突 -->
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

const MAP_BOUNDS = { minLon: 120.0665, maxLon: 120.0961, minLat:30.2910, maxLat: 30.3148 };
const activeTabId = ref<any>("L820");
const API_URLS = { LINE_DATA: '/bus_line_data.json', BUS_DATA_PREFIX: '/' };

const busLineData = ref<linetype[]>([]);
const busList = ref<bustype[]>([]);
const lastUpdateTime = ref<string>('');
const isPanelOpen = ref(true);
const userLocation = ref<{ lat: number, lng: number } | null>(null);
const cachedNearestStation = ref<{ station: any, index: number, distance: number } | null>(null);
const selectedStationIndex = ref<number | null>(null);

let timer: number | null = null;

// --- 地图状态 ---
const mapContainerRef = ref<HTMLElement | null>(null);
const mapImgRef = ref<HTMLImageElement | null>(null);
const mapState = reactive({ scale: 1, x: 0, y: 0 });
const isDragging = ref(false);
const isAnimating = ref(false);
const dragStart = reactive({ x: 0, y: 0 });
const mapStart = reactive({ x: 0, y: 0 });
const pointerDownPos = reactive({ x: 0, y: 0 });

let naturalWidth = 0; let naturalHeight = 0; let containerWidth = 0; let containerHeight = 0; let minScale = 1;
const panelTouch = reactive({ startY: 0, moving: false });

const wrapperStyle = computed(() => ({
  transform: `translate(calc(-50% + ${mapState.x}px), calc(-50% + ${mapState.y}px)) scale(${mapState.scale})`,
  transition: isAnimating.value ? 'transform 0.4s cubic-bezier(0.25, 1, 0.5, 1)' : 'none' 
}));

const initMap = () => {
  if (!mapImgRef.value || !mapContainerRef.value) return;
  naturalWidth = mapImgRef.value.naturalWidth;
  naturalHeight = mapImgRef.value.naturalHeight;
  updateContainerSize();
  const scaleX = containerWidth / naturalWidth;
  const scaleY = containerHeight / naturalHeight;
  minScale = Math.max(scaleX, scaleY);
  mapState.scale = minScale;
  checkBoundsAndSnap();
};

const updateContainerSize = () => {
  if (mapContainerRef.value) {
    containerWidth = mapContainerRef.value.clientWidth;
    containerHeight = mapContainerRef.value.clientHeight;
  }
};

window.addEventListener('resize', () => {
  updateContainerSize();
  if (naturalWidth > 0) {
     const scaleX = containerWidth / naturalWidth;
     const scaleY = containerHeight / naturalHeight;
     minScale = Math.max(scaleX, scaleY);
     if (mapState.scale < minScale) {
        mapState.scale = minScale;
        checkBoundsAndSnap();
     }
  }
});

const getLimits = () => {
  const currentW = naturalWidth * mapState.scale;
  const currentH = naturalHeight * mapState.scale;
  const limitX = Math.max(0, (currentW - containerWidth) / 2);
  const limitY = Math.max(0, (currentH - containerHeight) / 2);
  return { limitX, limitY };
};

const onPointerDown = (e: PointerEvent) => {
  isDragging.value = true;
  isAnimating.value = false;
  dragStart.x = e.clientX;
  dragStart.y = e.clientY;
  mapStart.x = mapState.x;
  mapStart.y = mapState.y;
  pointerDownPos.x = e.clientX;
  pointerDownPos.y = e.clientY;
  (e.target as HTMLElement).setPointerCapture(e.pointerId);
};

const onPointerMove = (e: PointerEvent) => {
  if (!isDragging.value) return;
  e.preventDefault();
  const deltaX = e.clientX - dragStart.x;
  const deltaY = e.clientY - dragStart.y;
  let newX = mapStart.x + deltaX;
  let newY = mapStart.y + deltaY;
  const { limitX, limitY } = getLimits();
  if (newX > limitX) newX = limitX + Math.pow(newX - limitX, 0.7);
  else if (newX < -limitX) newX = -limitX - Math.pow(-limitX - newX, 0.7);
  if (newY > limitY) newY = limitY + Math.pow(newY - limitY, 0.7);
  else if (newY < -limitY) newY = -limitY - Math.pow(-limitY - newY, 0.7);
  mapState.x = newX;
  mapState.y = newY;
};

const onPointerUp = (e: PointerEvent) => {
  isDragging.value = false;
  (e.target as HTMLElement).releasePointerCapture(e.pointerId);
  checkBoundsAndSnap();
  const dist = Math.hypot(e.clientX - pointerDownPos.x, e.clientY - pointerDownPos.y);
  if (dist < 5) onMapClick();
};

const onMapClick = () => {
  if (isPanelOpen.value) {
    isPanelOpen.value = false;
    selectedStationIndex.value = null; 
  }
};

const checkBoundsAndSnap = () => {
  const { limitX, limitY } = getLimits();
  let targetX = mapState.x;
  let targetY = mapState.y;
  let needsSnap = false;
  if (mapState.x > limitX) { targetX = limitX; needsSnap = true; } 
  else if (mapState.x < -limitX) { targetX = -limitX; needsSnap = true; }
  if (mapState.y > limitY) { targetY = limitY; needsSnap = true; } 
  else if (mapState.y < -limitY) { targetY = -limitY; needsSnap = true; }
  if (needsSnap) {
    isAnimating.value = true;
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
  if (newScale < minScale) newScale = minScale;
  if (newScale > 4.0) newScale = 4.0;
  mapState.scale = newScale;
  nextTick(() => { checkBoundsAndSnap(); });
};

const zoomIn = () => applyZoom(0.2);
const zoomOut = () => applyZoom(-0.2);
const resetMap = () => {
  isAnimating.value = true;
  mapState.scale = minScale;
  mapState.x = 0;
  mapState.y = 0;
};

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
      recalculateNearestStation();
      jumpToUserLocation();
    },
    (error) => {
      console.error(error);
      showToast('定位失败，请检查权限');
    }
  );
};

const jumpToUserLocation = () => {
  if (!userLocation.value) return;
  const { x: percentX, y: percentY } = geoToPercent(userLocation.value.lat, userLocation.value.lng);
  
  if (percentX < -50 || percentX > 150 || percentY < -50 || percentY > 150) {
    showToast('当前位置不在校车运行范围内');
    return;
  }

  const currentW = naturalWidth * mapState.scale;
  const currentH = naturalHeight * mapState.scale;
  
  const targetX = ((50 - percentX) / 100) * currentW;
  const targetY = ((50 - percentY) / 100) * currentH;

  isAnimating.value = true;
  mapState.x = targetX;
  mapState.y = targetY;
  
  nextTick(() => {
    checkBoundsAndSnap();
  });
};

const isSmallCar = (type: any) => String(type) === '3';

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
  if (distance > 50 && isPanelOpen.value) isPanelOpen.value = false;
  else if (distance < -50 && !isPanelOpen.value) isPanelOpen.value = true;
};
const togglePanel = () => { isPanelOpen.value = !isPanelOpen.value; };

const geoToPercent = (lat: number, lon: number) => {
  const x = ((lon - MAP_BOUNDS.minLon) / (MAP_BOUNDS.maxLon - MAP_BOUNDS.minLon)) * 100;
  const y = ((MAP_BOUNDS.maxLat - lat) / (MAP_BOUNDS.maxLat - MAP_BOUNDS.minLat)) * 100; 
  return { x, y };
};

const getMarkerStyle = (lat: number, lon: number, direction?: number) => {
  const { x, y } = geoToPercent(lat, lon);
  return { left: `${x}%`, top: `${y}%`, zIndex: direction !== undefined ? 20 : 10 };
};

const currentLineData = computed(() => busLineData.value.find(l => String(l.lid) === String(activeTabId.value)));
const currentStations = computed(() => currentLineData.value?.stationList || []);
const currentPoints = computed(() => currentLineData.value?.pointList || []);
const currentLinePoints = computed(() => currentPoints.value);

const svgPolylinePoints = computed(() => {
  return currentLinePoints.value.map(p => {
    const { x, y } = geoToPercent(p.py, p.px); 
    return `${x * 10},${y * 10}`;
  }).join(' ');
});

const getBusesNearStation = (stationIndex: number) => {
  const station = currentStations.value[stationIndex];
  if (!station) return [];
  return busList.value.filter(bus => {
    let minD = Infinity;
    let closestIdx = -1;
    currentStations.value.forEach((st, idx) => {
      const d = Math.pow(bus.px - st.stationLong, 2) + Math.pow(bus.py - st.stationLat, 2);
      if (d < minD) { minD = d; closestIdx = idx; }
    });
    return closestIdx === stationIndex;
  });
};

const MINS_PER_STOP = 2.5;
const getStationETA = (stationIndex: number) => {
  if (busList.value.length === 0) return null;
  let minStops = Infinity;
  busList.value.forEach(bus => {
    let closestIdx = -1;
    let minDist = Infinity;
    currentStations.value.forEach((st, idx) => {
      const d = Math.pow(bus.px - st.stationLong, 2) + Math.pow(bus.py - st.stationLat, 2);
      if (d < minDist) { minDist = d; closestIdx = idx; }
    });
    const stopsDiff = stationIndex - closestIdx;
    if (stopsDiff >= 0 && stopsDiff < minStops) minStops = stopsDiff;
  });

  if (minStops === Infinity) return null;
  if (minStops === 0) return { text: '即将到站', isArriving: true };
  const mins = Math.ceil(minStops * MINS_PER_STOP);
  return { text: `${mins}分`, isArriving: false };
};

// [修改] 核心逻辑：重新计算最近站点
// 确保使用 currentStations（当前线路的站点）进行计算
const recalculateNearestStation = () => {
  // 必须重新获取 currentStations.value，因为它依赖 activeTabId
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
    if (d < minDist) {
      minDist = d;
      nearestStation = st;
      nearestIndex = index;
    }
  });

  cachedNearestStation.value = {
    station: nearestStation,
    index: nearestIndex,
    distance: minDist
  };
};

const nearestStationToUser = computed(() => cachedNearestStation.value);

// [关键] 监听线路变化，确保数据刷新后再重算
watch(activeTabId, async () => {
  selectedStationIndex.value = null;
  // 等待 computed 属性 currentStations 更新
  await nextTick();
  recalculateNearestStation();
});

const selectStation = (index: number) => {
  selectedStationIndex.value = index;
};

// [新增] 计算距离目标站点最近车辆的信息
const nearestBusInfo = computed(() => {
  // 1. 确定目标站点 (优先手动选择，其次定位最近)
  let targetIndex = -1;
  if (selectedStationIndex.value !== null) {
    targetIndex = selectedStationIndex.value;
  } else if (nearestStationToUser.value) {
    targetIndex = nearestStationToUser.value.index;
  }

  if (targetIndex === -1 || busList.value.length === 0) return null;

  let minStops = Infinity;
  let targetBus = null;

  busList.value.forEach(bus => {
    // 找到这辆车当前位置对应的最近站点索引
    let closestIdx = -1;
    let minDist = Infinity;
    currentStations.value.forEach((st, idx) => {
      const d = Math.pow(bus.px - st.stationLong, 2) + Math.pow(bus.py - st.stationLat, 2);
      if (d < minDist) { minDist = d; closestIdx = idx; }
    });

    const stopsDiff = targetIndex - closestIdx;
    
    // 逻辑：找还没过站的车中，离得最近的
    if (stopsDiff >= 0) {
      if (stopsDiff < minStops) {
        minStops = stopsDiff;
        targetBus = bus;
      }
    }
  });

  // 返回车牌后三位
  return targetBus ? targetBus.vehiNum.slice(-3) : null;
});

const overallNearestETA = computed(() => {
    if (busList.value.length === 0 || currentStations.value.length === 0) return '当前暂无车辆运行';

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

    if (nearestStationToUser.value) {
      const userStationIndex = nearestStationToUser.value.index;
      const etaData = getStationETA(userStationIndex);
      if (etaData) {
        const stationName = nearestStationToUser.value.station.stationAlias;
        if (etaData.isArriving) return `车辆即将到达 ${stationName}`;
        return `距 ${stationName} 约 ${etaData.text.replace('分', '')} 分钟`;
      }
    }

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

onMounted(() => {
  fetchLinedata();
  fetchBusData();
  getUserLocation(); 
  timer = setInterval(fetchBusData, 3000);
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