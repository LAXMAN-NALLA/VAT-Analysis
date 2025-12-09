# React Integration Guide - VAT Analysis API

**Base URL:** `https://vat-analysis.onrender.com`

This guide helps React developers integrate with the VAT Analysis API.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication & User Management](#authentication--user-management)
3. [API Client Setup](#api-client-setup)
4. [Core Features Integration](#core-features-integration)
5. [Complete React Examples](#complete-react-examples)
6. [Error Handling](#error-handling)
7. [State Management](#state-management)
8. [Best Practices](#best-practices)

---

## Quick Start

### 1. Install Dependencies

```bash
npm install axios
# or
yarn add axios
```

### 2. Create API Client

Create `src/services/vatApi.js`:

```javascript
import axios from 'axios';

const API_BASE_URL = 'https://vat-analysis.onrender.com';

// Create axios instance with default config
const vatApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default vatApi;
```

---

## Authentication & User Management

### User ID Concept

The API uses **User ID** as the primary identifier. This should be:
- Stored in your app's state/context
- Sent as a header in every request (except `/health`)
- Unique per user/session

### Implementation Options

#### Option 1: User ID from Authentication System

```javascript
// If you have user authentication
const userId = user.id; // From your auth system
// or
const userId = sessionStorage.getItem('userId');
```

#### Option 2: Generate Temporary User ID

```javascript
// Generate a unique user ID for the session
const generateUserId = () => {
  let userId = localStorage.getItem('vat_user_id');
  if (!userId) {
    userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('vat_user_id', userId);
  }
  return userId;
};
```

#### Option 3: Use React Context for User ID

```javascript
// src/context/VatContext.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';

const VatContext = createContext();

export const VatProvider = ({ children }) => {
  const [userId, setUserId] = useState(() => {
    // Get from localStorage or generate new
    let id = localStorage.getItem('vat_user_id');
    if (!id) {
      id = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('vat_user_id', id);
    }
    return id;
  });

  const resetUserId = () => {
    const newId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setUserId(newId);
    localStorage.setItem('vat_user_id', newId);
  };

  return (
    <VatContext.Provider value={{ userId, setUserId, resetUserId }}>
      {children}
    </VatContext.Provider>
  );
};

export const useVat = () => {
  const context = useContext(VatContext);
  if (!context) {
    throw new Error('useVat must be used within VatProvider');
  }
  return context;
};
```

---

## API Client Setup

### Enhanced API Client with User ID

```javascript
// src/services/vatApi.js
import axios from 'axios';

const API_BASE_URL = 'https://vat-analysis.onrender.com';

const vatApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add User ID header
vatApi.interceptors.request.use(
  (config) => {
    const userId = localStorage.getItem('vat_user_id');
    if (userId) {
      config.headers['X-User-ID'] = userId;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
vatApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 400 && error.response?.data?.detail?.includes('X-User-ID')) {
      console.error('User ID is required. Please set a user ID.');
    }
    return Promise.reject(error);
  }
);

export default vatApi;
```

---

## Core Features Integration

### 1. Health Check

```javascript
// src/services/vatService.js
import vatApi from './vatApi';

export const checkHealth = async () => {
  try {
    const response = await vatApi.get('/health');
    return response.data;
  } catch (error) {
    throw new Error('API is not available');
  }
};
```

### 2. Process Invoices

```javascript
// src/services/vatService.js

/**
 * Process invoices (upload invoice data)
 * @param {Array} invoices - Array of invoice objects
 * @returns {Promise} API response
 */
export const processInvoices = async (invoices) => {
  try {
    const response = await vatApi.post('/process-invoices', invoices);
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to process invoices');
  }
};

// Invoice object structure:
const sampleInvoice = {
  date: "2025-09-25",              // Required: YYYY-MM-DD format
  type: "Purchase",                  // Required: "Purchase" or "Sales"
  currency: "EUR",                  // Optional
  file_name: "Invoice_001.pdf",     // Required: Unique identifier
  net_amount: 1000.00,             // Required: Number (can be negative for credit notes)
  vat_amount: null,                // Optional: Number or null (can be negative)
  description: "Product purchase",   // Optional
  vendor_name: "Supplier ABC",      // Required for Purchase
  customer_name: "Your Company",    // Required for Sales
  gross_amount: 1210.00,           // Optional
  vat_category: "Standard VAT",     // Required: See categories below
  vat_percentage: "21",             // Required: String "0", "9", "21", etc.
  invoice_number: "INV-001",        // Optional: For duplicate detection
  country: "NL",                    // Optional
  vendor_vat_id: "NL123456789B01",  // Optional for Purchase
  customer_vat_id: "NL987654321B01" // Optional for Sales
};
```

### 3. Get VAT Reports

```javascript
// src/services/vatService.js

/**
 * Get monthly VAT report
 * @param {string} year - Year (e.g., "2025")
 * @param {string} month - Month as number "09" or name "Sep"
 * @returns {Promise} Report data
 */
export const getMonthlyReport = async (year, month) => {
  try {
    const response = await vatApi.get('/vat-report-monthly', {
      params: { year, month }
    });
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to fetch monthly report');
  }
};

/**
 * Get quarterly VAT report
 * @param {string} year - Year (e.g., "2025")
 * @param {string} quarter - Quarter "Q1", "Q2", "Q3", or "Q4"
 * @returns {Promise} Report data
 */
export const getQuarterlyReport = async (year, quarter) => {
  try {
    const response = await vatApi.get('/vat-report-quarterly', {
      params: { year, quarter }
    });
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to fetch quarterly report');
  }
};

/**
 * Get yearly VAT report
 * @param {string} year - Year (e.g., "2025")
 * @returns {Promise} Report data
 */
export const getYearlyReport = async (year) => {
  try {
    const response = await vatApi.get('/vat-report-yearly', {
      params: { year }
    });
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to fetch yearly report');
  }
};
```

### 4. Company Details

```javascript
// src/services/vatService.js

/**
 * Set company details
 * @param {string} companyName - Company name
 * @param {string} companyVat - Company VAT number
 * @returns {Promise} API response
 */
export const setCompanyDetails = async (companyName, companyVat) => {
  try {
    const response = await vatApi.post('/company-details', null, {
      headers: {
        'X-Company-Name': companyName,
        'X-Company-VAT': companyVat,
      }
    });
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to set company details');
  }
};

/**
 * Get company details
 * @returns {Promise} Company details
 */
export const getCompanyDetails = async () => {
  try {
    const response = await vatApi.get('/company-details');
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to fetch company details');
  }
};
```

### 5. Other Useful Endpoints

```javascript
// src/services/vatService.js

/**
 * Get user info
 * @returns {Promise} User information
 */
export const getUserInfo = async () => {
  try {
    const response = await vatApi.get('/user-info');
    return response.data;
  } catch (error) {
    throw new Error('Failed to fetch user info');
  }
};

/**
 * Get VAT summary
 * @param {string} year - Year (e.g., "2025")
 * @returns {Promise} Summary data
 */
export const getVatSummary = async (year) => {
  try {
    const response = await vatApi.get('/vat-summary', {
      params: { year }
    });
    return response.data;
  } catch (error) {
    throw new Error('Failed to fetch VAT summary');
  }
};

/**
 * Clear all user data
 * @returns {Promise} API response
 */
export const clearUserData = async () => {
  try {
    const response = await vatApi.delete('/clear-user-data');
    return response.data;
  } catch (error) {
    throw new Error('Failed to clear user data');
  }
};
```

---

## Complete React Examples

### Example 1: Invoice Upload Component

```jsx
// src/components/InvoiceUpload.jsx
import React, { useState } from 'react';
import { processInvoices } from '../services/vatService';

const InvoiceUpload = () => {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleAddInvoice = () => {
    setInvoices([...invoices, {
      date: '',
      type: 'Purchase',
      file_name: '',
      net_amount: 0,
      vat_amount: null,
      description: '',
      vendor_name: '',
      customer_name: '',
      gross_amount: 0,
      vat_category: 'Standard VAT',
      vat_percentage: '21'
    }]);
  };

  const handleInvoiceChange = (index, field, value) => {
    const updated = [...invoices];
    updated[index][field] = value;
    setInvoices(updated);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await processInvoices(invoices);
      setResult(response);
      // Optionally clear form
      setInvoices([]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="invoice-upload">
      <h2>Upload Invoices</h2>
      
      {invoices.map((invoice, index) => (
        <div key={index} className="invoice-form">
          <h3>Invoice {index + 1}</h3>
          
          <div>
            <label>Date (YYYY-MM-DD):</label>
            <input
              type="date"
              value={invoice.date}
              onChange={(e) => handleInvoiceChange(index, 'date', e.target.value)}
              required
            />
          </div>

          <div>
            <label>Type:</label>
            <select
              value={invoice.type}
              onChange={(e) => handleInvoiceChange(index, 'type', e.target.value)}
            >
              <option value="Purchase">Purchase</option>
              <option value="Sales">Sales</option>
            </select>
          </div>

          <div>
            <label>File Name:</label>
            <input
              type="text"
              value={invoice.file_name}
              onChange={(e) => handleInvoiceChange(index, 'file_name', e.target.value)}
              required
            />
          </div>

          <div>
            <label>Net Amount:</label>
            <input
              type="number"
              step="0.01"
              value={invoice.net_amount}
              onChange={(e) => handleInvoiceChange(index, 'net_amount', parseFloat(e.target.value))}
              required
            />
          </div>

          <div>
            <label>VAT Amount (leave empty if 0):</label>
            <input
              type="number"
              step="0.01"
              value={invoice.vat_amount || ''}
              onChange={(e) => handleInvoiceChange(
                index, 
                'vat_amount', 
                e.target.value ? parseFloat(e.target.value) : null
              )}
            />
          </div>

          <div>
            <label>VAT Category:</label>
            <select
              value={invoice.vat_category}
              onChange={(e) => handleInvoiceChange(index, 'vat_category', e.target.value)}
            >
              <option value="Standard VAT">Standard VAT</option>
              <option value="Reduced Rate">Reduced Rate</option>
              <option value="Zero Rated">Zero Rated</option>
              <option value="EU Goods">EU Goods</option>
              <option value="EU Services">EU Services</option>
              <option value="Reverse Charge">Reverse Charge</option>
              <option value="Import">Import</option>
            </select>
          </div>

          <div>
            <label>VAT Percentage:</label>
            <input
              type="text"
              value={invoice.vat_percentage}
              onChange={(e) => handleInvoiceChange(index, 'vat_percentage', e.target.value)}
              required
            />
          </div>

          {invoice.type === 'Purchase' ? (
            <div>
              <label>Vendor Name:</label>
              <input
                type="text"
                value={invoice.vendor_name}
                onChange={(e) => handleInvoiceChange(index, 'vendor_name', e.target.value)}
                required
              />
            </div>
          ) : (
            <div>
              <label>Customer Name:</label>
              <input
                type="text"
                value={invoice.customer_name}
                onChange={(e) => handleInvoiceChange(index, 'customer_name', e.target.value)}
                required
              />
            </div>
          )}

          <div>
            <label>Description:</label>
            <input
              type="text"
              value={invoice.description}
              onChange={(e) => handleInvoiceChange(index, 'description', e.target.value)}
            />
          </div>
        </div>
      ))}

      <button onClick={handleAddInvoice}>Add Invoice</button>
      
      <button 
        onClick={handleSubmit} 
        disabled={loading || invoices.length === 0}
      >
        {loading ? 'Processing...' : 'Upload Invoices'}
      </button>

      {error && <div className="error">{error}</div>}
      
      {result && (
        <div className="success">
          <p>{result.message}</p>
          <p>Processed: {result.details.processed}</p>
          <p>Skipped: {result.details.skipped}</p>
          <p>Errors: {result.details.errors}</p>
        </div>
      )}
    </div>
  );
};

export default InvoiceUpload;
```

### Example 2: VAT Report Viewer Component

```jsx
// src/components/VatReportViewer.jsx
import React, { useState, useEffect } from 'react';
import { getMonthlyReport, getQuarterlyReport, getYearlyReport } from '../services/vatService';

const VatReportViewer = () => {
  const [reportType, setReportType] = useState('monthly');
  const [year, setYear] = useState(new Date().getFullYear().toString());
  const [month, setMonth] = useState('09');
  const [quarter, setQuarter] = useState('Q3');
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchReport = async () => {
    setLoading(true);
    setError(null);
    setReport(null);

    try {
      let data;
      switch (reportType) {
        case 'monthly':
          data = await getMonthlyReport(year, month);
          break;
        case 'quarterly':
          data = await getQuarterlyReport(year, quarter);
          break;
        case 'yearly':
          data = await getYearlyReport(year);
          break;
        default:
          throw new Error('Invalid report type');
      }
      setReport(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (year) {
      fetchReport();
    }
  }, [reportType, year, month, quarter]);

  return (
    <div className="vat-report-viewer">
      <h2>VAT Report</h2>

      <div className="report-controls">
        <select value={reportType} onChange={(e) => setReportType(e.target.value)}>
          <option value="monthly">Monthly</option>
          <option value="quarterly">Quarterly</option>
          <option value="yearly">Yearly</option>
        </select>

        <input
          type="text"
          placeholder="Year"
          value={year}
          onChange={(e) => setYear(e.target.value)}
        />

        {reportType === 'monthly' && (
          <input
            type="text"
            placeholder="Month (09 or Sep)"
            value={month}
            onChange={(e) => setMonth(e.target.value)}
          />
        )}

        {reportType === 'quarterly' && (
          <select value={quarter} onChange={(e) => setQuarter(e.target.value)}>
            <option value="Q1">Q1</option>
            <option value="Q2">Q2</option>
            <option value="Q3">Q3</option>
            <option value="Q4">Q4</option>
          </select>
        )}

        <button onClick={fetchReport}>Refresh</button>
      </div>

      {loading && <div>Loading...</div>}
      {error && <div className="error">{error}</div>}

      {report && (
        <div className="report-content">
          <h3>Report: {report.period}</h3>
          
          <div className="vat-calculation">
            <h4>VAT Calculation</h4>
            <p>VAT Collected: €{report.vat_calculation.vat_collected.toFixed(2)}</p>
            <p>VAT Deductible: €{report.vat_calculation.vat_deductible.toFixed(2)}</p>
            <p><strong>VAT Payable: €{report.vat_calculation.vat_payable.toFixed(2)}</strong></p>
          </div>

          <div className="categories">
            <h4>Categories</h4>
            {Object.entries(report.categories).map(([code, category]) => (
              category.totals.net !== 0 && (
                <div key={code} className="category">
                  <h5>{category.name} ({code})</h5>
                  <p>Net: €{category.totals.net.toFixed(2)}</p>
                  <p>VAT: €{category.totals.vat.toFixed(2)}</p>
                  
                  <div className="transactions">
                    {category.transactions.map((tx, idx) => (
                      <div key={idx} className="transaction">
                        <p>Date: {tx.date}</p>
                        <p>Invoice: {tx.invoice_no}</p>
                        <p>Description: {tx.description}</p>
                        <p>Net: €{tx.net_amount.toFixed(2)}</p>
                        <p>VAT: €{tx.vat_amount.toFixed(2)}</p>
                        {tx.vendor_name && <p>Vendor: {tx.vendor_name}</p>}
                        {tx.customer_name && <p>Customer: {tx.customer_name}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              )
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default VatReportViewer;
```

### Example 3: Company Details Component

```jsx
// src/components/CompanyDetails.jsx
import React, { useState, useEffect } from 'react';
import { getCompanyDetails, setCompanyDetails } from '../services/vatService';

const CompanyDetails = () => {
  const [companyName, setCompanyName] = useState('');
  const [companyVat, setCompanyVat] = useState('');
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadCompanyDetails();
  }, []);

  const loadCompanyDetails = async () => {
    try {
      const data = await getCompanyDetails();
      if (data.company_name && data.company_name !== 'N/A') {
        setCompanyName(data.company_name);
        setCompanyVat(data.company_vat);
      }
    } catch (err) {
      console.error('Failed to load company details:', err);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSaved(false);

    try {
      await setCompanyDetails(companyName, companyVat);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="company-details">
      <h2>Company Details</h2>
      
      <form onSubmit={handleSave}>
        <div>
          <label>Company Name:</label>
          <input
            type="text"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            required
          />
        </div>

        <div>
          <label>Company VAT Number:</label>
          <input
            type="text"
            value={companyVat}
            onChange={(e) => setCompanyVat(e.target.value)}
            required
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Saving...' : 'Save Company Details'}
        </button>
      </form>

      {saved && <div className="success">Company details saved successfully!</div>}
      {error && <div className="error">{error}</div>}
    </div>
  );
};

export default CompanyDetails;
```

### Example 4: App Setup with Context

```jsx
// src/App.jsx
import React from 'react';
import { VatProvider } from './context/VatContext';
import InvoiceUpload from './components/InvoiceUpload';
import VatReportViewer from './components/VatReportViewer';
import CompanyDetails from './components/CompanyDetails';

function App() {
  return (
    <VatProvider>
      <div className="App">
        <header>
          <h1>VAT Analysis Dashboard</h1>
        </header>
        
        <main>
          <CompanyDetails />
          <InvoiceUpload />
          <VatReportViewer />
        </main>
      </div>
    </VatProvider>
  );
}

export default App;
```

---

## Error Handling

### Centralized Error Handler

```javascript
// src/utils/errorHandler.js
export const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error
    const status = error.response.status;
    const message = error.response.data?.detail || error.response.data?.message;

    switch (status) {
      case 400:
        return `Bad Request: ${message}`;
      case 401:
        return 'Unauthorized. Please check your credentials.';
      case 404:
        return 'Resource not found.';
      case 500:
        return 'Server error. Please try again later.';
      default:
        return message || 'An error occurred';
    }
  } else if (error.request) {
    // Request made but no response
    return 'Network error. Please check your connection.';
  } else {
    // Something else happened
    return error.message || 'An unexpected error occurred';
  }
};
```

### Usage in Components

```jsx
import { handleApiError } from '../utils/errorHandler';

const MyComponent = () => {
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      const data = await getMonthlyReport('2025', '09');
      // Handle success
    } catch (err) {
      setError(handleApiError(err));
    }
  };

  return (
    <div>
      {error && <div className="error">{error}</div>}
      {/* ... */}
    </div>
  );
};
```

---

## State Management

### Using React Context + useReducer

```jsx
// src/context/VatContext.jsx
import React, { createContext, useContext, useReducer, useEffect } from 'react';
import * as vatService from '../services/vatService';

const VatContext = createContext();

const initialState = {
  userId: null,
  companyDetails: null,
  invoices: [],
  reports: {},
  loading: false,
  error: null,
};

const vatReducer = (state, action) => {
  switch (action.type) {
    case 'SET_USER_ID':
      return { ...state, userId: action.payload };
    case 'SET_COMPANY_DETAILS':
      return { ...state, companyDetails: action.payload };
    case 'SET_INVOICES':
      return { ...state, invoices: action.payload };
    case 'SET_REPORT':
      return {
        ...state,
        reports: { ...state.reports, [action.key]: action.payload }
      };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    default:
      return state;
  }
};

export const VatProvider = ({ children }) => {
  const [state, dispatch] = useReducer(vatReducer, initialState);

  useEffect(() => {
    // Initialize user ID
    let userId = localStorage.getItem('vat_user_id');
    if (!userId) {
      userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('vat_user_id', userId);
    }
    dispatch({ type: 'SET_USER_ID', payload: userId });

    // Load company details
    vatService.getCompanyDetails()
      .then(data => {
        if (data.company_name !== 'N/A') {
          dispatch({ type: 'SET_COMPANY_DETAILS', payload: data });
        }
      })
      .catch(err => console.error('Failed to load company details:', err));
  }, []);

  const processInvoices = async (invoices) => {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });
    
    try {
      const result = await vatService.processInvoices(invoices);
      dispatch({ type: 'SET_LOADING', payload: false });
      return result;
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
      dispatch({ type: 'SET_LOADING', payload: false });
      throw error;
    }
  };

  const fetchReport = async (type, year, monthOrQuarter = null) => {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });
    
    try {
      let report;
      if (type === 'monthly') {
        report = await vatService.getMonthlyReport(year, monthOrQuarter);
      } else if (type === 'quarterly') {
        report = await vatService.getQuarterlyReport(year, monthOrQuarter);
      } else {
        report = await vatService.getYearlyReport(year);
      }
      
      const key = `${type}_${year}_${monthOrQuarter || ''}`;
      dispatch({ type: 'SET_REPORT', key, payload: report });
      dispatch({ type: 'SET_LOADING', payload: false });
      return report;
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
      dispatch({ type: 'SET_LOADING', payload: false });
      throw error;
    }
  };

  return (
    <VatContext.Provider value={{ ...state, processInvoices, fetchReport }}>
      {children}
    </VatContext.Provider>
  );
};

export const useVat = () => {
  const context = useContext(VatContext);
  if (!context) {
    throw new Error('useVat must be used within VatProvider');
  }
  return context;
};
```

---

## Best Practices

### 1. User ID Management

- **Store in localStorage** for persistence across sessions
- **Generate unique ID** if user doesn't have authentication
- **Use same ID** for all requests from same user
- **Reset ID** when user logs out or switches account

### 2. Error Handling

- Always wrap API calls in try-catch
- Show user-friendly error messages
- Handle network errors gracefully
- Log errors for debugging

### 3. Loading States

- Show loading indicators during API calls
- Disable buttons during processing
- Provide feedback on success/failure

### 4. Data Validation

- Validate invoice data before sending
- Check required fields
- Validate date formats
- Ensure amounts are numbers

### 5. Performance

- Cache reports when possible
- Debounce search/filter inputs
- Use React.memo for expensive components
- Lazy load report components

### 6. Security

- Never expose API keys in frontend
- Validate all user inputs
- Sanitize data before display
- Use HTTPS (already handled by Render)

---

## VAT Category Reference

### Valid VAT Categories

| Category | Description | Use Case |
|----------|-------------|----------|
| `Standard VAT` | Standard rate (21% or 9%) | Domestic sales/purchases |
| `Reduced Rate` | Reduced rate (9%) | Food, books, etc. |
| `Zero Rated` | 0% VAT | Exports, EU supplies |
| `EU Goods` | EU goods supply | Goods to/from EU |
| `EU Services` | EU services supply | Services to/from EU |
| `Reverse Charge` | Reverse charge mechanism | Services from outside NL |
| `Import` | Import from non-EU | Goods from outside EU |

### VAT Percentage Values

- `"0"` - Zero rated
- `"9"` - Reduced rate
- `"21"` - Standard rate

---

## Complete Service File

```javascript
// src/services/vatService.js
import vatApi from './vatApi';

// Health Check
export const checkHealth = async () => {
  const response = await vatApi.get('/health');
  return response.data;
};

// Invoice Processing
export const processInvoices = async (invoices) => {
  const response = await vatApi.post('/process-invoices', invoices);
  return response.data;
};

// Reports
export const getMonthlyReport = async (year, month) => {
  const response = await vatApi.get('/vat-report-monthly', {
    params: { year, month }
  });
  return response.data;
};

export const getQuarterlyReport = async (year, quarter) => {
  const response = await vatApi.get('/vat-report-quarterly', {
    params: { year, quarter }
  });
  return response.data;
};

export const getYearlyReport = async (year) => {
  const response = await vatApi.get('/vat-report-yearly', {
    params: { year }
  });
  return response.data;
};

// Company Details
export const setCompanyDetails = async (companyName, companyVat) => {
  const response = await vatApi.post('/company-details', null, {
    headers: {
      'X-Company-Name': companyName,
      'X-Company-VAT': companyVat,
    }
  });
  return response.data;
};

export const getCompanyDetails = async () => {
  const response = await vatApi.get('/company-details');
  return response.data;
};

// Other Endpoints
export const getUserInfo = async () => {
  const response = await vatApi.get('/user-info');
  return response.data;
};

export const getVatSummary = async (year) => {
  const response = await vatApi.get('/vat-summary', {
    params: { year }
  });
  return response.data;
};

export const clearUserData = async () => {
  const response = await vatApi.delete('/clear-user-data');
  return response.data;
};
```

---

## Quick Integration Checklist

- [ ] Install axios: `npm install axios`
- [ ] Create API client with base URL
- [ ] Set up User ID management (localStorage or context)
- [ ] Add request interceptor for X-User-ID header
- [ ] Create service functions for all endpoints
- [ ] Implement error handling
- [ ] Create components for invoice upload
- [ ] Create components for report viewing
- [ ] Add company details management
- [ ] Test all endpoints
- [ ] Add loading states
- [ ] Add error messages
- [ ] Test duplicate detection
- [ ] Test credit notes (negative amounts)

---

## Support

For issues or questions:
- Check `POSTMAN_TESTING_GUIDE.md` for API details
- Review `COMPLETE_DOCUMENTATION.md` for full API reference
- Test endpoints in Postman first before React integration

---

**Happy Coding! 🚀**

