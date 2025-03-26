import React from 'react';
import ReactDOM from 'react-dom/client'; // Use 'react-dom/client' for React 18
import './index.css';
import App from './App';
import complianceTheme from './theme';
import { ThemeProvider, createTheme } from '@mui/material/styles';

const theme = createTheme();

// Create a root and render the app
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ThemeProvider theme={complianceTheme}>
      <App />
    </ThemeProvider>
  </React.StrictMode>
);