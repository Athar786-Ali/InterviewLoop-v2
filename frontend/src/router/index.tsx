import { lazy, type ReactElement, Suspense } from "react";
import { createBrowserRouter } from "react-router-dom";

import { NotFoundPage, RouteLoader } from "../components/RouteFallback";
import { AppShell } from "../layouts/AppShell";
import { ProtectedRoute } from "./ProtectedRoute";

const LoginPage = lazy(() => import("../auth/LoginPage").then((m) => ({ default: m.LoginPage })));
const SignupPage = lazy(() => import("../auth/SignupPage").then((m) => ({ default: m.SignupPage })));
const DashboardPage = lazy(() => import("../dashboard/DashboardPage").then((m) => ({ default: m.DashboardPage })));
const InterviewSetupPage = lazy(() => import("../interview/InterviewSetupPage").then((m) => ({ default: m.InterviewSetupPage })));
const InterviewPage = lazy(() => import("../interview/InterviewPage").then((m) => ({ default: m.InterviewPage })));
const CodingRoundPage = lazy(() => import("../code_execution/CodingRoundPage").then((m) => ({ default: m.CodingRoundPage })));
const ReportPage = lazy(() => import("../report/ReportPage").then((m) => ({ default: m.ReportPage })));

function withSuspense(element: ReactElement) {
  return <Suspense fallback={<RouteLoader />}>{element}</Suspense>;
}

export const router = createBrowserRouter([
  {
    path: "/login",
    element: withSuspense(<LoginPage />),
  },
  {
    path: "/signup",
    element: withSuspense(<SignupPage />),
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppShell />,
        children: [
          {
            path: "/",
            element: withSuspense(<DashboardPage />),
          },
          {
            path: "/interview/setup",
            element: withSuspense(<InterviewSetupPage />),
          },
          {
            path: "/interview/:sessionId",
            element: withSuspense(<InterviewPage />),
          },
          {
            path: "/coding",
            element: withSuspense(<CodingRoundPage />),
          },
          {
            path: "/reports",
            element: withSuspense(<ReportPage />),
          },
          {
            path: "*",
            element: <NotFoundPage />,
          },
        ],
      },
    ],
  },
]);
