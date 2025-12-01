<template>
  <div class="app-container">
    <van-nav-bar title="浙大校车 Live" fixed placeholder />

    <van-pull-refresh v-model="loading" @refresh="onRefresh">
      <div v-if="busList.length > 0" class="card-list">
        <div v-for="(bus, index) in busList" :key="index" class="bus-card">
          <div class="line-header">
            <span class="line-name">{{ index+1 }}</span>
            <van-tag type="primary" size="medium">{{ bus.vehiNum }}</van-tag>
          </div>

          <div class="bus-info">
            <div class="info-item">
              <span class="label">更新时间</span>
              <span class="value">{{ bus.speedTime }}</span>
            </div>
            <div class="info-item">
              <span class="label">方向</span>
              <span class="value">{{ bus.direction }}</span>
            </div>
          </div>
        </div>
      </div>

      <van-empty v-else description="当前没有运行中的校车" image="search" />

    </van-pull-refresh>
    <div class="button-group">
      <button @click="changeLine('L820')">1号线</button>
      <button @click="changeLine('L819')">2号线</button>
      <button @click="changeLine('L821')">3号线</button>
      <button @click="changeLine('L822')">假日专线</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
const currentLine = ref("L820");
const changeLine = (newLineName) => {
  // 1. 修改当前线路变量
  currentLine.value = newLineName;
  
  // 2. 马上根据新线路去抓取数据
  fetchBusData();
}
const loading = ref(false);
const busLineData = ref([]);
const busList = ref([]);
const fetchLinedata = async () => {
  try {
    // 1. 请求刚才 Python 生成的文件
    // 加上时间戳 ?t=... 防止浏览器缓存旧数据
    const response = await fetch('/bus_line_data.json');

    if (!response.ok) {
      throw new Error('暂无数据文件');
    }

    const res = await response.json();

    // 2. 将数据赋值给 busList
    // 注意：Python 生成的结构是 { data: [...] }，所以这里取 res.data
    busLineData.value = res.data || [];

    // 如果没有车，显示提示
    if (busLineData.value.length === 0) {
      console.log("文件读取成功，但列表为空（可能当前没车）");
    }

  } catch (error) {
    console.error("获取数据失败:", error);
    busLineData.value = []; // 清空列表
  } finally {
    loading.value=false;
  }
}

// 模拟从后端获取数据
const fetchBusData = async () => {
  loading.value = true;
  try {
    // 1. 请求刚才 Python 生成的文件
    // 加上时间戳 ?t=... 防止浏览器缓存旧数据
    const response = await fetch(`/${currentLine.value}.json`);

    if (!response.ok) {
      throw new Error('暂无数据文件');
    }

    const res = await response.json();

    // 2. 将数据赋值给 busList
    // 注意：Python 生成的结构是 { data: [...] }，所以这里取 res.data
    busList.value = res.data || [];

    // 如果没有车，显示提示
    if (busList.value.length === 0) {
      console.log("文件读取成功，但列表为空（可能当前没车）");
    }

  } catch (error) {
    console.error("获取数据失败:", error);
    busList.value = []; // 清空列表
  } finally {
    loading.value = false;
  }
};

// 下拉刷新触发
const onRefresh = () => {
  fetchBusData();
};

// 页面加载时触发
onMounted(() => {
  fetchLinedata();
  fetchBusData();
});
</script>