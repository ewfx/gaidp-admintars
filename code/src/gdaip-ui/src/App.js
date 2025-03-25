import React from 'react';
import ReactDOM from 'react-dom';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers';
// import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import complianceTheme from './theme';
import RegulatoryProfilingUI from './DataProfilling';

function App() {
  return (
    <ThemeProvider theme={complianceTheme}>
      {/* <CssBaseline /> Normalize CSS and apply theme background */}
      {/* <LocalizationProvider> */}
        <RegulatoryProfilingUI />
      {/* </LocalizationProvider> */}
    </ThemeProvider>
  );
}

export default App;