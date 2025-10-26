/**
 * Simple hook test to verify Vitest setup
 */

import { renderHook, act } from '@testing-library/react';
import { useState } from 'react';

// Simple counter hook for testing
function useCounter(initialValue = 0) {
  const [count, setCount] = useState(initialValue);

  const increment = () => setCount((c) => c + 1);

  return { count, increment };
}

it('increments counter', () => {
  const { result } = renderHook(() => useCounter());

  act(() => {
    result.current.increment();
  });

  expect(result.current.count).toBe(1);
});

