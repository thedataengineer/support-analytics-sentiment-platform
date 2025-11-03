// Accessibility utilities and helpers

export const a11yProps = (index) => ({
  id: `tab-${index}`,
  'aria-controls': `tabpanel-${index}`,
});

export const getAriaLabel = (type, value, context = '') => {
  switch (type) {
    case 'sentiment':
      return `Sentiment: ${value}${context ? ` for ${context}` : ''}`;
    case 'metric':
      return `Metric value: ${value}${context ? ` ${context}` : ''}`;
    case 'chart':
      return `Chart showing ${context || 'data visualization'}`;
    case 'table':
      return `Data table${context ? ` showing ${context}` : ''}`;
    default:
      return value;
  }
};

export const announceToScreenReader = (message) => {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', 'polite');
  announcement.setAttribute('aria-atomic', 'true');
  announcement.style.position = 'absolute';
  announcement.style.left = '-10000px';
  announcement.style.width = '1px';
  announcement.style.height = '1px';
  announcement.style.overflow = 'hidden';
  
  document.body.appendChild(announcement);
  announcement.textContent = message;
  
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
};

export const keyboardNavigation = {
  ENTER: 'Enter',
  SPACE: ' ',
  ESCAPE: 'Escape',
  ARROW_UP: 'ArrowUp',
  ARROW_DOWN: 'ArrowDown',
  ARROW_LEFT: 'ArrowLeft',
  ARROW_RIGHT: 'ArrowRight',
  TAB: 'Tab'
};

export const handleKeyboardNavigation = (event, handlers = {}) => {
  const { key } = event;
  const handler = handlers[key];
  
  if (handler) {
    event.preventDefault();
    handler(event);
  }
};