# 人生密度模块实现文档 - 替换状态评估模块

## 概述

本方案将现有的"状态评估模块"（情绪、精力、模板功能）替换为"人生密度模块"，作为每日最终的复盘工具。新模块将计算目标对齐率、进度效率和密度得分等指标，并集成到现有的Markdown导出功能中，支持导出到Obsidian。数据存储方式与现有系统一致，支持按日期手动清除更新。

## 现有模块分析

### 当前状态评估模块（第740-778行）
- 位置：第二列第二行（`class="card mood-energy"`）
- 包含：
  - 情绪评分（1-5级）
  - 精力评分（1-5级）
  - 每日模板选择器（默认模板、工作日志、学习日志、创意日志）
- 相关状态：
  ```javascript
  mood: 3,
  energy: 3,
  ```
- 相关函数：
  - `getMoodEmoji()`, `getEnergyEmoji()`
  - 事件监听器：`moodButtons`, `energyButtons`, `template-buttons`
- 导出内容：在Markdown的"## 📊 状态评估"部分

## 新模块设计

### 功能需求
1. **北极星目标管理**
   - 创建、编辑、删除目标
   - 设置目标标题、期望日期、优先级、颜色
   - 每日手动更新进度（0-100%）

2. **密度指标计算**
   - **目标对齐率**：投入目标相关时间 ÷ 总工作时间 × 100%
   - **进度效率**：当日进度增加值 ÷ 目标相关时间（小时）
   - **密度得分**：综合评分（0-100）

3. **可视化展示**
   - 指标卡片（3个关键指标）
   - 时间分配环形图
   - 进度趋势图

4. **复盘引导**
   - 基于数据的反思问题
   - 快速记录区域
   - 明日改进建议

### 用户界面
- 保持现有卡片位置和样式（`class="card mood-energy"`）
- 分为三个区域：
  1. **目标管理区**：目标选择器、进度更新
  2. **指标仪表盘**：三个指标卡片 + 图表
  3. **复盘引导区**：问题 + 记录文本框

## 数据结构更改

### 状态对象更新（第788-798行）
```javascript
const state = {
    date: new Date(),
    timeBlocks: [],
    tasks: [],
    notes: '',
    // 移除 mood 和 energy
    // mood: 3,
    // energy: 3,

    // 添加人生密度模块数据
    northStarGoals: [
        {
            id: "goal_1",
            title: "示例目标",
            targetDate: "2026-06-30", // 可选
            priority: "high",
            color: "#3498db",
            progress: 0, // 0-100
            totalTimeInvested: 0, // 总分钟数
            dailyProgressLog: [], // { date, progress, timeSpent }
            keywords: ["示例"] // 用于时间块匹配
        }
    ],
    activeGoalId: "goal_1", // 当前活跃目标
    dailyDensityLog: {}, // 按日期存储：{ "2026-03-29": { alignmentRate, progressEfficiency, densityScore, ... } }

    selectedTags: [],
    selectedTimeBlockId: null,
    viewMode: 'list'
};
```

### 存储结构
现有存储使用`localStorage`的`efficiencyTrackerAllData`键，按日期索引。将更新为包含新字段。

## 代码修改步骤

### 1. HTML结构替换（第740-778行）
```html
<!-- 替换为人生密度模块 -->
<div class="card mood-energy">
    <div class="card-header">
        <div class="card-title">
            <span class="icon">🎯</span> 人生密度复盘
        </div>
    </div>

    <!-- 目标管理区 -->
    <div class="goal-management">
        <div class="goal-selector">
            <select id="goalSelect">
                <option value="">选择北极星目标</option>
            </select>
            <button id="createGoalBtn">新建目标</button>
        </div>
        <div class="goal-progress">
            <div>当前进度：<span id="currentProgress">0</span>%</div>
            <input type="range" id="progressSlider" min="0" max="100" value="0">
            <button id="updateProgressBtn">更新进度</button>
        </div>
    </div>

    <!-- 指标仪表盘 -->
    <div class="density-dashboard">
        <div class="metric-cards">
            <div class="metric-card">
                <div class="metric-title">目标对齐率</div>
                <div class="metric-value" id="alignmentRate">0%</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">进度效率</div>
                <div class="metric-value" id="progressEfficiency">0</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">密度得分</div>
                <div class="metric-value" id="densityScore">0</div>
            </div>
        </div>
        <div class="density-charts">
            <!-- 图表容器 -->
            <div id="timeDistributionChart"></div>
            <div id="progressTrendChart"></div>
        </div>
    </div>

    <!-- 复盘引导区 -->
    <div class="retro-guide">
        <div class="reflection-questions">
            <h4>复盘问题：</h4>
            <p id="question1">今日时间投入是否与目标对齐？</p>
            <p id="question2">进度效率如何？有哪些改进空间？</p>
        </div>
        <textarea class="retro-notes" id="retroNotes" placeholder="记录今日复盘思考..."></textarea>
        <div class="tomorrow-suggestions">
            <h4>明日建议：</h4>
            <p id="tomorrowSuggestion">基于今日数据，明日可尝试...</p>
        </div>
    </div>
</div>
```

### 2. CSS样式更新
在现有的`<style>`标签中添加新样式：
```css
/* 人生密度模块样式 */
.goal-management {
    padding: 12px;
    border-bottom: 1px solid #eee;
}

.goal-selector {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
}

.goal-progress {
    display: flex;
    align-items: center;
    gap: 12px;
}

.metric-cards {
    display: flex;
    justify-content: space-between;
    margin: 16px 0;
    gap: 12px;
}

.metric-card {
    flex: 1;
    background: #f8f9fa;
    border-radius: 8px;
    padding: 12px;
    text-align: center;
    border: 1px solid #e9ecef;
}

.metric-title {
    font-size: 0.9rem;
    color: #6c757d;
    margin-bottom: 4px;
}

.metric-value {
    font-size: 1.5rem;
    font-weight: bold;
    color: #2c3e50;
}

.density-charts {
    display: flex;
    gap: 16px;
    height: 200px;
    margin-bottom: 16px;
}

.density-charts > div {
    flex: 1;
    background: #f8f9fa;
    border-radius: 8px;
}

.retro-guide {
    padding: 12px;
    border-top: 1px solid #eee;
}

.reflection-questions p, .tomorrow-suggestions p {
    margin: 8px 0;
    font-size: 0.9rem;
    color: #495057;
}

.retro-notes {
    width: 100%;
    height: 80px;
    margin: 12px 0;
    padding: 8px;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    font-family: inherit;
}
```

### 3. JavaScript功能实现

#### 3.1 移除旧功能
- 删除`moodButtons`、`energyButtons`相关代码
- 删除`template-buttons`相关代码
- 删除`getMoodEmoji()`和`getEnergyEmoji()`函数

#### 3.2 添加新功能

**目标管理函数：**
```javascript
// 目标CRUD操作
function createGoal(goalData) {
    const id = 'goal_' + Date.now();
    const newGoal = {
        id,
        title: goalData.title || '未命名目标',
        targetDate: goalData.targetDate || '',
        priority: goalData.priority || 'medium',
        color: goalData.color || '#3498db',
        progress: 0,
        totalTimeInvested: 0,
        dailyProgressLog: [],
        keywords: goalData.keywords || []
    };
    state.northStarGoals.push(newGoal);
    if (!state.activeGoalId) state.activeGoalId = id;
    renderGoalSelector();
    saveToStorage();
}

function updateGoalProgress(goalId, progress) {
    const goal = state.northStarGoals.find(g => g.id === goalId);
    if (!goal) return;

    const today = getTodayKey();
    const prevProgress = goal.progress;
    goal.progress = Math.max(0, Math.min(100, progress));

    // 记录每日进度
    const logEntry = goal.dailyProgressLog.find(entry => entry.date === today);
    if (logEntry) {
        logEntry.progress = goal.progress;
    } else {
        goal.dailyProgressLog.push({
            date: today,
            progress: goal.progress,
            timeSpent: 0 // 将由时间分析更新
        });
    }

    calculateDailyDensity();
    saveToStorage();
}
```

**密度指标计算：**
```javascript
function calculateDailyDensity() {
    const today = getTodayKey();
    const activeGoal = state.northStarGoals.find(g => g.id === state.activeGoalId);
    if (!activeGoal) return;

    // 1. 计算目标相关时间
    const goalRelatedTime = calculateGoalRelatedTime(activeGoal);
    const totalWorkTime = calculateTotalWorkTime();

    // 2. 计算指标
    const alignmentRate = totalWorkTime > 0 ? (goalRelatedTime / totalWorkTime) * 100 : 0;

    // 获取今日进度变化
    const todayLog = activeGoal.dailyProgressLog.find(entry => entry.date === today);
    const yesterday = getYesterdayKey();
    const yesterdayLog = activeGoal.dailyProgressLog.find(entry => entry.date === yesterday);
    const progressChange = todayLog ? (todayLog.progress - (yesterdayLog?.progress || 0)) : 0;

    const progressEfficiency = goalRelatedTime > 0 ? (progressChange / (goalRelatedTime / 60)) * 100 : 0;
    const densityScore = calculateDensityScore(alignmentRate, progressEfficiency);

    // 3. 存储结果
    state.dailyDensityLog[today] = {
        alignmentRate,
        progressEfficiency,
        densityScore,
        goalRelatedTime,
        totalWorkTime,
        progressChange
    };

    updateDensityUI();
}

function calculateGoalRelatedTime(goal) {
    let totalMinutes = 0;
    const todayKey = getTodayKey();

    state.timeBlocks.forEach(block => {
        // 检查是否为今日时间块
        if (block.date !== todayKey) return;

        // 关键词匹配
        const activity = block.activity || '';
        const matchesKeyword = goal.keywords.some(keyword =>
            activity.toLowerCase().includes(keyword.toLowerCase())
        );

        if (matchesKeyword && block.startTime && block.endTime) {
            const [startH, startM] = block.startTime.split(':').map(Number);
            const [endH, endM] = block.endTime.split(':').map(Number);
            const minutes = (endH * 60 + endM) - (startH * 60 + startM);
            if (minutes > 0) totalMinutes += minutes;
        }
    });

    return totalMinutes;
}
```

**UI更新函数：**
```javascript
function renderGoalSelector() {
    const selectEl = document.getElementById('goalSelect');
    if (!selectEl) return;

    selectEl.innerHTML = '<option value="">选择北极星目标</option>';
    state.northStarGoals.forEach(goal => {
        const option = document.createElement('option');
        option.value = goal.id;
        option.textContent = goal.title;
        option.selected = goal.id === state.activeGoalId;
        selectEl.appendChild(option);
    });
}

function updateDensityUI() {
    const today = getTodayKey();
    const density = state.dailyDensityLog[today] || {};

    document.getElementById('alignmentRate').textContent =
        density.alignmentRate ? density.alignmentRate.toFixed(1) + '%' : '0%';
    document.getElementById('progressEfficiency').textContent =
        density.progressEfficiency ? density.progressEfficiency.toFixed(1) : '0';
    document.getElementById('densityScore').textContent =
        density.densityScore ? Math.round(density.densityScore) : '0';

    // 更新进度显示
    const activeGoal = state.northStarGoals.find(g => g.id === state.activeGoalId);
    if (activeGoal) {
        document.getElementById('currentProgress').textContent = activeGoal.progress;
        document.getElementById('progressSlider').value = activeGoal.progress;
    }
}
```

#### 3.3 事件监听器更新
```javascript
// 替换原有的情绪/精力/模板事件监听器
function setupDensityEventListeners() {
    // 目标选择器
    const goalSelect = document.getElementById('goalSelect');
    if (goalSelect) {
        goalSelect.addEventListener('change', (e) => {
            state.activeGoalId = e.target.value;
            calculateDailyDensity();
            saveToStorage();
        });
    }

    // 进度滑块
    const progressSlider = document.getElementById('progressSlider');
    if (progressSlider) {
        progressSlider.addEventListener('input', (e) => {
            document.getElementById('currentProgress').textContent = e.target.value;
        });

        progressSlider.addEventListener('change', (e) => {
            if (state.activeGoalId) {
                updateGoalProgress(state.activeGoalId, parseInt(e.target.value));
            }
        });
    }

    // 新建目标按钮
    const createGoalBtn = document.getElementById('createGoalBtn');
    if (createGoalBtn) {
        createGoalBtn.addEventListener('click', () => {
            const title = prompt('请输入目标标题：');
            if (title) {
                createGoal({ title });
            }
        });
    }
}
```

### 4. 导出功能更新

#### 4.1 修改generateMarkdown()函数（第1427行）
```javascript
function generateMarkdown() {
    const now = state.date;
    const dateStr = now.toISOString().split('T')[0];
    const weekday = ['日', '一', '二', '三', '四', '五', '六'][now.getDay()];

    // ... 现有时间计算代码 ...

    // 获取今日密度数据
    const density = state.dailyDensityLog[dateStr] || {};
    const activeGoal = state.northStarGoals.find(g => g.id === state.activeGoalId);

    // 生成Markdown
    let markdown = `---
date: ${dateStr}
weekday: 星期${weekday}
total_time: ${totalHours}h${remainingMinutes > 0 ? remainingMinutes + 'm' : ''}
`;

    // 添加目标信息
    if (activeGoal) {
        markdown += `active_goal: "${activeGoal.title}"
goal_progress: ${activeGoal.progress}%
`;
    }

    // 添加密度指标
    markdown += `alignment_rate: ${density.alignmentRate ? density.alignmentRate.toFixed(1) : 0}%
progress_efficiency: ${density.progressEfficiency ? density.progressEfficiency.toFixed(1) : 0}
density_score: ${density.densityScore ? Math.round(density.densityScore) : 0}
---

# ${dateStr} 星期${weekday} 每日记录

## 🎯 人生密度复盘

`;

    if (activeGoal) {
        markdown += `**北极星目标**: ${activeGoal.title}
**当前进度**: ${activeGoal.progress}%

### 📊 密度指标
- **目标对齐率**: ${density.alignmentRate ? density.alignmentRate.toFixed(1) : 0}%
- **进度效率**: ${density.progressEfficiency ? density.progressEfficiency.toFixed(1) : 0}
- **密度得分**: ${density.densityScore ? Math.round(density.densityScore) : 0}/100

`;
    }

    // 原有时间记录、任务列表等部分保持不变...
    markdown += `
## ⏰ 时间记录

| 时间 | 活动 | 时长 |
|------|------|------|
`;

    // ... 原有时间块表格代码 ...

    markdown += `
总计：${totalHours}小时${remainingMinutes > 0 ? remainingMinutes + '分钟' : ''}

## ✅ 今日任务

`;

    // ... 原有任务列表代码 ...

    markdown += `
## 📝 笔记与反思

${notesTextEl.value}

## 💭 密度复盘思考

${document.getElementById('retroNotes') ? document.getElementById('retroNotes').value : ''}

---

*记录时间: ${now.toLocaleString('zh-CN')}*
`;

    return markdown;
}
```

#### 4.2 移除旧的状态评估部分
删除原有Markdown生成中的"## 📊 状态评估"部分。

### 5. 数据存储更新

#### 5.1 修改saveToStorage()和loadFromStorage()
更新存储逻辑以包含新字段：
```javascript
function saveToStorage() {
    const todayKey = getTodayKey();
    const allData = getAllData();

    // 准备今日数据（排除不必要的字段）
    const todayData = {
        date: state.date.toISOString(),
        timeBlocks: state.timeBlocks,
        tasks: state.tasks,
        notes: notesTextEl.value,
        northStarGoals: state.northStarGoals,
        activeGoalId: state.activeGoalId,
        dailyDensityLog: state.dailyDensityLog
    };

    allData[todayKey] = todayData;
    saveAllData(allData);
}

function loadFromStorage() {
    const todayKey = getTodayKey();
    const allData = getAllData();
    const todayData = allData[todayKey];

    if (todayData) {
        // 加载基础数据
        if (todayData.timeBlocks) state.timeBlocks = todayData.timeBlocks;
        if (todayData.tasks) state.tasks = todayData.tasks;
        if (todayData.notes) notesTextEl.value = todayData.notes;

        // 加载人生密度数据
        if (todayData.northStarGoals) state.northStarGoals = todayData.northStarGoals;
        if (todayData.activeGoalId) state.activeGoalId = todayData.activeGoalId;
        if (todayData.dailyDensityLog) state.dailyDensityLog = todayData.dailyDensityLog;
    }

    // 初始化默认目标（如果没有）
    if (state.northStarGoals.length === 0) {
        createGoal({ title: "我的第一个目标", keywords: [] });
    }
}
```

#### 5.2 修改clearData()函数（第1548行）
```javascript
function clearData() {
    if (confirm('确定要清空今天的所有数据吗？此操作不可撤销！')) {
        // 重置状态
        state.timeBlocks = [];
        state.tasks = [];
        state.notes = '';
        // 保留目标数据（跨日持久化）
        // state.northStarGoals 保持不变
        // state.dailyDensityLog 保留历史数据

        // 重置今日特定数据
        const todayKey = getTodayKey();
        delete state.dailyDensityLog[todayKey];

        // 更新今日目标的进度日志（清空今日记录）
        state.northStarGoals.forEach(goal => {
            goal.dailyProgressLog = goal.dailyProgressLog.filter(entry => entry.date !== todayKey);
        });

        state.selectedTags = [];
        state.selectedTimeBlockId = null;

        // 从按日期存储的数据中删除今天的记录
        const allData = getAllData();
        delete allData[todayKey];
        saveAllData(allData);

        // 更新UI
        renderTimeBlocks();
        renderTimeAxis();
        renderTasks();
        notesTextEl.value = '';

        // 清空复盘笔记
        const retroNotesEl = document.getElementById('retroNotes');
        if (retroNotesEl) retroNotesEl.value = '';

        // 重置密度UI
        updateDensityUI();

        // 添加一个默认时间块和任务
        addTimeBlock('09:00', '10:30', '');
        addTask('示例任务，点击编辑');
    }
}
```

### 6. 初始化函数更新

#### 6.1 修改init()函数
```javascript
function init() {
    loadFromStorage();
    renderTimeBlocks();
    renderTimeAxis();
    renderTasks();

    // 移除原有的情绪/精力初始化
    // setRatingSelection(moodButtons, state.mood);
    // setRatingSelection(energyButtons, state.energy);

    // 初始化人生密度模块
    renderGoalSelector();
    calculateDailyDensity();
    setupDensityEventListeners();

    // 保留其他初始化代码...
}
```

### 7. 移除不再需要的函数
- `getMoodEmoji()` (第1530行)
- `getEnergyEmoji()` (第1536行)
- `setRatingSelection()`（如果不再使用）

## 测试计划

### 单元测试
1. **目标管理功能**
   - 创建、读取、更新、删除目标
   - 进度更新和日志记录

2. **密度计算逻辑**
   - 目标相关时间计算
   - 指标计算公式验证
   - 边界条件测试（零时间、零进度）

3. **数据持久化**
   - 存储/加载完整性
   - 跨日数据保留

### 集成测试
1. **与时间块系统集成**
   - 关键词匹配功能
   - 时间统计准确性

2. **导出功能集成**
   - Markdown格式正确性
   - Obsidian兼容性

3. **UI交互**
   - 目标选择器操作
   - 进度滑块响应
   - 实时指标更新

### 用户验收测试
1. **功能完整性**
   - 所有需求功能可用
   - 数据准确性

2. **用户体验**
   - 界面直观性
   - 操作流畅度

3. **性能表现**
   - 页面加载时间
   - 响应速度

## 部署步骤

### 1. 备份现有版本
```bash
cp index.html index_backup_$(date +%Y%m%d_%H%M%S).html
```

### 2. 分步实施
1. **第一阶段**：HTML结构替换 + CSS样式添加
2. **第二阶段**：JavaScript核心功能实现
3. **第三阶段**：导出功能更新
4. **第四阶段**：数据存储更新
5. **第五阶段**：测试和调试

### 3. 验证检查清单
- [ ] 页面正常加载，无JavaScript错误
- [ ] 目标创建和选择功能正常
- [ ] 密度指标正确计算和显示
- [ ] 数据正确保存和加载
- [ ] Markdown导出包含密度信息
- [ ] 清空数据功能正常工作

## 风险与缓解

### 技术风险
1. **数据迁移风险**：现有用户数据可能丢失
   - 缓解：提供数据备份和迁移工具

2. **性能问题**：大量目标或时间块导致计算缓慢
   - 缓解：优化算法，添加防抖处理

### 用户体验风险
1. **功能复杂度**：新模块可能较复杂
   - 缓解：提供默认配置和简单引导

2. **学习曲线**：用户需要时间适应
   - 缓解：保留核心时间记录功能不变

## 成功指标

### 功能指标
- 目标创建成功率 > 95%
- 密度计算准确率 > 98%
- 数据导出完整性 100%

### 用户体验指标
- 用户满意度调查得分 > 4/5
- 每日使用率 > 70%
- 错误报告数量 < 5/月

---

**文档版本**: v1.0
**创建日期**: 2026-03-29
**更新日期**: 2026-03-29
**适用版本**: 日程记录工具 v2.0