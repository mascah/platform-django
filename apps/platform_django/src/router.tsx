import { createBrowserRouter } from 'react-router';

import { ProtectedRoute } from '@/features/auth';
import { DashboardPage } from '@/features/dashboard/pages/dashboard-page';
import { AppLayout } from '@/features/layout';

export const router = createBrowserRouter(
  [
    {
      element: (
        <ProtectedRoute>
          <AppLayout />
        </ProtectedRoute>
      ),
      children: [
        {
          index: true,
          element: <DashboardPage />,
        },
      ],
    },
  ],
  {
    basename: '/app',
  },
);
