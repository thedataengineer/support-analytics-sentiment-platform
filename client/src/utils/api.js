/**
 * API utility to handle base URL configuration
 */

// Use environment variable for production, fallback to empty string for local development
const API_BASE_URL = process.env.REACT_APP_API_URL || '';

/**
 * Construct full API URL
 * @param {string} path - API endpoint path (e.g., '/api/sentiment/overview')
 * @returns {string} Full URL
 */
export const getApiUrl = (path) => {
  return `${API_BASE_URL}${path}`;
};

/**
 * Fetch wrapper with automatic URL handling
 * @param {string} path - API endpoint path
 * @param {object} options - Fetch options
 * @returns {Promise<Response>}
 */
export const apiFetch = (path, options = {}) => {
  return fetch(getApiUrl(path), options);
};
