import type React from 'react';
import { Container, Typography, Button } from '@mui/material';

const App: React.FC = () => {
  return (
    <Container>
      <Typography variant="h1" component="h1" gutterBottom>
        Frontend Agent
      </Typography>
      <Typography variant="body1" gutterBottom>
        This is the root component of the Frontend Agent, now with Material-UI.
      </Typography>
      <Button variant="contained" color="primary">
        Click Me
      </Button>
    </Container>
  );
};

export default App;