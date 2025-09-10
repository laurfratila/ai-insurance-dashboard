import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Shell from "./layouts/Shell";
import Overview from "./routes/Overview";
import Claims from "./routes/Claims";
import Risk from "./routes/Risk";
import Ops from "./routes/Ops";
import C360 from "./routes/Customer360";
import Settings from "./routes/Settings";

export default function App() {
  return (
    <BrowserRouter>
      <Shell>
        <Routes>
          <Route path="/" element={<Navigate to="/overview" replace />} />
          <Route path="/overview" element={<Overview />} />
          <Route path="/claims" element={<Claims />} />
          <Route path="/risk" element={<Risk />} />
          <Route path="/ops" element={<Ops />} />
          <Route path="/c360" element={<C360 />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/overview" replace />} />
        </Routes>
      </Shell>
    </BrowserRouter>
  );
}
