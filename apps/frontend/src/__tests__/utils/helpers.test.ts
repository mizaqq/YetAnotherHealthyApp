/**
 * Simple utility test to verify Vitest setup
 */

import { describe, it, expect } from 'vitest';

function add(a: number, b: number): number {
  return a + b;
}

describe('helpers', () => {
  it('adds two numbers', () => {
    const result = add(2, 3);
    expect(result).toBe(5);
  });
});

