// Shared styles for the application
export const styles = {
  // Container styles
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(to bottom right, #eff6ff, #e0e7ff)',
  },
  
  // Login card
  loginCard: {
    backgroundColor: 'white',
    padding: '32px',
    borderRadius: '8px',
    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
    width: '400px',
  },
  
  // Button styles
  button: {
    padding: '8px 16px',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'all 0.2s',
    border: 'none',
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
  },
  
  primaryButton: {
    backgroundColor: '#3b82f6',
    color: 'white',
  },
  
  secondaryButton: {
    backgroundColor: '#e5e7eb',
    color: '#374151',
  },
  
  dangerButton: {
    backgroundColor: '#ef4444',
    color: 'white',
  },
  
  // Input styles
  input: {
    width: '100%',
    padding: '8px 12px',
    border: '1px solid #d1d5db',
    borderRadius: '6px',
    fontSize: '14px',
    outline: 'none',
    marginBottom: '16px',
  },
  
  // Sidebar styles
  sidebar: {
    width: '256px',
    backgroundColor: '#111827',
    color: 'white',
    display: 'flex',
    flexDirection: 'column' as const,
  },
  
  sidebarHeader: {
    padding: '16px',
    borderBottom: '1px solid #374151',
  },
  
  conversationItem: {
    padding: '12px',
    cursor: 'pointer',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    transition: 'background-color 0.2s',
  },
  
  conversationItemActive: {
    backgroundColor: '#1f2937',
  },
  
  conversationItemHover: {
    backgroundColor: '#1f2937',
  },
  
  // Chat area styles
  chatContainer: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column' as const,
    backgroundColor: '#f9fafb',
  },
  
  chatHeader: {
    backgroundColor: 'white',
    boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)',
    padding: '16px 24px',
    borderBottom: '1px solid #e5e7eb',
  },
  
  chatMessages: {
    flex: 1,
    overflowY: 'auto' as const,
    padding: '24px',
  },
  
  messageWrapper: {
    marginBottom: '16px',
    display: 'flex',
  },
  
  userMessage: {
    maxWidth: '768px',
    padding: '12px 16px',
    borderRadius: '8px',
    backgroundColor: '#3b82f6',
    color: 'white',
  },
  
  assistantMessage: {
    maxWidth: '768px',
    padding: '12px 16px',
    borderRadius: '8px',
    backgroundColor: 'white',
    border: '1px solid #d1d5db',
  },
  
  chatInputArea: {
    backgroundColor: 'white',
    borderTop: '1px solid #e5e7eb',
    padding: '16px',
  },
  
  chatInputWrapper: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  
  chatInput: {
    flex: 1,
    padding: '8px 16px',
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    fontSize: '14px',
    outline: 'none',
  },
  
  // Loading spinner
  loadingSpinner: {
    display: 'inline-block',
    width: '32px',
    height: '32px',
    border: '3px solid #e5e7eb',
    borderTop: '3px solid #3b82f6',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  
  // Error message
  errorMessage: {
    backgroundColor: '#fee2e2',
    border: '1px solid #f87171',
    color: '#b91c1c',
    padding: '12px 16px',
    borderRadius: '6px',
    marginBottom: '16px',
  },
  
  // Success message
  successMessage: {
    backgroundColor: '#dcfce7',
    border: '1px solid #86efac',
    color: '#16a34a',
    padding: '12px 16px',
    borderRadius: '6px',
    marginBottom: '16px',
  },
  
  // Badge
  badge: {
    display: 'inline-block',
    padding: '2px 8px',
    borderRadius: '9999px',
    fontSize: '12px',
    fontWeight: '600',
  },
  
  activeBadge: {
    backgroundColor: '#dcfce7',
    color: '#16a34a',
  },
  
  inactiveBadge: {
    backgroundColor: '#fee2e2',
    color: '#dc2626',
  },
  
  adminBadge: {
    backgroundColor: '#f3e8ff',
    color: '#9333ea',
  },
};