// 处理连字测试
document.addEventListener('DOMContentLoaded', function () {
    const testInput = document.getElementById('testInput');
    const testOutput = document.getElementById('testOutput');
    const clearButton = document.getElementById('clearButton');
    const fontSizeSlider = document.getElementById('fontSize');
    const fontSizeDisplay = document.getElementById('fontSizeDisplay');

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
