import React from 'react';
import { Grid } from '@mui/material';

function CardGrid({ 
  children, 
  breakpoints = { xs: 1, md: 2, lg: 3 },
  spacing = 3 
}) {
  return (
    <Grid container spacing={spacing}>
      {React.Children.map(children, (child, index) => (
        <Grid 
          item 
          xs={12 / breakpoints.xs}
          md={12 / breakpoints.md}
          lg={12 / breakpoints.lg}
          key={index}
        >
          {child}
        </Grid>
      ))}
    </Grid>
  );
}

export default CardGrid;