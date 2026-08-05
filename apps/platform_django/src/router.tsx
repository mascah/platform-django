import { createBrowserRouter } from 'react-router';

import { ProtectedRoute } from '@/features/auth';
import { DashboardPage } from '@/features/dashboard/pages/dashboard-page';
import { AppLayout } from '@/features/layout';
import { RouteErrorBoundary } from '@/features/monitoring';

export const router = createBrowserRouter(
  [
    {
      element: (
        <ProtectedRoute>
          <AppLayout />
        </ProtectedRoute>
      ),
      // On the root route so it catches everything below it, including a URL
      // that matches no child. Without one, React Router renders its own
      // boundary and the error is reported nowhere.
      errorElement: <RouteErrorBoundary />,
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
