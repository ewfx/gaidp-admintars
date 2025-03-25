import { createTheme } from '@mui/material/styles';

const complianceTheme = createTheme({
  palette: {
    mode: 'light', // or 'dark' for dark mode
    primary: {
      main: '#2c3e50', // Dark blue-gray for primary actions
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#3498db', // Bright blue for secondary actions
      contrastText: '#ffffff',
    },
    error: {
      main: '#e74c3c', // Alert red for errors
    },
    warning: {
      main: '#f39c12', // Orange for warnings
    },
    success: {
      main: '#2ecc71', // Green for success states
    },
    background: {
      default: '#f5f7fa', // Light gray background
      paper: '#ffffff', // White for cards/paper
    },
    text: {
      primary: '#2c3e50', // Dark text
      secondary: '#7f8c8d', // Gray for secondary text
    },
  },
  typography: {
    fontFamily: [
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif'
    ].join(','),
    h5: {
      fontWeight: 600,
      fontSize: '1.5rem',
    },
    h6: {
      fontWeight: 500,
    },
    button: {
      textTransform: 'none', // Buttons won't be uppercase
      fontWeight: 500,
    },
  },
  components: {
    MuiDataGrid: {
      styleOverrides: {
        root: {
          border: 'none',
          '& .MuiDataGrid-columnHeaders': {
            backgroundColor: '#2c3e50',
            color: '#ffffff',
          },
          '& .MuiDataGrid-cell': {
            borderBottom: '1px solid #ecf0f1',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 16px',
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 4px 20px 0 rgba(0,0,0,0.05)',
        },
      },
    },
  },
});

export default complianceTheme;