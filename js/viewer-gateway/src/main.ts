import './style.css';
import { buildImageIds, createStackViewer } from './viewerGateway';

const root = document.getElementById('app') as HTMLDivElement;
const viewportDiv = document.createElement('div');
viewportDiv.style.width = '512px';
viewportDiv.style.height = '512px';
viewportDiv.style.background = 'black';
root.appendChild(viewportDiv);

const info = document.createElement('p');
info.textContent = 'Loading sample_series via wadouri...';
root.appendChild(info);

// Adjust base URL to wherever you serve sample_series over HTTP
const baseUrl = 'http://localhost:8080/sample_series';
const imageIds = buildImageIds(baseUrl, 174);

createStackViewer({
  element: viewportDiv,
  imageIds,
})
  .then(() => {
    info.textContent = `Loaded ${imageIds.length} slices from ${baseUrl}`;
  })
  .catch((err) => {
    console.error(err);
    info.textContent = `Failed to load series: ${String(err)}`;
  });
