import React from 'react';
import { Chip, Tooltip } from '@mui/material';

function SentimentBadge({ 
  sentiment, 
  confidence = null, 
  size = 'small',
  showConfidence = false 
}) {
  const getSentimentColor = (sentiment) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive': return 'success';
      case 'negative': return 'error';
      case 'neutral': return 'warning';
      default: return 'default';
    }
  };

  const formatSentiment = (sentiment) => {
    if (!sentiment) return 'Unknown';
    return sentiment.charAt(0).toUpperCase() + sentiment.slice(1);
  };

  const label = showConfidence && confidence 
    ? `${formatSentiment(sentiment)} (${Math.round(confidence * 100)}%)`
    : formatSentiment(sentiment);

  const chipElement = (
    <Chip
      label={label}
      color={getSentimentColor(sentiment)}
      size={size}
      variant="filled"
    />
  );

  if (confidence && !showConfidence) {
    return (
      <Tooltip title={`Confidence: ${Math.round(confidence * 100)}%`}>
        {chipElement}
      </Tooltip>
    );
  }

  return chipElement;
}

export default SentimentBadge;