import { lazy, type ReactElement, Suspense } from "react";
import { createBrowserRouter } from "react-router-dom";

import { NotFoundPage, RouteLoader } from "../components/RouteFallback";
import { AppShell } from "../layouts/AppShell";
import { ProtectedRoute } from "./ProtectedRoute";

const LoginPage = lazy(() => import("../auth/LoginPage").then((module) => ({ default: module.LoginPage })));
const SignupPage = lazy(() => import("../auth/SignupPage").then((module) => ({ default: module.SignupPage })));
const EnrollmentPage = lazy(() => import("../auth/EnrollmentPage").then((module) => ({ default: module.EnrollmentPage })));
const DashboardPage = lazy(() => import("../dashboard/DashboardPage").then((module) => ({ default: module.DashboardPage })));
const InterviewSetupPage = lazy(() => import("../interview/InterviewSetupPage").then((module) => ({ default: module.InterviewSetupPage })));
const InterviewPage = lazy(() => import("../interview/InterviewPage").then((module) => ({ default: module.InterviewPage })));
const CodingRoundPage = lazy(() => import("../code_execution/CodingRoundPage").then((module) => ({ default: module.CodingRoundPage })));
const ReportPage = lazy(() => import("../report/ReportPage").then((module) => ({ default: module.ReportPage })));

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
            path: "/enrollment",
            element: withSuspense(<EnrollmentPage />),
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
