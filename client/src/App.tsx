import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { ProjectView } from "./pages/ProjectView";
import { ProjectsList } from "./pages/ProjectsList";
import { Settings } from "./pages/Settings";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="/projects" element={<ProjectsList />} />
        <Route path="/projects/:projectId" element={<ProjectView />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}
