# 苦强指数模块项目文档

## 项目概述

### 目标
替换现有的"状态评估模块"，创建"苦强指数模块"作为每日量化评估工具。通过"变强"（主动增值）和"吃苦"（被动消耗）两个维度的评估，计算每日的苦强指数，帮助用户量化个人成长与生存成本。

### 核心变化
1. **模块替换**：完全替代原有的情绪/精力评估和每日模板功能
2. **双维度评估**：基于两张图片中的指标，分为"变强"和"吃苦"两个评估页面
3. **量化计分**：根据用户选择和时间输入计算具体得分
4. **指数计算**：综合两个维度计算最终的苦强指数

## 功能需求

### 1. 变强评估（苦强指数测试【1】）
- **评估问题**：你今天做了哪些变强的事？（可多选）
- **评价标准**：主动、有结果的行动，能带来实际回报
- **评估选项**：
  1. 学到一个有用的知识点并付诸实践
  2. 学会一个新方法or技术
  3. 找到一个新客户
  4. 认识一个厉害的人
  5. 获得一笔超额回报（是时薪的3倍）
  6. 主动向领导汇报一次
  7. 以上都没有
- **计分规则**：每个选项有相应的分值，计算当前得分

### 2. 吃苦评估（苦强指数测试【2】）
- **评估问题**：今天你吃苦了吗？（可多选）
- **评价标准**：被动、消耗性的，是维持生存必须付出的时间成本
- **评估项目**：
  1. 坐班时长（小时）
  2. 通勤时长（小时）
  3. 家务时长（小时）
- **计算规则**：总吃苦时长 = 坐班时长 + 通勤时长 + 家务时长

### 3. 苦强指数计算
- **计算公式**：苦强指数 = 变强得分 × (1 - 吃苦时长衰减系数)
- **显示方式**：点击按钮查看最终的苦强指数

### 4. 数据导出
- 在Markdown导出中添加"苦强指数评估"章节
- 包含变强选择、吃苦时长和最终指数

## 系统设计

### 用户界面设计

#### 直接替换方案
苦强指数模块将**直接替代现有的状态评估模块**，保持相同的网格位置（第二列第二行）。无需修改布局，完全兼容现有设计。

#### 模块UI组件
1. **变强评估区**（顶部）
   - **标题**：苦强指数测试【1】
   - **问题**：你今天做了哪些变强的事？（可多选）
   - **选项列表**：7个复选框选项
   - **当前得分显示**：实时计算和显示得分

2. **吃苦评估区**（中部）
   - **标题**：苦强指数测试【2】
   - **问题**：今天你吃苦了吗？（可多选）
   - **时间输入**：三个时间输入框（坐班、通勤、家务）
   - **总时长显示**：实时计算和显示总吃苦时长

3. **指数查看区**（底部）
   - **查看按钮**："点击查看你的苦强指数吧！"
   - **结果显示**：点击后显示计算出的苦强指数

### 数据结构设计

#### 核心状态对象
```javascript
// 在现有state对象中替换/添加
const state = {
  // 现有属性...（保留时间块、任务、笔记等）

  // 替换原有的mood、energy等属性
  kuQiangData: {
    // 变强评估数据
    strengthening: {
      selections: [], // 选中的选项索引数组 [0,2,4]
      score: 0 // 当前得分
    },
    // 吃苦评估数据
    suffering: {
      officeHours: 0,   // 坐班时长（小时）
      commuteHours: 0,  // 通勤时长（小时）
      houseworkHours: 0, // 家务时长（小时）
      totalHours: 0     // 总吃苦时长
    },
    // 最终指数
    kuQiangIndex: 0
  }
};
```

#### 变强选项配置
```javascript
// 变强选项配置（与图片完全一致）
const strengtheningOptions = [
  { id: 1, text: "学到一个有用的知识点并付诸实践", score: 10 },
  { id: 2, text: "学会一个新方法or技术", score: 15 },
  { id: 3, text: "找到一个新客户", score: 20 },
  { id: 4, text: "认识一个厉害的人", score: 12 },
  { id: 5, text: "获得一笔超额回报(是时薪的3倍", score: 25 },
  { id: 6, text: "主动向领导汇报一次", score: 8 },
  { id: 7, text: "以上都没有", score: 0, exclusive: true } // 互斥选项
];
```

#### 苦强指数计算逻辑
```javascript
// 苦强指数计算函数
function calculateKuQiangIndex() {
  const { strengthening, suffering } = state.kuQiangData;

  // 1. 计算变强得分
  let strengtheningScore = 0;
  if (strengthening.selections.length === 0) {
    // 如果没有选择任何选项，得分为0
    strengtheningScore = 0;
  } else if (strengthening.selections.includes(6)) { // "以上都没有"是第7个选项，索引6
    // 如果选择了"以上都没有"，得分为0
    strengtheningScore = 0;
  } else {
    // 计算选中选项的总分
    strengthening.selections.forEach(optionIndex => {
      if (optionIndex < strengtheningOptions.length) {
        strengtheningScore += strengtheningOptions[optionIndex].score;
      }
    });
  }

  // 2. 计算吃苦衰减系数
  // 假设每天最多可承受12小时吃苦时间
  const maxSufferingHours = 12;
  const sufferingRatio = Math.min(suffering.totalHours / maxSufferingHours, 1);
  const sufferingPenalty = sufferingRatio * 0.5; // 最多减少50%的得分

  // 3. 计算苦强指数
  const kuQiangIndex = Math.round(strengtheningScore * (1 - sufferingPenalty));

  // 4. 更新状态
  state.kuQiangData.strengthening.score = strengtheningScore;
  state.kuQiangData.kuQiangIndex = kuQiangIndex;

  return kuQiangIndex;
}
```

### 与现有系统集成

#### 1. 替换状态评估模块
- 直接替换HTML中第740-778行的"状态评估"卡片
- 保持相同的CSS类名和结构
- 更新JavaScript初始化逻辑

#### 2. 数据导出集成
- 在Markdown导出中添加"苦强指数评估"章节
- 包含变强选择、吃苦时长和最终指数

#### 3. 模板系统移除
- 移除原有的每日模板功能
- 专注于苦强指数评估

## 实现步骤

### 阶段1：基础架构
1. **扩展数据模型**
   - 添加苦强指数数据结构定义
   - 实现存储/加载函数
   - 更新初始化逻辑

2. **创建UI组件**
   - 变强评估组件（复选框列表）
   - 吃苦评估组件（时间输入框）
   - 指数显示组件

3. **实现计分逻辑**
   - 变强选项计分
   - 吃苦时长计算
   - 苦强指数计算

### 阶段2：交互功能
1. **选项选择交互**
   - 复选框选择/取消
   - 实时得分更新
   - 互斥选项处理（"以上都没有"）

2. **时间输入交互**
   - 数字输入验证
   - 实时总时长计算
   - 输入限制（0-24小时）

3. **指数计算交互**
   - 按钮点击事件
   - 指数计算和显示
   - 结果格式化

### 阶段3：数据集成
1. **存储集成**
   - 与现有localStorage系统集成
   - 按日期存储苦强数据
   - 数据加载和恢复

2. **导出集成**
   - 扩展Markdown导出功能
   - 添加苦强指数章节
   - 格式美化

### 阶段4：优化与测试
1. **用户体验优化**
   - 响应式设计
   - 输入提示和帮助
   - 结果可视化

2. **测试验证**
   - 计分逻辑测试
   - 数据持久化测试
   - 导出功能测试

## 详细设计

### HTML结构设计
```html
<!-- 替换原有的情绪与精力卡片 -->
<div class="card mood-energy">
    <div class="card-header">
        <div class="card-title">
            <span class="icon">📊</span> 苦强指数评估
        </div>
    </div>

    <!-- 变强评估部分 -->
    <div class="strengthening-section">
        <h4>苦强指数测试【1】</h4>
        <p class="question">你今天做了哪些变强的事？（可多选）</p>
        <p class="criteria"><small>变强评价标准：主动、有结果的行动，能带来实际回报</small></p>

        <div class="options-list" id="strengtheningOptions">
            <!-- 选项将通过JavaScript动态生成 -->
        </div>

        <div class="score-display">
            当前得分：<span id="strengtheningScore">0</span>分
        </div>
    </div>

    <!-- 吃苦评估部分 -->
    <div class="suffering-section">
        <h4>苦强指数测试【2】</h4>
        <p class="question">今天你吃苦了吗？（可多选）</p>
        <p class="criteria"><small>吃苦评价标准：被动、消耗性的，是维持生存必须付出的时间成本</small></p>

        <div class="time-inputs">
            <div class="time-input">
                <label>坐班时长</label>
                <input type="number" id="officeHours" min="0" max="24" step="0.5" value="0">
                <span>小时</span>
            </div>
            <div class="time-input">
                <label>通勤时长</label>
                <input type="number" id="commuteHours" min="0" max="24" step="0.5" value="0">
                <span>小时</span>
            </div>
            <div class="time-input">
                <label>家务时长</label>
                <input type="number" id="houseworkHours" min="0" max="24" step="0.5" value="0">
                <span>小时</span>
            </div>
        </div>

        <div class="total-display">
            总吃苦时长：<span id="totalSufferingHours">0</span>小时
        </div>
    </div>

    <!-- 指数查看部分 -->
    <div class="index-section">
        <button id="calculateIndexBtn">点击查看你的苦强指数吧！</button>
        <div id="indexResult" class="index-result" style="display: none;">
            你的苦强指数是：<span id="kuQiangIndexValue">0</span>
        </div>
    </div>
</div>
```

### CSS样式设计
```css
/* 苦强指数模块样式 */
.strengthening-section,
.suffering-section {
    padding: 12px;
    border-bottom: 1px solid #eee;
}

.question {
    font-weight: 600;
    margin: 8px 0 4px 0;
    color: #2c3e50;
}

.criteria {
    color: #7f8c8d;
    font-size: 0.9rem;
    margin-bottom: 12px;
}

.options-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 12px;
}

.option-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 8px;
    background: #f8f9fa;
    border-radius: 4px;
    border: 1px solid #e9ecef;
}

.option-item input[type="checkbox"] {
    width: 16px;
    height: 16px;
}

.option-item label {
    flex: 1;
    font-size: 0.95rem;
    cursor: pointer;
}

.score-display,
.total-display {
    text-align: right;
    font-weight: 600;
    color: #3498db;
    margin-top: 8px;
}

.time-inputs {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin: 12px 0;
}

.time-input {
    display: flex;
    align-items: center;
    gap: 8px;
}

.time-input label {
    width: 80px;
    font-weight: 500;
}

.time-input input {
    flex: 1;
    padding: 6px 8px;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    text-align: right;
}

.index-section {
    padding: 12px;
    text-align: center;
}

#calculateIndexBtn {
    background: #3498db;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    font-size: 1rem;
    cursor: pointer;
    transition: background 0.2s;
}

#calculateIndexBtn:hover {
    background: #2980b9;
}

.index-result {
    margin-top: 16px;
    padding: 12px;
    background: #e8f4fc;
    border-radius: 8px;
    font-size: 1.2rem;
    font-weight: bold;
    color: #2c3e50;
}
```

### JavaScript功能实现

#### 1. 初始化函数
```javascript
function initKuQiangModule() {
    // 渲染变强选项
    renderStrengtheningOptions();

    // 设置事件监听
    setupKuQiangEventListeners();

    // 加载已有数据
    loadKuQiangData();

    // 初始计算
    updateStrengtheningScore();
    updateTotalSufferingHours();
}

function renderStrengtheningOptions() {
    const container = document.getElementById('strengtheningOptions');
    if (!container) return;

    container.innerHTML = '';

    strengtheningOptions.forEach((option, index) => {
        const optionEl = document.createElement('div');
        optionEl.className = 'option-item';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `strength_opt_${index}`;
        checkbox.value = index;
        checkbox.checked = state.kuQiangData.strengthening.selections.includes(index);

        const label = document.createElement('label');
        label.htmlFor = `strength_opt_${index}`;
        label.textContent = option.text;

        optionEl.appendChild(checkbox);
        optionEl.appendChild(label);
        container.appendChild(optionEl);
    });
}
```

#### 2. 事件处理函数
```javascript
function setupKuQiangEventListeners() {
    // 变强选项点击事件
    const optionCheckboxes = document.querySelectorAll('#strengtheningOptions input[type="checkbox"]');
    optionCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', handleStrengtheningOptionChange);
    });

    // 吃苦时间输入事件
    const timeInputs = ['officeHours', 'commuteHours', 'houseworkHours'];
    timeInputs.forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) {
            input.addEventListener('input', handleSufferingTimeChange);
            input.addEventListener('change', handleSufferingTimeChange);
        }
    });

    // 指数计算按钮
    const calculateBtn = document.getElementById('calculateIndexBtn');
    if (calculateBtn) {
        calculateBtn.addEventListener('click', calculateAndShowKuQiangIndex);
    }
}

function handleStrengtheningOptionChange(e) {
    const index = parseInt(e.target.value);
    const isChecked = e.target.checked;

    let selections = [...state.kuQiangData.strengthening.selections];

    if (isChecked) {
        // 如果选中了"以上都没有"
        if (index === 6) { // 第7个选项（索引6）
            selections = [6]; // 只保留这个选项
            // 取消选中其他所有复选框
            document.querySelectorAll('#strengtheningOptions input[type="checkbox"]').forEach((cb, i) => {
                if (i !== 6) cb.checked = false;
            });
        } else {
            // 如果选中了其他选项，确保"以上都没有"不被选中
            selections = selections.filter(i => i !== 6);
            const noneCheckbox = document.querySelector('#strengtheningOptions input[type="checkbox"][value="6"]');
            if (noneCheckbox) noneCheckbox.checked = false;
            selections.push(index);
        }
    } else {
        // 取消选中
        selections = selections.filter(i => i !== index);
    }

    // 更新状态
    state.kuQiangData.strengthening.selections = [...new Set(selections)]; // 去重

    // 更新UI和存储
    updateStrengtheningScore();
    saveToStorage();
}

function handleSufferingTimeChange() {
    // 获取输入值
    const officeHours = parseFloat(document.getElementById('officeHours').value) || 0;
    const commuteHours = parseFloat(document.getElementById('commuteHours').value) || 0;
    const houseworkHours = parseFloat(document.getElementById('houseworkHours').value) || 0;

    // 更新状态
    state.kuQiangData.suffering.officeHours = officeHours;
    state.kuQiangData.suffering.commuteHours = commuteHours;
    state.kuQiangData.suffering.houseworkHours = houseworkHours;

    // 计算总时长
    updateTotalSufferingHours();
    saveToStorage();
}

function calculateAndShowKuQiangIndex() {
    const index = calculateKuQiangIndex();

    // 显示结果
    const resultEl = document.getElementById('indexResult');
    const valueEl = document.getElementById('kuQiangIndexValue');

    if (resultEl && valueEl) {
        valueEl.textContent = index;
        resultEl.style.display = 'block';

        // 根据指数值添加评价
        let evaluation = '';
        if (index >= 80) {
            evaluation = '（非常出色！）';
            valueEl.style.color = '#27ae60';
        } else if (index >= 60) {
            evaluation = '（表现良好）';
            valueEl.style.color = '#f39c12';
        } else if (index >= 40) {
            evaluation = '（还需努力）';
            valueEl.style.color = '#e67e22';
        } else {
            evaluation = '（加油改进）';
            valueEl.style.color = '#e74c3c';
        }

        valueEl.textContent = `${index} ${evaluation}`;
    }
}
```

#### 3. 工具函数
```javascript
function updateStrengtheningScore() {
    // 计算得分
    calculateKuQiangIndex(); // 这会更新strengthening.score

    // 更新UI
    const scoreEl = document.getElementById('strengtheningScore');
    if (scoreEl) {
        scoreEl.textContent = state.kuQiangData.strengthening.score;
    }
}

function updateTotalSufferingHours() {
    const { officeHours, commuteHours, houseworkHours } = state.kuQiangData.suffering;
    const total = officeHours + commuteHours + houseworkHours;

    // 更新状态
    state.kuQiangData.suffering.totalHours = total;

    // 更新UI
    const totalEl = document.getElementById('totalSufferingHours');
    if (totalEl) {
        totalEl.textContent = total.toFixed(1);
    }
}

function loadKuQiangData() {
    const todayKey = getTodayKey();
    const allData = getAllData();
    const todayData = allData[todayKey];

    if (todayData && todayData.kuQiangData) {
        // 加载苦强数据
        state.kuQiangData = todayData.kuQiangData;

        // 更新UI
        renderStrengtheningOptions();

        // 更新时间输入
        document.getElementById('officeHours').value = state.kuQiangData.suffering.officeHours;
        document.getElementById('commuteHours').value = state.kuQiangData.suffering.commuteHours;
        document.getElementById('houseworkHours').value = state.kuQiangData.suffering.houseworkHours;

        updateStrengtheningScore();
        updateTotalSufferingHours();
    }
}
```

## 数据导出集成

### 修改generateMarkdown()函数
```javascript
function generateMarkdown() {
    const now = state.date;
    const dateStr = now.toISOString().split('T')[0];
    const weekday = ['日', '一', '二', '三', '四', '五', '六'][now.getDay()];

    // ... 现有时间计算代码 ...

    // 获取苦强指数数据
    const kuQiangData = state.kuQiangData;

    // 生成Markdown
    let markdown = `---
date: ${dateStr}
weekday: 星期${weekday}
kuqiang_index: ${kuQiangData.kuQiangIndex}
total_time: ${totalHours}h${remainingMinutes > 0 ? remainingMinutes + 'm' : ''}
---

# ${dateStr} 星期${weekday} 每日记录

## 📊 苦强指数评估

### 变强评估（苦强指数测试【1】）
- **得分**: ${kuQiangData.strengthening.score}分
- **选中项目**:
`;

    // 添加选中的变强项目
    if (kuQiangData.strengthening.selections.length === 0) {
        markdown += `  - 无选择\n`;
    } else if (kuQiangData.strengthening.selections.includes(6)) {
        markdown += `  - 以上都没有\n`;
    } else {
        kuQiangData.strengthening.selections.forEach(index => {
            if (index < strengtheningOptions.length) {
                markdown += `  - ${strengtheningOptions[index].text}\n`;
            }
        });
    }

    markdown += `
### 吃苦评估（苦强指数测试【2】）
- **坐班时长**: ${kuQiangData.suffering.officeHours}小时
- **通勤时长**: ${kuQiangData.suffering.commuteHours}小时
- **家务时长**: ${kuQiangData.suffering.houseworkHours}小时
- **总吃苦时长**: ${kuQiangData.suffering.totalHours}小时

### 最终指数
- **苦强指数**: ${kuQiangData.kuQiangIndex}
`;

    // 原有时间记录、任务列表、笔记等部分保持不变...
    // ... 后续代码 ...

    return markdown;
}
```

## 测试计划

### 单元测试
1. **计分逻辑测试**
   - 变强选项计分准确性
   - 互斥选项处理（"以上都没有"）
   - 吃苦时长计算

2. **指数计算测试**
   - 不同场景下的指数计算
   - 边界条件测试（零时间、全选中）
   - 公式验证

3. **数据持久化测试**
   - 存储/加载完整性
   - 跨日数据保留

### 集成测试
1. **与现有系统集成**
   - 页面加载无冲突
   - 数据导出功能
   - 清空数据功能

2. **用户界面测试**
   - 复选框交互
   - 时间输入验证
   - 指数计算按钮

### 用户验收测试
1. **功能完整性**
   - 所有选项正常工作
   - 计算准确性
   - 数据保存可靠

2. **用户体验**
   - 界面直观性
   - 操作流畅度
   - 结果可理解性

## 部署步骤

### 1. 备份现有版本
```bash
cp index.html index_backup_$(date +%Y%m%d_%H%M%S).html
```

### 2. 分步实施
1. **第一阶段**：HTML结构替换 + CSS样式添加
2. **第二阶段**：JavaScript核心功能实现
3. **第三阶段**：数据存储和导出集成
4. **第四阶段**：测试和调试

### 3. 验证检查清单
- [ ] 页面正常加载，无JavaScript错误
- [ ] 变强选项可以选择和取消
- [ ] 吃苦时间可以输入和计算
- [ ] 苦强指数正确计算和显示
- [ ] 数据正确保存和加载
- [ ] Markdown导出包含苦强指数信息
- [ ] 清空数据功能正常工作

## 风险与缓解

### 技术风险
1. **数据兼容性风险**：现有用户数据迁移
   - 缓解：保持原有数据结构不变，新增字段

2. **计算准确性风险**：指数公式可能需调整
   - 缓解：提供可配置的计分规则

### 用户体验风险
1. **理解成本**：用户需要理解"苦强"概念
   - 缓解：提供清晰的定义和说明

2. **操作复杂度**：两个评估部分可能较复杂
   - 缓解：保持界面简洁，提供默认值

## 成功指标

### 功能指标
- 选项选择成功率 > 98%
- 指数计算准确率 > 99%
- 数据导出完整性 100%

### 用户体验指标
- 每日使用率 > 80%
- 用户满意度得分 > 4/5
- 平均完成时间 < 2分钟

---

**文档版本**: v1.0
**创建日期**: 2026-03-29
**更新日期**: 2026-03-29
**适用版本**: 日程记录工具 v2.0