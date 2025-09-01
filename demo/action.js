// 处理连字测试
document.addEventListener('DOMContentLoaded', function () {
    const testInput = document.getElementById('testInput');
    const testOutput = document.getElementById('testOutput');
    const clearButton = document.getElementById('clearButton');
    const fontSizeSlider = document.getElementById('fontSize');
    const fontSizeDisplay = document.getElementById('fontSizeDisplay');
    const shadowToggle = document.getElementById('shadowToggle');

    // 设置全局阴影状态变量
    let shadowMode = false;

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

    // 处理阴影模式切换
    shadowToggle.addEventListener('change', function() {
        shadowMode = this.checked;

        // 更新测试输出区域
        if (shadowMode) {
            testOutput.classList.add('shadow-mode');
        } else {
            testOutput.classList.remove('shadow-mode');
        }

        // 更新所有图标
        document.querySelectorAll('.magic-icon').forEach(icon => {
            if (shadowMode) {
                icon.classList.add('shadow-mode');
            } else {
                icon.classList.remove('shadow-mode');
            }
        });
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
