// Immigration Document Extractor - Frontend JavaScript

// State
let selectedFiles = [];
let currentDocType = 'passport';

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const selectFilesBtn = document.getElementById('selectFilesBtn');
const selectedFilesContainer = document.getElementById('selectedFiles');
const processBtn = document.getElementById('processBtn');
const batchBtn = document.getElementById('batchBtn');
const progressSection = document.getElementById('progressSection');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const resultsSection = document.getElementById('resultsSection');
const resultsContainer = document.getElementById('resultsContainer');

// Document type buttons
const docTypeButtons = document.querySelectorAll('.doc-type-btn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
});

function setupEventListeners() {
    // Document type selection
    docTypeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            docTypeButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentDocType = btn.dataset.type;
        });
    });

    // File selection
    selectFilesBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);

    // Process buttons
    processBtn.addEventListener('click', processDocuments);
    batchBtn.addEventListener('click', batchProcessDocuments);
}

// File handling functions
function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    addFiles(files);
}

function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');

    const files = Array.from(e.dataTransfer.files);
    addFiles(files);
}

function addFiles(files) {
    const validExtensions = ['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'];

    files.forEach(file => {
        const extension = file.name.split('.').pop().toLowerCase();

        if (validExtensions.includes(extension) && file.size <= 16 * 1024 * 1024) {
            // Check if file already added
            if (!selectedFiles.find(f => f.name === file.name)) {
                selectedFiles.push(file);
            }
        } else {
            alert(`Arquivo inválido: ${file.name}\nAceito apenas: PDF, PNG, JPG, TIFF (máx 16MB)`);
        }
    });

    updateFilesList();
    updateButtons();
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    updateFilesList();
    updateButtons();
}

function updateFilesList() {
    selectedFilesContainer.innerHTML = '';

    selectedFiles.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';

        const fileIcon = getFileIcon(file.name);
        const fileSize = formatFileSize(file.size);

        fileItem.innerHTML = `
            <div class="file-info">
                <span class="file-icon">${fileIcon}</span>
                <div>
                    <div class="file-name">${file.name}</div>
                    <div class="file-size">${fileSize}</div>
                </div>
            </div>
            <button class="remove-file" onclick="removeFile(${index})">Remover</button>
        `;

        selectedFilesContainer.appendChild(fileItem);
    });
}

function updateButtons() {
    const hasFiles = selectedFiles.length > 0;
    processBtn.disabled = !hasFiles;
    batchBtn.disabled = !hasFiles;
}

function getFileIcon(filename) {
    const extension = filename.split('.').pop().toLowerCase();
    const icons = {
        'pdf': '📄',
        'png': '🖼️',
        'jpg': '🖼️',
        'jpeg': '🖼️',
        'tiff': '🖼️',
        'bmp': '🖼️'
    };
    return icons[extension] || '📎';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Processing functions
async function processDocuments() {
    if (selectedFiles.length === 0) return;

    // Show progress
    showProgress();
    clearResults();

    const formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append('files[]', file);
    });
    formData.append('document_type', currentDocType);

    try {
        progressText.textContent = 'Processando documentos...';
        progressFill.style.width = '50%';

        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        progressFill.style.width = '75%';

        if (!response.ok) {
            throw new Error('Erro ao processar documentos');
        }

        const data = await response.json();

        progressFill.style.width = '100%';
        progressText.textContent = 'Concluído!';

        setTimeout(() => {
            hideProgress();
            displayResults(data.results);
        }, 500);

    } catch (error) {
        hideProgress();
        showError(error.message);
    }
}

async function batchProcessDocuments() {
    if (selectedFiles.length === 0) return;

    showProgress();
    clearResults();

    const formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append('files[]', file);
    });

    try {
        progressText.textContent = 'Processando em lote (auto-detectando tipos)...';
        progressFill.style.width = '30%';

        const response = await fetch('/api/batch', {
            method: 'POST',
            body: formData
        });

        progressFill.style.width = '70%';

        if (!response.ok) {
            throw new Error('Erro ao processar documentos em lote');
        }

        const data = await response.json();

        progressFill.style.width = '100%';
        progressText.textContent = 'Concluído!';

        setTimeout(() => {
            hideProgress();
            displayBatchResults(data);
        }, 500);

    } catch (error) {
        hideProgress();
        showError(error.message);
    }
}

// UI functions
function showProgress() {
    progressSection.style.display = 'block';
    progressFill.style.width = '0%';
    processBtn.disabled = true;
    batchBtn.disabled = true;
}

function hideProgress() {
    progressSection.style.display = 'none';
    processBtn.disabled = false;
    batchBtn.disabled = false;
}

function clearResults() {
    resultsSection.style.display = 'none';
    resultsContainer.innerHTML = '';
}

function displayResults(results) {
    resultsSection.style.display = 'block';
    resultsContainer.innerHTML = '';

    results.forEach(result => {
        const resultCard = createResultCard(result);
        resultsContainer.appendChild(resultCard);
    });
}

function displayBatchResults(data) {
    resultsSection.style.display = 'block';
    resultsContainer.innerHTML = '';

    const batchCard = document.createElement('div');
    batchCard.className = 'result-card success';

    batchCard.innerHTML = `
        <div class="result-header">
            <h3 class="result-filename">
                📦 Processamento em Lote
            </h3>
            <span class="result-status success">✓ Sucesso</span>
        </div>
        <div class="result-data">
            <div class="data-field">
                <span class="field-label">Total de documentos:</span>
                <span class="field-value">${data.total_documents}</span>
            </div>
        </div>
    `;

    resultsContainer.appendChild(batchCard);

    // Show individual document info if available
    if (data.combined_data && data.combined_data.metadata && data.combined_data.metadata.documents) {
        const docsInfo = document.createElement('div');
        docsInfo.style.marginTop = '1rem';
        docsInfo.innerHTML = '<h4>Documentos processados:</h4>';

        const docsList = document.createElement('div');
        docsList.className = 'result-data';

        data.combined_data.metadata.documents.forEach((doc, index) => {
            const docField = document.createElement('div');
            docField.className = 'data-field';
            docField.innerHTML = `
                <span class="field-label">Documento ${index + 1}:</span>
                <span class="field-value">${doc.source_file} (${doc.type || doc.category})</span>
            `;
            docsList.appendChild(docField);
        });

        docsInfo.appendChild(docsList);
        batchCard.appendChild(docsInfo);
    }
}

function createResultCard(result) {
    const card = document.createElement('div');
    card.className = `result-card ${result.success ? 'success' : 'error'}`;

    const statusIcon = result.success ? '✓' : '✗';
    const statusText = result.success ? 'Sucesso' : 'Erro';

    let contentHTML = '';

    if (result.success) {
        // Show markdown content with copy button
        const markdownId = `markdown-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const markdownText = result.markdown_content || 'Nenhum dado foi extraído.';

        contentHTML = `
            <div class="markdown-container">
                <div class="markdown-header">
                    <h4>Dados Extraídos</h4>
                    <button class="copy-btn" onclick="copyMarkdown('${markdownId}')">
                        📋 Copiar
                    </button>
                </div>
                <textarea id="${markdownId}" class="markdown-content" readonly>${markdownText}</textarea>
            </div>
        `;
    } else {
        // Show detailed error message
        const errorMsg = result.error || 'Erro desconhecido ao processar o documento.';
        contentHTML = `
            <div class="error-details">
                <h4>Descrição do Erro:</h4>
                <p>${errorMsg}</p>
            </div>
        `;
    }

    card.innerHTML = `
        <div class="result-header">
            <h3 class="result-filename">
                ${getFileIcon(result.filename)} ${result.filename}
            </h3>
            <span class="result-status ${result.success ? 'success' : 'error'}">
                ${statusIcon} ${statusText}
            </span>
        </div>
        ${result.extraction_method ? `
            <div style="margin-bottom: 1rem; color: #64748b; font-size: 0.9rem;">
                Método: ${result.extraction_method}
            </div>
        ` : ''}
        ${contentHTML}
    `;

    return card;
}

// Copy markdown to clipboard
function copyMarkdown(elementId) {
    const textarea = document.getElementById(elementId);
    textarea.select();
    document.execCommand('copy');

    // Show feedback
    const copyBtn = event.target;
    const originalText = copyBtn.innerHTML;
    copyBtn.innerHTML = '✓ Copiado!';
    copyBtn.style.background = '#10b981';

    setTimeout(() => {
        copyBtn.innerHTML = originalText;
        copyBtn.style.background = '';
    }, 2000);
}

// Make copyMarkdown available globally
window.copyMarkdown = copyMarkdown;

function showError(message) {
    resultsSection.style.display = 'block';
    resultsContainer.innerHTML = `
        <div class="error-message">
            <strong>Erro:</strong> ${message}
        </div>
    `;
}

// Make removeFile available globally
window.removeFile = removeFile;
