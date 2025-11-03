import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Container } from '@mui/material';
import Upload from './components/Upload/Upload';
import Login from './pages/Login/Login';
import ReportExport from './components/ReportExport/ReportExport';
import JobListPage from './pages/Jobs/JobListPage';
import JobStatusPage from './pages/Jobs/JobStatusPage';
import SentimentAnalysis from './pages/SentimentAnalysis/SentimentAnalysis';
import TicketTrajectory from './pages/TicketTrajectory/TicketTrajectory';
import SupportAnalytics from './pages/SupportAnalytics/SupportAnalytics';

// Protected Route wrapper
function PrivateRoute({ children }) {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" replace />;
}

function App() {
  return (
    <Container maxWidth="lg">
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Navigate to="/support-analytics" replace />} />
        <Route path="/upload" element={<PrivateRoute><Upload /></PrivateRoute>} />
        <Route path="/reports" element={<PrivateRoute><ReportExport /></PrivateRoute>} />
        <Route path="/sentiment-analysis" element={<PrivateRoute><SentimentAnalysis /></PrivateRoute>} />
        <Route path="/ticket-trajectory" element={<PrivateRoute><TicketTrajectory /></PrivateRoute>} />
        <Route path="/support-analytics" element={<PrivateRoute><SupportAnalytics /></PrivateRoute>} />
        <Route path="/jobs" element={<PrivateRoute><JobListPage /></PrivateRoute>} />
        <Route path="/jobs/:jobId" element={<PrivateRoute><JobStatusPage /></PrivateRoute>} />
      </Routes>
    </Container>
  );
}

export default App;
