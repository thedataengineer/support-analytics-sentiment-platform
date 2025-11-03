import { createTheme } from '@mui/material/styles';

// Design System Configuration
export const designTokens = {
  colors: {
    primary: '#1976d2',
    secondary: '#dc004e',
    success: '#2e7d32',
    warning: '#ed6c02',
    error: '#d32f2f',
    info: '#0288d1',
    
    // Sentiment colors
    sentiment: {
      positive: '#4caf50',
      negative: '#f44336',
      neutral: '#ff9800'
    },
    
    // Background colors
    background: {
      default: '#fafafa',
      paper: '#ffffff',
      dark: '#f5f5f5'
    }
  },
  
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: { fontSize: '2.5rem', fontWeight: 300 },
    h2: { fontSize: '2rem', fontWeight: 400 },
    h3: { fontSize: '1.75rem', fontWeight: 400 },
    h4: { fontSize: '1.5rem', fontWeight: 500 },
    h5: { fontSize: '1.25rem', fontWeight: 500 },
    h6: { fontSize: '1rem', fontWeight: 500 }
  },
  
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32
  },
  
  breakpoints: {
    xs: 0,
    sm: 600,
    md: 768,
    lg: 1024,
    xl: 1200
  },
  
  shadows: {
    card: '0 2px 8px rgba(0,0,0,0.1)',
    elevated: '0 4px 16px rgba(0,0,0,0.15)',
    modal: '0 8px 32px rgba(0,0,0,0.2)'
  }
};

// Material-UI Theme
export const theme = createTheme({
  palette: {
    primary: {
      main: designTokens.colors.primary,
    },
    secondary: {
      main: designTokens.colors.secondary,
    },
    success: {
      main: designTokens.colors.success,
    },
    warning: {
      main: designTokens.colors.warning,
    },
    error: {
      main: designTokens.colors.error,
    },
    info: {
      main: designTokens.colors.info,
    },
    background: designTokens.colors.background
  },
  
  typography: designTokens.typography,
  
  breakpoints: {
    values: designTokens.breakpoints
  },
  
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: designTokens.shadows.card,
          borderRadius: 8
        }
      }
    },
    
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          textTransform: 'none',
          fontWeight: 500
        }
      }
    },
    
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 16
        }
      }
    }
  }
});

export default theme;