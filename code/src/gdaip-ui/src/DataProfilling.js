import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Button, Paper, TextField, Divider, Chip, 
  CircularProgress, Alert, Snackbar, Tab, Tabs, List, ListItem, 
  ListItemText, IconButton, Tooltip 
} from '@mui/material';
import { 
  FileUpload, Insights, Code, GppGood, Chat, Settings,
  Download, Refresh, CheckCircle, Error, Warning 
} from '@mui/icons-material';
import { DataGrid } from '@mui/x-data-grid';
import * as api from './api';

const RegulatoryProfilingUI = () => {
  // State management
  const [activeTab, setActiveTab] = useState('upload');
  const [regulatoryText, setRegulatoryText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [rules, setRules] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [validationCode, setValidationCode] = useState('');
  const [riskScores, setRiskScores] = useState([]);
  const [remediationActions, setRemediationActions] = useState([]);
  const [conversation, setConversation] = useState([]);
  const [userMessage, setUserMessage] = useState('');
  const [file, setFile] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const [sampleData] = useState([
    { Customer_ID: 1001, Account_Balance: 15000, Amount: 500, Reported_Amount: 500, Currency: 'USD', Country: 'US', Transaction_Date: '2025-02-25' },
    { Customer_ID: 1002, Account_Balance: 32000, Amount: 1200, Reported_Amount: 1200, Currency: 'EUR', Country: 'DE', Transaction_Date: '2025-02-20' },
    { Customer_ID: 1003, Account_Balance: -5000, Amount: 300, Reported_Amount: 300, Currency: 'GBP', Country: 'UK', Transaction_Date: '2025-02-18', Account_Type: '' },
    { Customer_ID: 1004, Account_Balance: 70000, Amount: 2000, Reported_Amount: 2000, Currency: 'USD', Country: 'US', Transaction_Date: '2025-02-28' }
  ]);

  const handleFileUpload = async (e) => {
    const uploadedFile = e.target.files[0];
    if (!uploadedFile) return;
    
    setFile(uploadedFile);
    setIsProcessing(true);
    
    try {
      const result = await api.uploadFile(uploadedFile);
      setRegulatoryText(result.text);
      setSnackbar({ open: true, message: `File uploaded successfully: ${result.original_filename}`, severity: 'success' });
    } catch (error) {
      setSnackbar({ open: true, message: `Upload failed: ${error.message}`, severity: 'error' });
    } finally {
      setIsProcessing(false);
    }
  };

  const processRegulations = async () => {
    if (!regulatoryText && !file) {
      setSnackbar({ open: true, message: 'Please upload a file or enter text', severity: 'warning' });
      return;
    }
    
    setIsProcessing(true);
    try {
      const result = await api.processRegulations(regulatoryText);
      setRules(result.rules.rules);
      setValidationCode(result.validation_code);
      
      // Removed auto-validation here
      setSnackbar({ 
        open: true, 
        message: 'Regulations processed successfully! Click "Validate" to check your data', 
        severity: 'success' 
      });
      setActiveTab('rules');
    } catch (error) {
      setSnackbar({ open: true, message: `Processing failed: ${error.message}`, severity: 'error' });
    } finally {
      setIsProcessing(false);
    }
  };

//   
// Add to your state declarations
  const [transactionData, setTransactionData] = useState(null);
  const [transactionFile, setTransactionFile] = useState(null);

    // Add this handler function
  const handleTransactionUpload = async (e) => {
  const uploadedFile = e.target.files[0];
    if (!uploadedFile) return;
    
    setTransactionFile(uploadedFile);
    setIsProcessing(true);
    
    try {
        const result = await api.uploadTransactionData(uploadedFile);
        setTransactionData(result.data);
        setSnackbar({ 
        open: true, 
        message: `Transaction data uploaded successfully: ${uploadedFile.name}`, 
        severity: 'success' 
        });
    } catch (error) {
        setSnackbar({ 
        open: true, 
        message: `Transaction upload failed: ${error.message}`, 
        severity: 'error' 
        });
    } finally {
        setIsProcessing(false);
    }
    };

    // Modify the refreshValidation function to use uploaded data
    const refreshValidation = async () => {
        if (rules.length === 0) {
          setSnackbar({ 
            open: true, 
            message: 'No rules available. Process regulations first', 
            severity: 'warning' 
          });
          return;
        }
        
        setIsProcessing(true);
        try {
          const dataToValidate = transactionData || sampleData;
          const validationResult = await api.validateData(rules, dataToValidate);
          
          setAnomalies(validationResult.validation_results);
          setRiskScores(validationResult.risk_assessment);
          setRemediationActions(validationResult.remediation_actions);
          
          setSnackbar({ 
            open: true, 
            message: transactionData 
              ? 'Validation completed using uploaded data' 
              : 'Validation completed using sample data',
            severity: 'success' 
          });
          
          setActiveTab('anomalies'); // Switch to show results
        } catch (error) {
          setSnackbar({ 
            open: true, 
            message: `Validation failed: ${error.message}`, 
            severity: 'error' 
          });
        } finally {
          setIsProcessing(false);
        }
    };

  const handleSendMessage = async () => {
    if (!userMessage.trim()) return;
    
    const userMsg = { sender: 'user', text: userMessage, time: new Date().toLocaleTimeString() };
    setConversation([...conversation, userMsg]);
    setUserMessage('');
    
    setIsProcessing(true);
    try {
      // In a real implementation, this would call your LLM API
      // Simulating API call with timeout
      setTimeout(() => {
        const aiResponses = [
          "Based on regulation Section 2.1, transaction amounts must match within 1% tolerance for currency conversions.",
          "Negative balances require OD flag verification as per compliance rule 3.4.",
          "I can adjust the validation threshold. What percentage tolerance would you prefer?"
        ];
        const aiMsg = { 
          sender: 'ai', 
          text: aiResponses[Math.floor(Math.random() * aiResponses.length)],
          time: new Date().toLocaleTimeString() 
        };
        setConversation(prev => [...prev, aiMsg]);
        setIsProcessing(false);
      }, 1500);
    } catch (error) {
      setSnackbar({ open: true, message: `Assistant error: ${error.message}`, severity: 'error' });
      setIsProcessing(false);
    }
  };

  const downloadCode = () => {
    if (!validationCode) {
      setSnackbar({ open: true, message: 'No validation code generated yet', severity: 'warning' });
      return;
    }
    api.downloadValidationCode(validationCode);
  };

  const getRiskColor = (score) => {
    if (score > 0.8) return '#f44336'; // High risk
    if (score > 0.5) return '#ff9800'; // Medium risk
    return '#4caf50'; // Low risk
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', backgroundColor: '#f5f7fa' }}>
      {/* Sidebar Navigation */}
      <Box sx={{ width: 240, bgcolor: '#2c3e50', color: 'white', p: 2 }}>
        <Typography variant="h6" sx={{ mb: 3, textAlign: 'center' }}>GenAI - Data Profiler</Typography>
        <Button
          fullWidth
          startIcon={<FileUpload />}
          sx={{ justifyContent: 'flex-start', mb: 1 }}
          onClick={() => setActiveTab('upload')}
          color={activeTab === 'upload' ? 'secondary' : 'inherit'}
        >
          Upload Regulations
        </Button>
        <Button
          fullWidth
          startIcon={<GppGood />}
          sx={{ justifyContent: 'flex-start', mb: 1 }}
          onClick={() => setActiveTab('rules')}
          color={activeTab === 'rules' ? 'secondary' : 'inherit'}
        >
          Generated Rules
        </Button>
        <Button
          fullWidth
          startIcon={<Insights />}
          sx={{ justifyContent: 'flex-start', mb: 1 }}
          onClick={() => setActiveTab('anomalies')}
          color={activeTab === 'anomalies' ? 'secondary' : 'inherit'}
        >
          Anomaly Detection
        </Button>
        <Button
          fullWidth
          startIcon={<Code />}
          sx={{ justifyContent: 'flex-start', mb: 1 }}
          onClick={() => setActiveTab('validation')}
          color={activeTab === 'validation' ? 'secondary' : 'inherit'}
        >
          Validation Code
        </Button>
        <Button
          fullWidth
          startIcon={<Chat />}
          sx={{ justifyContent: 'flex-start', mb: 1 }}
          onClick={() => setActiveTab('assistant')}
          color={activeTab === 'assistant' ? 'secondary' : 'inherit'}
        >
          Compliance Assistant
        </Button>
      </Box>

      {/* Main Content Area */}
      <Box sx={{ flex: 1, p: 3 }}>
        {activeTab === 'upload' && (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>Upload Regulatory Documents</Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              Upload PDF/CSV files or paste regulatory text to generate compliance rules
            </Typography>
            
            <Box sx={{ mb: 3 }}>
              <Button
                variant="contained"
                component="label"
                startIcon={<FileUpload />}
                sx={{ mr: 2 }}
                disabled={isProcessing}
              >
                Upload File
                <input type="file" hidden onChange={handleFileUpload} accept=".pdf,.csv" />
              </Button>
              {file && (
                <Chip 
                  label={file.name} 
                  onDelete={() => setFile(null)} 
                  sx={{ ml: 1 }} 
                  deleteIcon={isProcessing ? <CircularProgress size={20} /> : undefined}
                />
              )}
            </Box>
            
            <Divider sx={{ my: 2 }}>OR</Divider>
            
            <TextField
              label="Paste Regulatory Text"
              multiline
              rows={10}
              fullWidth
              value={regulatoryText}
              onChange={(e) => setRegulatoryText(e.target.value)}
              placeholder="Paste regulatory reporting instructions here..."
              sx={{ mb: 3 }}
            />
            
            <Button
              variant="contained"
              color="primary"
              onClick={processRegulations}
              disabled={isProcessing || (!regulatoryText && !file)}
              startIcon={isProcessing ? <CircularProgress size={20} /> : null}
            >
              {isProcessing ? 'Processing...' : 'Generate Profiling Rules'}
            </Button>
          </Paper>
        )}

        {activeTab === 'rules' && (
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h5">Generated Profiling Rules</Typography>
              <Box>
                <Chip 
                  label="Sample Data" 
                  color="info" 
                  variant="outlined"
                  size="small"
                  sx={{ mr: 2 }}
                />
                <Button
                  variant="outlined"
                  startIcon={<Refresh />}
                  onClick={refreshValidation}
                  disabled={isProcessing}
                >
                  Refresh Validation
                </Button>
              </Box>
            </Box>
            
            {rules.length > 0 ? (
              <DataGrid
                rows={rules}
                columns={[
                  { 
                    field: 'description', 
                    headerName: 'Rule', 
                    flex: 2,
                    renderCell: (params) => (
                      <Tooltip title={params.value} placement="top">
                        <span>{params.value}</span>
                      </Tooltip>
                    )
                  },
                  { 
                    field: 'fields', 
                    headerName: 'Fields', 
                    flex: 1, 
                    valueGetter: (params) => params.value?.join(', ') || 'N/A',
                    renderCell: (params) => (
                      <Chip 
                        label={params.value} 
                        size="small" 
                        variant="outlined"
                      />
                    )
                  },
                  { 
                    field: 'status', 
                    headerName: 'Status', 
                    width: 120,
                    renderCell: (params) => (
                      <Chip 
                        label={params.value || 'active'} 
                        color={(!params.value || params.value === 'active') ? 'success' : 'warning'} 
                        size="small" 
                      />
                    )
                  }
                ]}
                pageSize={10}
                rowsPerPageOptions={[10]}
                autoHeight
                sx={{ 
                  mb: 3,
                  '& .MuiDataGrid-cell': {
                    borderBottom: '1px solid #f0f0f0',
                  }
                }}
                getRowId={(row) => row.id}
              />
            ) : (
              <Alert severity="info" sx={{ mb: 3 }}>
                No rules generated yet. Upload regulatory documents to generate profiling rules.
              </Alert>
            )}
            
            <Alert severity="info" sx={{ mb: 2 }}>
              These are sample rules. Process your regulations to generate custom rules.
            </Alert>
            
            <Button
              variant="outlined"
              onClick={() => setActiveTab('assistant')}
              startIcon={<Chat />}
            >
              Refine Rules with Assistant
            </Button>
          </Paper>
        )}

        {activeTab === 'anomalies' && (
            <Paper sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h5">Anomaly Detection</Typography>
                <Box display="flex" alignItems="center" gap={2}>
                    {/* Upload Button */}
                    <Button
                    variant="outlined"
                    component="label"
                    startIcon={<FileUpload />}
                    disabled={isProcessing}
                    size="small"
                    >
                    Upload Data
                    <input 
                        type="file" 
                        hidden 
                        onChange={handleTransactionUpload} 
                        accept=".csv,.xlsx,.xls" 
                    />
                    </Button>
                    
                    {/* Current Dataset Indicator */}
                    {transactionFile ? (
                    <Chip 
                        label={`Using: ${transactionFile.name}`}
                        color="success"
                        variant="outlined"
                        onDelete={() => {
                        setTransactionFile(null);
                        setTransactionData(null);
                        }}
                    />
                    ) : (
                    <Chip 
                        label="Using: Sample Data" 
                        color="info" 
                        variant="outlined"
                    />
                    )}
                    
                    {/* Validate Button */}
                    <Button
                    variant="contained"
                    startIcon={<GppGood />}
                    onClick={refreshValidation}
                    disabled={isProcessing || rules.length === 0}
                    >
                    Validate
                    </Button>
                </Box>
            </Box>
            
            {riskScores.length > 0 ? (
              <>
                <DataGrid
                  rows={riskScores}
                  columns={[
                    { field: 'Customer_ID', headerName: 'Customer ID', width: 120 },
                    { field: 'Amount', headerName: 'Amount', width: 100 },
                    { field: 'Currency', headerName: 'Currency', width: 100 },
                    { field: 'Country', headerName: 'Country', width: 120 },
                    { 
                      field: 'risk_score', 
                      headerName: 'Risk Score', 
                      width: 150,
                      renderCell: (params) => (
                        <Box sx={{ 
                          width: '100%', 
                          bgcolor: '#e0e0e0', 
                          borderRadius: 1,
                          overflow: 'hidden'
                        }}>
                          <Box sx={{ 
                            width: `${Math.min(params.value * 100, 100)}%`,
                            bgcolor: getRiskColor(params.value),
                            height: '100%',
                            textAlign: 'center',
                            color: 'white',
                            fontSize: '0.75rem'
                          }}>
                            {params.value.toFixed(2)}
                          </Box>
                        </Box>
                      )
                    }
                  ]}
                  pageSize={10}
                  rowsPerPageOptions={[10]}
                  autoHeight
                  sx={{ mb: 3 }}
                  getRowId={(row) => row.id}
                />
                
                <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                  Remediation Actions
                  <Chip 
                    label="Sample Data" 
                    color="info" 
                    variant="outlined"
                    size="small"
                    sx={{ ml: 2 }}
                  />
                </Typography>
                <List dense>
                  {remediationActions.map((action, index) => (
                    <ListItem key={index} sx={{ 
                      borderBottom: '1px solid #eee',
                      bgcolor: action.documentation_required ? '#fff8e1' : 'inherit'
                    }}>
                      <ListItemText
                        primary={`Transaction ${action.transaction_id}`}
                        secondary={
                          <>
                            <Box component="span" sx={{ display: 'block' }}>
                              <strong>Issues:</strong> {action.issues.join(', ')}
                            </Box>
                            <Box component="span" sx={{ display: 'block' }}>
                              <strong>Actions:</strong> {action.actions.join(', ')}
                            </Box>
                          </>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </>
            ) : (
              <Alert severity="info" sx={{ mb: 3 }}>
                No validation results available. Process regulations first to generate validation rules.
              </Alert>
            )}
            
            <Alert severity="info">
              This panel shows sample anomaly detection results. Process your regulations to see real validation results.
            </Alert>
          </Paper>
        )}

        {activeTab === 'validation' && (
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h5">Generated Validation Code</Typography>
              <Button
                variant="contained"
                startIcon={<Download />}
                onClick={downloadCode}
                disabled={!validationCode}
              >
                Download Code
              </Button>
            </Box>
            
            <Paper variant="outlined" sx={{ p: 2, bgcolor: '#f5f5f5', overflow: 'auto', mb: 3 }}>
              <pre style={{ 
                margin: 0, 
                fontFamily: 'monospace', 
                whiteSpace: 'pre-wrap',
                fontSize: '0.875rem'
              }}>
                {validationCode || 'No validation code generated yet. Process regulations first.'}
              </pre>
            </Paper>
            
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button 
                variant="outlined" 
                onClick={() => setActiveTab('rules')}
                startIcon={<GppGood />}
              >
                View Rules
              </Button>
              <Button 
                variant="outlined" 
                onClick={() => setActiveTab('anomalies')}
                startIcon={<Insights />}
              >
                View Validation Results
              </Button>
            </Box>
          </Paper>
        )}

        {activeTab === 'assistant' && (
          <Paper sx={{ p: 3, height: '70vh', display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h5" gutterBottom>Compliance Assistant</Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              Refine profiling rules through conversational interface
            </Typography>
            
            <Box sx={{ 
              flex: 1, 
              overflow: 'auto', 
              mb: 2, 
              p: 1, 
              bgcolor: '#f9f9f9', 
              borderRadius: 1,
              border: '1px solid #eee'
            }}>
              {conversation.length === 0 ? (
                <Box sx={{ 
                  display: 'flex', 
                  flexDirection: 'column', 
                  alignItems: 'center', 
                  justifyContent: 'center', 
                  height: '100%',
                  color: 'text.secondary'
                }}>
                  <Chat sx={{ fontSize: 60, mb: 2, opacity: 0.5 }} />
                  <Typography>Start a conversation to refine compliance rules</Typography>
                </Box>
              ) : (
                conversation.map((msg, index) => (
                  <Box 
                    key={index} 
                    sx={{ 
                      display: 'flex', 
                      justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                      mb: 2
                    }}
                  >
                    <Paper
                      elevation={0}
                      sx={{
                        p: 2,
                        maxWidth: '80%',
                        bgcolor: msg.sender === 'user' ? '#e3f2fd' : '#f5f5f5',
                        borderRadius: msg.sender === 'user' ? '18px 18px 0 18px' : '18px 18px 18px 0'
                      }}
                    >
                      <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                        {msg.sender === 'user' ? 'You' : 'Compliance AI'} • {msg.time}
                      </Typography>
                      <Typography>{msg.text}</Typography>
                    </Paper>
                  </Box>
                ))
              )}
            </Box>
            
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                fullWidth
                variant="outlined"
                placeholder="Ask about compliance rules or request changes..."
                value={userMessage}
                onChange={(e) => setUserMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                disabled={isProcessing}
              />
              <Button 
                variant="contained" 
                onClick={handleSendMessage}
                disabled={!userMessage.trim() || isProcessing}
              >
                Send
              </Button>
            </Box>
          </Paper>
        )}
      </Box>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={() => setSnackbar({ ...snackbar, open: false })} 
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default RegulatoryProfilingUI;