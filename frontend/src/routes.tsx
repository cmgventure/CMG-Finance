import { createBrowserRouter } from "react-router-dom";
import BasicLayout from "./layout/BasicLayout";
import NotFoundPage from "./pages/error/NotFound";
import MainPage from "./pages/index";

const router = createBrowserRouter([
  {
    element: <BasicLayout />,
    children: [
      {
        path: "/",
        element: <MainPage />,
      },
    ],
    errorElement: <NotFoundPage />,
  },
]);

export default router;
