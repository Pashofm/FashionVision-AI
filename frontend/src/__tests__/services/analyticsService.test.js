import { beforeEach, describe, expect, it, vi } from 'vitest';

const { authenticatedFetch } = vi.hoisted(() => ({
  authenticatedFetch: vi.fn()
}));

vi.mock('../../services/api', () => ({ authenticatedFetch }));

import { analyticsService } from '../../services/analyticsService';

describe('analyticsService', () => {
  beforeEach(() => {
    authenticatedFetch.mockReset();
  });

  it('builds the dashboard URL through the relative API proxy', async () => {
    authenticatedFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({})
    });

    await analyticsService.getSummary();

    expect(authenticatedFetch).toHaveBeenCalledWith(
      '/api/analytics/dashboard/summary?period=weekly'
    );
  });
});
