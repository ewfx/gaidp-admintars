export const API_BASE_URL = 'http://localhost:8000';

export const uploadFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${API_BASE_URL}/api/upload`, {
    method: 'POST',
    body: formData
  });
  
  if (!response.ok) {
    throw new Error('File upload failed');
  }
  return await response.json();
};

export const processRegulations = async (text) => {
  const response = await fetch(`${API_BASE_URL}/api/process`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text })
  });
  
  if (!response.ok) {
    throw new Error('Regulation processing failed');
  }
  return await response.json();
};

export const validateData = async (rules, data) => {
  const response = await fetch(`${API_BASE_URL}/api/validate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ rules, data })
  });
  
  if (!response.ok) {
    throw new Error('Data validation failed');
  }
  return await response.json();
};

export const downloadValidationCode = (code) => {
  const blob = new Blob([code], { type: 'text/python' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'validation_rules.py';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// Add this new function to api.js
export const uploadTransactionData = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/api/upload-transactions`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error('Transaction data upload failed');
    }
    return await response.json();
};