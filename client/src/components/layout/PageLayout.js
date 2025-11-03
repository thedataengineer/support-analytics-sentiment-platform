import React from 'react';
import { Container, Stack, Typography, Box, Breadcrumbs, Link } from '@mui/material';
import { useResponsive } from '../../theme/responsive';

function PageLayout({ 
  title, 
  subtitle,
  actions, 
  filters, 
  breadcrumbs = [],
  children,
  maxWidth = 'lg' 
}) {
  const { isMobile } = useResponsive();

  return (
    <Container maxWidth={maxWidth} sx={{ mt: 4, mb: 4 }}>
      {/* Breadcrumbs */}
      {breadcrumbs.length > 0 && (
        <Breadcrumbs sx={{ mb: 2 }}>
          {breadcrumbs.map((crumb, index) => (
            <Link key={index} href={crumb.href} color="inherit">
              {crumb.label}
            </Link>
          ))}
        </Breadcrumbs>
      )}

      {/* Header */}
      <Stack 
        direction={isMobile ? 'column' : 'row'} 
        justifyContent="space-between" 
        alignItems={isMobile ? 'stretch' : 'center'} 
        sx={{ mb: 3 }}
        spacing={2}
      >
        <Box>
          <Typography variant={isMobile ? 'h5' : 'h4'} component="h1">
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="body1" color="text.secondary">
              {subtitle}
            </Typography>
          )}
        </Box>
        
        {actions && (
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {actions}
          </Box>
        )}
      </Stack>

      {/* Filters */}
      {filters && (
        <Box sx={{ mb: 3 }}>
          {filters}
        </Box>
      )}

      {/* Content */}
      <Box>
        {children}
      </Box>
    </Container>
  );
}

export default PageLayout;