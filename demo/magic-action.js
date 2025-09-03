// 处理连字测试
document.addEventListener('DOMContentLoaded', function () {
    const testInput = document.getElementById('testInput');
    const testOutput = document.getElementById('testOutput');
    const clearButton = document.getElementById('clearButton');
    const fontSizeSlider = document.getElementById('fontSize');
    const fontSizeDisplay = document.getElementById('fontSizeDisplay');
    const modeButtons = document.querySelectorAll('.mode-button');

    // 设置当前激活的模式
    let currentMode = 'normal'; // 默认为普通模式

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

    // 处理模式切换
    modeButtons.forEach(button => {
        button.addEventListener('click', function() {
            // 获取选中的模式
            const newMode = this.getAttribute('data-mode');

            // 如果点击的是当前激活的模式，则不做任何操作
            if (newMode === currentMode) return;

            // 更新按钮状态
            modeButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            // 更新模式
            applyMode(newMode);

            // 保存当前模式
            currentMode = newMode;
        });
    });

    // 应用模式到所有图标
    function applyMode(mode) {
        // 移除所有模式类
        const allModes = ['normal', 'shadow', 'flat'];

        // 更新所有图标（支持不同的字体代码前缀）
        const iconSelectors = ['.magic-icon', '.magic-output']; // 默认的选择器

        // 查找页面上所有符合"*-icon"和"*-output"模式的元素
        document.querySelectorAll('[class*="-icon"], [class*="-output"]').forEach(element => {
            // 检查元素是否有图标或输出类
            if (element.className.includes('-icon') || element.className.includes('-output')) {
                allModes.forEach(m => element.classList.remove(m));
                element.classList.add(mode);
            }
        });
    }

    // 初始化时应用默认模式
    applyMode(currentMode);

    // 允许点击符号将其添加到测试输入框
    document.querySelectorAll('.icon-item').forEach(item => {
        item.addEventListener('click', function () {
            const ligature = this.querySelector('.icon-code').textContent;
            testInput.value += ligature;
            testOutput.textContent = testInput.value;
        });
    });
});
