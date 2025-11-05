// API Configuration
const API_BASE = 'http://localhost:5000/api';

// Global state
let currentFileId = null;
let currentExpenseData = null;
let allCategories = [];
let allVendors = [];

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeNavigation();
    initializeUpload();
    initializeExpenses();
    initializeReports();
    initializeDashboard();
    loadCategories();
});

// Navigation
function initializeNavigation() {
    const navBtns = document.querySelectorAll('.nav-btn');
    const views = document.querySelectorAll('.view');

    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetView = btn.dataset.view;

            // Update active states
            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            views.forEach(v => v.classList.remove('active'));
            document.getElementById(`${targetView}-view`).classList.add('active');

            // Load data for specific views
            if (targetView === 'expenses') {
                loadExpenses();
            } else if (targetView === 'dashboard') {
                loadDashboard();
            }
        });
    });
}

// Upload functionality
function initializeUpload() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');

    // Browse button
    browseBtn.addEventListener('click', () => fileInput.click());

    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    // Drag and drop
    uploadArea.addEventListener('click', () => fileInput.click());

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');

        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    // Form submission
    document.getElementById('expense-form').addEventListener('submit', handleFormSubmit);

    // Cancel button
    document.getElementById('cancel-btn').addEventListener('click', resetUploadForm);

    // Upload another button
    document.getElementById('upload-another-btn').addEventListener('click', resetUploadForm);

    // Vendor input change for category suggestions
    document.getElementById('vendor').addEventListener('input', debounce(updateCategorySuggestions, 500));
}

async function handleFileUpload(file) {
    try {
        // Show pipeline
        document.getElementById('pipeline').style.display = 'block';
        updatePipelineStep('upload', 'active');

        // Upload file
        const formData = new FormData();
        formData.append('file', file);

        const uploadResponse = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!uploadResponse.ok) {
            throw new Error('Upload failed');
        }

        const uploadData = await uploadResponse.json();
        currentFileId = uploadData.file_id;

        updatePipelineStep('upload', 'completed');
        updatePipelineStep('extract', 'active');

        // Extract data
        const extractResponse = await fetch(`${API_BASE}/extract/${currentFileId}`, {
            method: 'POST'
        });

        if (!extractResponse.ok) {
            throw new Error('Extraction failed');
        }

        const extractData = await extractResponse.json();
        currentExpenseData = extractData.data;

        updatePipelineStep('extract', 'completed');
        updatePipelineStep('review', 'active');

        // Show extraction form
        populateForm(currentExpenseData, uploadData.original_name);
        document.getElementById('extraction-form').style.display = 'block';

        // Update category suggestions
        await updateCategorySuggestions();

    } catch (error) {
        showToast('Error processing file: ' + error.message, 'error');
        resetUploadForm();
    }
}

function populateForm(data, originalFilename) {
    document.getElementById('file-id').value = currentFileId;
    document.getElementById('vendor').value = data.vendor || '';
    document.getElementById('amount').value = data.amount || '';

    // Format date for input
    const dateInput = document.getElementById('date');
    if (data.date) {
        dateInput.value = data.date;
    }

    document.getElementById('invoice-number').value = data.invoice_number || '';
    document.getElementById('description').value = data.description || '';

    // Update confidence indicator
    const confidence = data.confidence || 0;
    document.getElementById('confidence-fill').style.width = `${confidence}%`;
    document.getElementById('confidence-text').textContent = `${confidence}%`;

    // Store original filename
    currentExpenseData.original_filename = originalFilename;
}

async function updateCategorySuggestions() {
    const vendor = document.getElementById('vendor').value;
    const description = document.getElementById('description').value;

    if (!vendor) return;

    try {
        const response = await fetch(`${API_BASE}/categorize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ vendor, description })
        });

        const data = await response.json();
        displayCategorySuggestions(data.suggestions);
    } catch (error) {
        console.error('Error getting category suggestions:', error);
    }
}

function displayCategorySuggestions(suggestions) {
    const container = document.getElementById('category-suggestions');
    container.innerHTML = '';

    if (!suggestions || suggestions.length === 0) return;

    suggestions.slice(0, 3).forEach(suggestion => {
        const chip = document.createElement('div');
        chip.className = 'suggestion-chip';
        chip.innerHTML = `
            ${suggestion.category}
            <span class="confidence">(${suggestion.confidence}%)</span>
        `;
        chip.addEventListener('click', () => {
            document.getElementById('category').value = suggestion.category;
        });
        container.appendChild(chip);
    });
}

async function handleFormSubmit(e) {
    e.preventDefault();

    updatePipelineStep('review', 'completed');
    updatePipelineStep('categorize', 'active');

    const formData = {
        file_id: currentFileId,
        expense_data: {
            vendor: document.getElementById('vendor').value,
            amount: parseFloat(document.getElementById('amount').value),
            date: document.getElementById('date').value,
            category: document.getElementById('category').value,
            invoice_number: document.getElementById('invoice-number').value,
            description: document.getElementById('description').value,
            notes: document.getElementById('notes').value,
            original_filename: currentExpenseData.original_filename
        }
    };

    try {
        const response = await fetch(`${API_BASE}/process`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error('Processing failed');
        }

        const result = await response.json();

        updatePipelineStep('categorize', 'completed');
        updatePipelineStep('complete', 'active');

        setTimeout(() => {
            updatePipelineStep('complete', 'completed');
            showSuccessMessage(result);
        }, 500);

    } catch (error) {
        showToast('Error processing document: ' + error.message, 'error');
    }
}

function showSuccessMessage(result) {
    document.getElementById('extraction-form').style.display = 'none';
    document.getElementById('pipeline').style.display = 'none';

    const successMessage = document.getElementById('success-message');
    const details = document.getElementById('success-details');

    details.innerHTML = `
        <p><strong>File:</strong> ${result.filename}</p>
        <p><strong>Location:</strong> ${result.final_path}</p>
        <p>Your document has been organized and is ready for review in your expenses!</p>
    `;

    successMessage.style.display = 'block';
    showToast('Document processed successfully!', 'success');
}

function resetUploadForm() {
    document.getElementById('pipeline').style.display = 'none';
    document.getElementById('extraction-form').style.display = 'none';
    document.getElementById('success-message').style.display = 'none';
    document.getElementById('expense-form').reset();
    document.getElementById('file-input').value = '';

    // Reset pipeline steps
    document.querySelectorAll('.pipeline-step').forEach(step => {
        step.classList.remove('active', 'completed');
    });

    currentFileId = null;
    currentExpenseData = null;
}

function updatePipelineStep(step, status) {
    const stepElement = document.querySelector(`.pipeline-step[data-step="${step}"]`);
    stepElement.classList.remove('active', 'completed');

    if (status) {
        stepElement.classList.add(status);
    }
}

// Expenses functionality
function initializeExpenses() {
    document.getElementById('search-input').addEventListener('input', debounce(loadExpenses, 300));
    document.getElementById('filter-category').addEventListener('change', loadExpenses);
    document.getElementById('filter-vendor').addEventListener('change', loadExpenses);
    document.getElementById('filter-start-date').addEventListener('change', loadExpenses);
    document.getElementById('filter-end-date').addEventListener('change', loadExpenses);
    document.getElementById('clear-filters-btn').addEventListener('click', clearExpenseFilters);
}

async function loadExpenses() {
    const params = new URLSearchParams();
    const search = document.getElementById('search-input').value;
    const category = document.getElementById('filter-category').value;
    const vendor = document.getElementById('filter-vendor').value;
    const startDate = document.getElementById('filter-start-date').value;
    const endDate = document.getElementById('filter-end-date').value;

    if (search) params.append('search', search);
    if (category) params.append('category', category);
    if (vendor) params.append('vendor', vendor);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    try {
        const response = await fetch(`${API_BASE}/expenses?${params}`);
        const data = await response.json();
        displayExpenses(data.expenses);
    } catch (error) {
        showToast('Error loading expenses', 'error');
    }
}

function displayExpenses(expenses) {
    const container = document.getElementById('expenses-list');

    if (!expenses || expenses.length === 0) {
        container.innerHTML = '<div class="empty-state">No expenses found. Upload some documents to get started!</div>';
        return;
    }

    container.innerHTML = expenses.map(expense => `
        <div class="expense-card">
            <div class="expense-header">
                <div>
                    <div class="expense-vendor">${expense.vendor}</div>
                    <div class="expense-category">${expense.category}</div>
                </div>
                <div class="expense-amount">$${expense.amount.toFixed(2)}</div>
            </div>
            <div class="expense-details">
                <div class="expense-detail">📅 ${formatDate(expense.date)}</div>
                ${expense.invoice_number ? `<div class="expense-detail">🔖 ${expense.invoice_number}</div>` : ''}
                <div class="expense-detail">📝 ${expense.description}</div>
            </div>
            ${expense.notes ? `<div style="margin-top: 0.8rem; color: var(--text-light); font-size: 0.9rem;">💬 ${expense.notes}</div>` : ''}
        </div>
    `).join('');
}

function clearExpenseFilters() {
    document.getElementById('search-input').value = '';
    document.getElementById('filter-category').value = '';
    document.getElementById('filter-vendor').value = '';
    document.getElementById('filter-start-date').value = '';
    document.getElementById('filter-end-date').value = '';
    loadExpenses();
}

// Reports functionality
function initializeReports() {
    document.getElementById('generate-report-btn').addEventListener('click', generateReport);
    document.getElementById('export-csv-btn').addEventListener('click', exportReport);
}

async function generateReport() {
    const reportType = document.getElementById('report-type').value;
    const startDate = document.getElementById('report-start-date').value;
    const endDate = document.getElementById('report-end-date').value;

    const filters = {};
    if (startDate) filters.start_date = startDate;
    if (endDate) filters.end_date = endDate;

    try {
        const response = await fetch(`${API_BASE}/report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: reportType, filters })
        });

        const data = await response.json();
        displayReport(reportType, data.report);
    } catch (error) {
        showToast('Error generating report', 'error');
    }
}

function displayReport(reportType, report) {
    const container = document.getElementById('report-content');

    if (reportType === 'summary') {
        container.innerHTML = `
            <div class="report-section">
                <h3>Summary Report</h3>
                <div class="report-summary">
                    <div class="stat-card">
                        <div class="stat-label">Total Expenses</div>
                        <div class="stat-value">${report.total_expenses}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Total Amount</div>
                        <div class="stat-value">$${report.total_amount.toFixed(2)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Average Amount</div>
                        <div class="stat-value">$${report.average_amount.toFixed(2)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Date Range</div>
                        <div class="stat-value" style="font-size: 1.2rem;">
                            ${report.date_range.start ? formatDate(report.date_range.start) : 'N/A'} -
                            ${report.date_range.end ? formatDate(report.date_range.end) : 'N/A'}
                        </div>
                    </div>
                </div>

                <h4>By Category</h4>
                <table class="report-table">
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Count</th>
                            <th>Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${report.categories.map(cat => `
                            <tr>
                                <td>${cat.category}</td>
                                <td>${cat.count}</td>
                                <td>$${cat.total.toFixed(2)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>

                <h4 style="margin-top: 2rem;">Top Vendors</h4>
                <table class="report-table">
                    <thead>
                        <tr>
                            <th>Vendor</th>
                            <th>Count</th>
                            <th>Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${report.top_vendors.map(vendor => `
                            <tr>
                                <td>${vendor.vendor}</td>
                                <td>${vendor.count}</td>
                                <td>$${vendor.total.toFixed(2)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } else if (reportType === 'by_category') {
        container.innerHTML = `
            <div class="report-section">
                <h3>Expenses by Category</h3>
                <div class="report-summary">
                    <div class="stat-card">
                        <div class="stat-label">Total Amount</div>
                        <div class="stat-value">$${report.total_amount.toFixed(2)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Total Expenses</div>
                        <div class="stat-value">${report.total_expenses}</div>
                    </div>
                </div>
                ${report.categories.map(cat => `
                    <div style="margin-top: 2rem;">
                        <h4>${cat.category} (${cat.count} expenses - $${cat.total.toFixed(2)})</h4>
                        <table class="report-table">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Vendor</th>
                                    <th>Amount</th>
                                    <th>Description</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${cat.expenses.map(exp => `
                                    <tr>
                                        <td>${formatDate(exp.date)}</td>
                                        <td>${exp.vendor}</td>
                                        <td>$${exp.amount.toFixed(2)}</td>
                                        <td>${exp.description}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                `).join('')}
            </div>
        `;
    } else if (reportType === 'by_vendor') {
        container.innerHTML = `
            <div class="report-section">
                <h3>Expenses by Vendor</h3>
                <div class="report-summary">
                    <div class="stat-card">
                        <div class="stat-label">Total Amount</div>
                        <div class="stat-value">$${report.total_amount.toFixed(2)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Total Expenses</div>
                        <div class="stat-value">${report.total_expenses}</div>
                    </div>
                </div>
                <table class="report-table">
                    <thead>
                        <tr>
                            <th>Vendor</th>
                            <th>Count</th>
                            <th>Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${report.vendors.map(vendor => `
                            <tr>
                                <td>${vendor.vendor}</td>
                                <td>${vendor.count}</td>
                                <td>$${vendor.total.toFixed(2)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } else if (reportType === 'monthly') {
        container.innerHTML = `
            <div class="report-section">
                <h3>Monthly Breakdown</h3>
                <div class="report-summary">
                    <div class="stat-card">
                        <div class="stat-label">Total Amount</div>
                        <div class="stat-value">$${report.total_amount.toFixed(2)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Total Expenses</div>
                        <div class="stat-value">${report.total_expenses}</div>
                    </div>
                </div>
                ${report.months.map(month => `
                    <div style="margin-top: 2rem;">
                        <h4>${month.month_name} (${month.count} expenses - $${month.total.toFixed(2)})</h4>
                        <table class="report-table">
                            <thead>
                                <tr>
                                    <th>Category</th>
                                    <th>Count</th>
                                    <th>Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${month.categories.map(cat => `
                                    <tr>
                                        <td>${cat.category}</td>
                                        <td>${cat.count}</td>
                                        <td>$${cat.total.toFixed(2)}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                `).join('')}
            </div>
        `;
    }
}

async function exportReport() {
    const reportType = document.getElementById('report-type').value;
    const startDate = document.getElementById('report-start-date').value;
    const endDate = document.getElementById('report-end-date').value;

    const filters = {};
    if (startDate) filters.start_date = startDate;
    if (endDate) filters.end_date = endDate;

    try {
        const response = await fetch(`${API_BASE}/report/export`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: reportType, filters })
        });

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'expense_report.csv';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showToast('Report exported successfully!', 'success');
    } catch (error) {
        showToast('Error exporting report', 'error');
    }
}

// Dashboard functionality
function initializeDashboard() {
    // Dashboard will load when view is activated
}

async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const data = await response.json();
        displayDashboard(data.stats);
    } catch (error) {
        showToast('Error loading dashboard', 'error');
    }
}

function displayDashboard(stats) {
    const container = document.getElementById('dashboard-grid');

    container.innerHTML = `
        <div class="stat-card">
            <div class="stat-label">Total Expenses</div>
            <div class="stat-value">${stats.total_expenses}</div>
            <div class="stat-subtitle">documents processed</div>
        </div>

        <div class="stat-card">
            <div class="stat-label">Total Amount</div>
            <div class="stat-value">$${stats.total_amount.toFixed(2)}</div>
            <div class="stat-subtitle">in tracked expenses</div>
        </div>

        <div class="stat-card">
            <div class="stat-label">Categories</div>
            <div class="stat-value">${Object.keys(stats.by_category).length}</div>
            <div class="stat-subtitle">expense categories</div>
        </div>

        <div class="stat-card">
            <div class="stat-label">Vendors</div>
            <div class="stat-value">${Object.keys(stats.by_vendor).length}</div>
            <div class="stat-subtitle">unique vendors</div>
        </div>

        <div class="stat-card" style="grid-column: span 2;">
            <h3 style="margin-bottom: 1rem;">Recent Expenses</h3>
            ${stats.recent_expenses.slice(0, 5).map(exp => `
                <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid var(--border-color);">
                    <div>
                        <strong>${exp.vendor}</strong>
                        <div style="font-size: 0.9rem; color: var(--text-light);">${formatDate(exp.date)} • ${exp.category}</div>
                    </div>
                    <div style="font-size: 1.2rem; font-weight: 700; color: var(--accent-color);">$${exp.amount.toFixed(2)}</div>
                </div>
            `).join('')}
        </div>

        <div class="stat-card" style="grid-column: span 2;">
            <h3 style="margin-bottom: 1rem;">Top Categories</h3>
            <table class="report-table">
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Count</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
                    ${Object.entries(stats.by_category)
                        .sort((a, b) => b[1].total - a[1].total)
                        .slice(0, 5)
                        .map(([cat, data]) => `
                            <tr>
                                <td>${cat}</td>
                                <td>${data.count}</td>
                                <td>$${data.total.toFixed(2)}</td>
                            </tr>
                        `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

// Load categories and vendors
async function loadCategories() {
    try {
        const [categoriesRes, vendorsRes] = await Promise.all([
            fetch(`${API_BASE}/categories`),
            fetch(`${API_BASE}/vendors`)
        ]);

        const categoriesData = await categoriesRes.json();
        const vendorsData = await vendorsRes.json();

        allCategories = categoriesData.categories;
        allVendors = vendorsData.vendors;

        populateCategorySelects();
        populateVendorSelects();
    } catch (error) {
        console.error('Error loading categories and vendors:', error);
    }
}

function populateCategorySelects() {
    const selects = [
        document.getElementById('category'),
        document.getElementById('filter-category')
    ];

    selects.forEach(select => {
        const currentValue = select.value;
        const isFilter = select.id === 'filter-category';

        if (isFilter) {
            select.innerHTML = '<option value="">All Categories</option>';
        } else {
            select.innerHTML = '<option value="">Select a category...</option>';
        }

        allCategories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            select.appendChild(option);
        });

        if (currentValue) {
            select.value = currentValue;
        }
    });
}

function populateVendorSelects() {
    const select = document.getElementById('filter-vendor');
    select.innerHTML = '<option value="">All Vendors</option>';

    allVendors.forEach(vendor => {
        const option = document.createElement('option');
        option.value = vendor;
        option.textContent = vendor;
        select.appendChild(option);
    });
}

// Utility functions
function formatDate(dateStr) {
    if (!dateStr) return 'N/A';

    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch {
        return dateStr;
    }
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    toast.innerHTML = `
        <div class="toast-icon">${icons[type]}</div>
        <div>${message}</div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
