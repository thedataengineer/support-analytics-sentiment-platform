import { useTheme, useMediaQuery } from '@mui/material';

export const useResponsive = () => {
  const theme = useTheme();
  
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isTablet = useMediaQuery(theme.breakpoints.between('md', 'lg'));
  const isDesktop = useMediaQuery(theme.breakpoints.up('lg'));
  
  return {
    isMobile,
    isTablet,
    isDesktop,
    getGridCols: () => {
      if (isMobile) return 1;
      if (isTablet) return 2;
      return 3;
    },
    getChartHeight: () => isMobile ? 250 : 300,
    getTablePageSize: () => isMobile ? 5 : 10
  };
};

export const responsiveStyles = {
  dashboardGrid: {
    display: 'grid',
    gap: 2,
    gridTemplateColumns: {
      xs: '1fr',
      md: 'repeat(2, 1fr)',
      lg: 'repeat(3, 1fr)'
    }
  },
  
  mobileStack: {
    flexDirection: { xs: 'column', md: 'row' },
    gap: { xs: 1, md: 2 }
  },
  
  responsiveCard: {
    height: { xs: 'auto', md: '100%' }
  }
};