/**
 * Simple component test to verify Vitest setup
 */

import { render, screen } from '@testing-library/react';

// Simple button component for testing
function Button({ children }: { children: React.ReactNode }) {
  return <button>{children}</button>;
}

it('renders a button with text', () => {
  render(<Button>Click me</Button>);

  const button = screen.getByRole('button', { name: /click me/i });
  expect(button).toBeInTheDocument();
});

