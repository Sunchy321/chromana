document.addEventListener('DOMContentLoaded', () => {
    // Load icon JSON data
    fetch('../dist/chromana-icons.json') // This path will be './chromana-icons.json' in production
        .then(response => response.json())
        .then(data => {
            const iconGrid = document.getElementById('iconGrid');

            // Dynamically create icon list
            data.icons.forEach(icon => {
                const iconItem = document.createElement('div');
                iconItem.className = 'icon-item';

                const iconDisplay = document.createElement('span');
                iconDisplay.className = `cm ${icon.class}`;
                iconDisplay.classList.add('icon-display');

                const iconName = document.createElement('span');
                iconName.className = 'icon-name';
                iconName.textContent = icon.name;

                iconItem.appendChild(iconDisplay);
                iconItem.appendChild(iconName);
                iconGrid.appendChild(iconItem);
            });
        })
        .catch(error => {
            console.error('Failed to load icon data:', error);
            document.getElementById('iconGrid').innerHTML = '<p>Error loading icon data. Please run the build script first (npm run build).</p>';
        });

    // Ligature demo functionality
    const textInput = document.getElementById('textInput');
    const ligatureDisplay = document.getElementById('ligatureDisplay');

    textInput.addEventListener('input', () => {
        ligatureDisplay.textContent = textInput.value;
    });
});
