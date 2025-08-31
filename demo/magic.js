// 符号数据
const symbolData = [
    // 基本法术力
    { name: 'white', ligature: '{W}', category: 'basicMana' },
    { name: 'blue', ligature: '{U}', category: 'basicMana' },
    { name: 'black', ligature: '{B}', category: 'basicMana' },
    { name: 'red', ligature: '{R}', category: 'basicMana' },
    { name: 'green', ligature: '{G}', category: 'basicMana' },
    { name: 'colorless', ligature: '{C}', category: 'basicMana' },
    { name: 'tap', ligature: '{T}', category: 'basicMana' },
    { name: 'untap', ligature: '{Q}', category: 'basicMana' },
    { name: 'energy', ligature: '{E}', category: 'basicMana' },
    { name: 'chaos', ligature: '{CHAOS}', category: 'basicMana' },
    { name: 'planeswalker', ligature: '{PW}', category: 'basicMana' },

    // 数字法术力
    { name: '0', ligature: '{0}', category: 'numericMana' },
    { name: '1', ligature: '{1}', category: 'numericMana' },
    { name: '2', ligature: '{2}', category: 'numericMana' },
    { name: '3', ligature: '{3}', category: 'numericMana' },
    { name: '4', ligature: '{4}', category: 'numericMana' },
    { name: '5', ligature: '{5}', category: 'numericMana' },
    { name: '6', ligature: '{6}', category: 'numericMana' },
    { name: '7', ligature: '{7}', category: 'numericMana' },
    { name: '8', ligature: '{8}', category: 'numericMana' },
    { name: '9', ligature: '{9}', category: 'numericMana' },
    { name: '10', ligature: '{10}', category: 'numericMana' },
    { name: '11', ligature: '{11}', category: 'numericMana' },
    { name: '12', ligature: '{12}', category: 'numericMana' },
    { name: '13', ligature: '{13}', category: 'numericMana' },
    { name: '14', ligature: '{14}', category: 'numericMana' },
    { name: '15', ligature: '{15}', category: 'numericMana' },
    { name: '16', ligature: '{16}', category: 'numericMana' },
    { name: '17', ligature: '{17}', category: 'numericMana' },
    { name: '18', ligature: '{18}', category: 'numericMana' },
    { name: '19', ligature: '{19}', category: 'numericMana' },
    { name: '20', ligature: '{20}', category: 'numericMana' },
    { name: '100', ligature: '{100}', category: 'numericMana' },
    { name: '1000000', ligature: '{1000000}', category: 'numericMana' },

    // 混色法术力
    { name: 'white-blue', ligature: '{W/U}', category: 'hybridMana' },
    { name: 'white-black', ligature: '{W/B}', category: 'hybridMana' },
    { name: 'blue-black', ligature: '{U/B}', category: 'hybridMana' },
    { name: 'blue-red', ligature: '{U/R}', category: 'hybridMana' },
    { name: 'black-red', ligature: '{B/R}', category: 'hybridMana' },
    { name: 'black-green', ligature: '{B/G}', category: 'hybridMana' },
    { name: 'red-green', ligature: '{R/G}', category: 'hybridMana' },
    { name: 'red-white', ligature: '{R/W}', category: 'hybridMana' },
    { name: 'green-white', ligature: '{G/W}', category: 'hybridMana' },
    { name: 'green-blue', ligature: '{G/U}', category: 'hybridMana' },

    // 费雷西亚法术力
    { name: 'white-phyrexian', ligature: '{W/P}', category: 'phyrexianMana' },
    { name: 'blue-phyrexian', ligature: '{U/P}', category: 'phyrexianMana' },
    { name: 'black-phyrexian', ligature: '{B/P}', category: 'phyrexianMana' },
    { name: 'red-phyrexian', ligature: '{R/P}', category: 'phyrexianMana' },
    { name: 'green-phyrexian', ligature: '{G/P}', category: 'phyrexianMana' },

    // 特殊符号
    { name: 'x', ligature: '{X}', category: 'specialSymbols' },
    { name: 'y', ligature: '{Y}', category: 'specialSymbols' },
    { name: 'z', ligature: '{Z}', category: 'specialSymbols' },
    { name: 'infinity', ligature: '{∞}', category: 'specialSymbols' },
    { name: 'half', ligature: '{½}', category: 'specialSymbols' },
];

// 动态生成符号展示
function renderSymbols() {
    const categories = ['basicMana', 'numericMana', 'hybridMana', 'phyrexianMana', 'specialSymbols'];

    categories.forEach(category => {
        const container = document.getElementById(category);
        const categorySymbols = symbolData.filter(symbol => symbol.category === category);

        categorySymbols.forEach(symbol => {
            const item = document.createElement('div');
            item.className = 'icon-item';

            item.innerHTML = `
        <i class="magic-icon icon-display">${symbol.ligature}</i>
        <div class="icon-name">${symbol.name}</div>
        <div class="icon-code">${symbol.ligature}</div>
      `;

            container.appendChild(item);
        });
    });
}

// 处理连字测试
document.addEventListener('DOMContentLoaded', function () {
    const testInput = document.getElementById('testInput');
    const testOutput = document.getElementById('testOutput');
    const clearButton = document.getElementById('clearButton');
    const fontSizeSlider = document.getElementById('fontSize');
    const fontSizeDisplay = document.getElementById('fontSizeDisplay');

    // 渲染符号
    renderSymbols();

    // 处理输入
    testInput.addEventListener('input', function () {
        testOutput.textContent = this.value;
    });

    // 处理清空按钮
    clearButton.addEventListener('click', function () {
        testInput.value = '';
        testOutput.textContent = '';
    });

    // 处理字体大小
    fontSizeSlider.addEventListener('input', function () {
        const size = this.value;
        testOutput.style.fontSize = `${size}px`;
        fontSizeDisplay.textContent = `${size}px`;
    });

    // 允许点击符号将其添加到测试输入框
    document.querySelectorAll('.icon-item').forEach(item => {
        item.addEventListener('click', function () {
            const ligature = this.querySelector('.icon-code').textContent;
            testInput.value += ligature;
            testOutput.textContent = testInput.value;
        });
    });
});
