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

const mockRules = [
  {
      "description": "Must include loans and leases as specified in FR Y-9C, Schedule HC-C, items 6.c and 10.a.",
      "fields": [
          "loan_type",
          "lease_type"
      ],
      "validation_logic": "loan_type in ['international_auto_loan'] and lease_type in ['international_auto_lease']",
      "parameters": {}
  },
  {
      "description": "Must include repossessed loans as specified in FR Y-9C, Schedule HC-F, item 6.",
      "fields": [
          "repossessed_loans"
      ],
      "validation_logic": "repossessed_loans is not None",
      "parameters": {}
  },
  {
      "description": "Must exclude loans originated by third parties and only serviced by the BHC, IHC, or SLHC.",
      "fields": [
          "loan_originator"
      ],
      "validation_logic": "loan_originator in ['BHC', 'IHC', 'SLHC']",
      "parameters": {}
  },
  {
      "description": "Must exclude loans or leases held for sale or held for investment and measured at fair value.",
      "fields": [
          "loan_holding_type"
      ],
      "validation_logic": "loan_holding_type == 'held_for_investment_at_amortized_cost'",
      "parameters": {}
  },
  {
      "description": "Must divide the portfolio into 3*3*6*4 = 216 segments based on product type, credit score, delinquency status, and geography.",
      "fields": [
          "product_type",
          "credit_score",
          "delinquency_status",
          "geography"
      ],
      "validation_logic": "len(set(zip(product_type, credit_score, delinquency_status, geography))) == 216",
      "parameters": {}
  },
  {
      "description": "Segment ID must be based on the segment ID positions and attribute codes listed in Table A.1.a.",
      "fields": [
          "SEGMENT_ID"
      ],
      "validation_logic": "len(str(SEGMENT_ID)) == 8 and SEGMENT_ID.isdigit()",
      "parameters": {}
  },
  {
      "description": "Must include all specified fields for each row of data.",
      "fields": [
          "BHC_NAME",
          "RSSD_ID",
          "REPORTING_MONTH",
          "PORTFOLIO_ID",
          "SEGMENT_ID"
      ],
      "validation_logic": "all(field is not None for field in [BHC_NAME, RSSD_ID, REPORTING_MONTH, PORTFOLIO_ID, SEGMENT_ID])",
      "parameters": {}
  },
  {
      "description": "Must use 'IntAuto' as the portfolio ID.",
      "fields": [
          "PORTFOLIO_ID"
      ],
      "validation_logic": "PORTFOLIO_ID == 'IntAuto'",
      "parameters": {}
  },
  {
      "description": "All dollar amounts must be reported in millions.",
      "fields": [
          "dollar_amounts"
      ],
      "validation_logic": "all(isinstance(amount, (int, float)) for amount in dollar_amounts)",
      "parameters": {}
  },
  {
      "description": "Must calculate account weighted averages for PD, LGD, ELGD, and RWA.",
      "fields": [
          "PD",
          "LGD",
          "ELGD",
          "RWA"
      ],
      "validation_logic": "all(isinstance(param, (int, float)) for param in [PD, LGD, ELGD, RWA])",
      "parameters": {
          "exception": "If Basel data are not refreshed monthly, use the appropriate Basel data from the prior quarter."
      }
  },
  {
      "description": "Must use codes '01', '02', '03' for the respective product types.",
      "fields": [
          "product_type"
      ],
      "validation_logic": "product_type in ['01', '02', '03']",
      "parameters": {}
  },
  {
      "description": "Must use codes '01', '02', '03' for the respective score ranges.",
      "fields": [
          "credit_score"
      ],
      "validation_logic": "credit_score in ['01', '02', '03']",
      "parameters": {
          "exception": "If underwriting was based on an internal score, map it to an industry standard credit score."
      }
  },
  {
      "description": "Must use codes '01' to '06' for the respective delinquency statuses.",
      "fields": [
          "delinquency_status"
      ],
      "validation_logic": "delinquency_status in ['01', '02', '03', '04', '05', '06']",
      "parameters": {}
  },
  {
      "description": "Must use codes '01' to '04' for the respective regions.",
      "fields": [
          "geography"
      ],
      "validation_logic": "geography in ['01', '02', '03', '04']",
      "parameters": {}
  },
  {
      "description": "Must report the total number of accounts.",
      "fields": [
          "#_Accounts"
      ],
      "validation_logic": "isinstance(#_Accounts, int) and #_Accounts >= 0",
      "parameters": {}
  },
  {
      "description": "Must report the total unpaid principal balance.",
      "fields": [
          "$Outstandings"
      ],
      "validation_logic": "isinstance($Outstandings, (int, float)) and $Outstandings >= 0",
      "parameters": {}
  },
  {
      "description": "Must report the total number of new accounts.",
      "fields": [
          "#New_accounts"
      ],
      "validation_logic": "isinstance(#New_accounts, int) and #New_accounts >= 0",
      "parameters": {}
  },
  {
      "description": "Must report the total dollar amount of new accounts.",
      "fields": [
          "$New_accounts"
      ],
      "validation_logic": "isinstance($New_accounts, (int, float)) and $New_accounts >= 0",
      "parameters": {}
  },
  {
      "description": "Must report the unpaid principal balance for 'car/van'.",
      "fields": [
          "$Vehicle_type_car/van"
      ],
      "validation_logic": "isinstance($Vehicle_type_car/van, (int, float)) and $Vehicle_type_car/van >= 0",
      "parameters": {}
  },
  {
      "description": "Must report the unpaid principal balance for 'SUV/truck'.",
      "fields": [
          "$Vehicle_type_SUV/truck"
      ],
      "validation_logic": "isinstance($Vehicle_type_SUV/truck, (int, float)) and $Vehicle_type_SUV/truck >= 0",
      "parameters": {}
  },
  {
      "description": "Must report the unpaid principal balance for 'sport/luxury/convertible'.",
      "fields": [
          "$Vehicle_type_sport/luxury/convertible"
      ],
      "validation_logic": "isinstance($Vehicle_type_sport/luxury/convertible, (int, float)) and $Vehicle_type_sport/luxury/convertible >= 0",
      "parameters": {}
  },
  {
      "description": "Must report the unpaid principal balance for 'unknown'.",
      "fields": [
          "$Vehicle_type_unknown"
      ],
      "validation_logic": "isinstance($Vehicle_type_unknown, (int, float)) and $Vehicle_type_unknown >= 0",
      "parameters": {}
  },
  {
      "description": "Must report the unpaid principal balance of repossessed loans.",
      "fields": [
          "$Repossession"
      ],
      "validation_logic": "isinstance($Repossession, (int, float)) and $Repossession >= 0",
      "parameters": {}
  },
  {
      "description": "Must report the unpaid principal balance of newly repossessed loans.",
      "fields": [
          "$Current_month_repossession"
      ],
      "validation_logic": "isinstance($Current_month_repossession, (int, float)) and $Current_month_repossession >= 0",
      "parameters": {}
  },
  {
      "description": "Must report the dollar amount of write-downs.",
      "fields": [
          "$Gross_contractual_charge-offs"
      ],
      "validation_logic": "isinstance($Gross_contractual_charge-offs, (int, float)) and $Gross_contractual_charge-offs >= 0",
      "parameters": {}
  },
  {
      "description": "Must report the dollar amount of bankruptcy charge-offs.",
      "fields": [
          "$Bankruptcy_charge-offs"
      ],
      "validation_logic": "isinstance($Bankruptcy_charge-offs, (int, float)) and $Bankruptcy_charge-offs >= 0",
      "parameters": {}
  },
  {
      "description": "Must report the dollar amount of recoveries.",
      "fields": [
          "$Recoveries"
      ],
      "validation_logic": "isinstance($Recoveries, (int, float)) and $Recoveries >= 0",
      "parameters": {}
  },
  {
      "description": "Must report the net charge-offs.",
      "fields": [
          "$Net_charge-offs"
      ],
      "validation_logic": "isinstance($Net_charge-offs, (int, float)) and $Net_charge-offs >= 0",
      "parameters": {}
  },
  {
      "description": "Must provide the adjustment factor and an explanation for the difference.",
      "fields": [
          "Adjustment_factor"
      ],
      "validation_logic": "isinstance(Adjustment_factor, (int, float))",
      "parameters": {}
  },
  {
      "description": "Must report the unpaid principal balance for accounts ever 30+ DPD.",
      "fields": [
          "$Ever_30DPD_in_the_last_12_months"
      ],
      "validation_logic": "isinstance($Ever_30DPD_in_the_last_12_months, (int, float)) and $Ever_30DPD_in_the_last_12_months >= 0",
      "parameters": {}
  },
  {
      "description": "Must report the unpaid principal balance for accounts ever 60+ DPD.",
      "fields": [
          "$Ever_60DPD_in_the_last_12_months"
      ],
      "validation_logic": "isinstance($Ever_60DPD_in_the_last_12_months, (int, float)) and $Ever_60DPD_in_the_last_12_months >= 0",
      "parameters": {}
  },
  {
      "description": "Must report the projected value for leased vehicles.",
      "fields": [
          "Projected_value"
      ],
      "validation_logic": "isinstance(Projected_value, (int, float)) and Projected_value >= 0",
      "parameters": {
          "exception": "Only applicable to leased vehicles."
      }
  },
  {
      "description": "Must report the sales proceeds for leased vehicles.",
      "fields": [
          "Actual_sale_proceeds"
      ],
      "validation_logic": "isinstance(Actual_sale_proceeds, (int, float)) and Actual_sale_proceeds >= 0",
      "parameters": {
          "exception": "Only applicable to leased vehicles."
      }
  },
  {
      "description": "Must calculate the account weighted average PD.",
      "fields": [
          "PD"
      ],
      "validation_logic": "isinstance(PD, (int, float)) and 0 <= PD <= 1",
      "parameters": {
          "exception": "Only applicable to advanced approaches reporting banks."
      }
  },
  {
      "description": "Must calculate the account weighted average LGD.",
      "fields": [
          "LGD"
      ],
      "validation_logic": "isinstance(LGD, (int, float)) and 0 <= LGD <= 1",
      "parameters": {
          "exception": "Only applicable to advanced approaches reporting banks."
      }
  },
  {
      "description": "Must calculate the account weighted average ELGD.",
      "fields": [
          "ELGD"
      ],
      "validation_logic": "isinstance(ELGD, (int, float)) and 0 <= ELGD <= 1",
      "parameters": {
          "exception": "Only applicable to advanced approaches reporting banks."
      }
  },
  {
      "description": "Must calculate the account weighted average RWA.",
      "fields": [
          "RWA"
      ],
      "validation_logic": "isinstance(RWA, (int, float)) and RWA >= 0",
      "parameters": {
          "exception": "Only applicable to banks subject to the advanced approaches rule."
      }
  },
  {
      "description": "Must reflect the current position, new business activity, and behavioral assumptions.",
      "fields": [
          "Weighted_Average_Life_of_Loans"
      ],
      "validation_logic": "isinstance(Weighted_Average_Life_of_Loans, (int, float)) and Weighted_Average_Life_of_Loans >= 0",
      "parameters": {}
  }
];

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

  const processRegulations2 = async () => {
    if (!regulatoryText && !file) {
      setSnackbar({ open: true, message: 'Please upload a file or enter text', severity: 'warning' });
      return;
    }
    
    setIsProcessing(true);
    try {
      const result = await api.processRegulations(regulatoryText);
      console.log(result.rules.rules);
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
        severity: 'warning',
      });
      return;
    }
    console.log("rules", rules.rules);
    setIsProcessing(true);
    try {
      // Prepare the payload
      // const payload = {
      const mappedRules = rules.map((rule) => ({
        description: rule.description,
        fields: rule.fields,
        parameters: rule.parameters,
        validation_logic: rule.validation_logic,
      }));
      const data = transactionData || sampleData;
      // };
  
      // Send the payload to the validateData API
      const validationResult = await api.validateData(mappedRules, data);
  
      // Handle the response
      setAnomalies(validationResult.validation_results);
      setRiskScores(validationResult.risk_assessment);
      setRemediationActions(validationResult.remediation_actions);
  
      setSnackbar({
        open: true,
        message: transactionData
          ? 'Validation completed using uploaded data'
          : 'Validation completed using sample data',
        severity: 'success',
      });
  
      setActiveTab('anomalies'); // Switch to show results
    } catch (error) {
      setSnackbar({
        open: true,
        message: `Validation failed: ${error.message}`,
        severity: 'error',
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
  console.log("rulesssssssssssssssss: ", rules);
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

  useEffect(() => {
    console.log('Rules state updated:', rules);
  }, [rules]);

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
              onClick={processRegulations2}
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
              <Box sx={{ overflow: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#f5f5f5' }}>
                      <th style={{ padding: '8px', textAlign: 'left' }}>Rule</th>
                      <th style={{ padding: '8px', textAlign: 'left' }}>Fields</th>
                      <th style={{ padding: '8px', textAlign: 'left' }}>Parameters</th>
                      <th style={{ padding: '8px', textAlign: 'left' }}>Validation Logic</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rules.map((rule, index) => (
                      <tr key={index} style={{ borderBottom: '1px solid #eee' }}>
                        <td style={{ padding: '8px' }}>{rule.description}</td>
                        <td style={{ padding: '8px' }}>{rule.fields.join(', ')}</td>
                        <td style={{ padding: '8px' }}>
                          {rule.parameters && Object.keys(rule.parameters).length > 0 
                            ? JSON.stringify(rule.parameters) 
                            : 'None'}
                        </td>
                        <td style={{ padding: '8px' }}>{rule.validation_logic}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Box>
            ) : (
              <Alert severity="info" sx={{ mb: 3 }}>
                No rules generated yet. Upload regulatory documents to generate profiling rules.
              </Alert>
            )}
            { rules.length <=0 && (
              <Alert severity="info" sx={{ mb: 2 }}>
                These are sample rules. Process your regulations to generate custom rules.
              </Alert>
            )}
            
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
                <Typography variant="h6" gutterBottom>
                  Risk Assessment Results
                  {transactionFile ? null : (
                    <Chip 
                      label="Sample Data" 
                      color="info" 
                      variant="outlined"
                      size="small"
                      sx={{ ml: 2 }}
                    />
                  )}
                </Typography>
                
                {/* Risk Scores Table */}
                <Box sx={{ overflow: 'auto', mb: 4 }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#f5f5f5' }}>
                        <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Transaction ID</th>
                        <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Risk Score</th>
                        <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #ddd' }}>Risk Reasons</th>
                      </tr>
                    </thead>
                    <tbody>
                      {riskScores.map((item, index) => (
                        <tr key={index} style={{ borderBottom: '1px solid #eee' }}>
                          <td style={{ padding: '12px' }}>{item.transaction_id}</td>
                          <td style={{ padding: '12px' }}>
                            <Box sx={{ 
                              width: '100%', 
                              bgcolor: '#e0e0e0', 
                              borderRadius: 1,
                              overflow: 'hidden'
                            }}>
                              <Box sx={{ 
                                width: `${Math.min(item.risk_score * 100, 100)}%`,
                                bgcolor: getRiskColor(item.risk_score),
                                height: '24px',
                                textAlign: 'center',
                                color: 'white',
                                fontSize: '0.75rem',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                              }}>
                                {item.risk_score.toFixed(2)}
                              </Box>
                            </Box>
                          </td>
                          <td style={{ padding: '12px' }}>
                            {item.risk_reasons?.length ? item.risk_reasons.join(', ') : 'None'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </Box>
                
                <Typography variant="h6" gutterBottom>
                  Remediation Actions
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
                              <strong>Actions:</strong> {action.actions?.length ? action.actions.join(', ') : 'No actions required'}
                            </Box>
                            <Box component="span" sx={{ display: 'block' }}>
                              <strong>Documentation:</strong> {action.documentation_required ? 'Required' : 'Not required'}
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
              {transactionFile 
                ? 'Showing validation results for uploaded data'
                : 'This panel shows sample anomaly detection results. Process your regulations to see real validation results.'}
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
            <Typography variant="h5" gutterBottom>Compliance Assistant (Future Enhancement)</Typography>
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