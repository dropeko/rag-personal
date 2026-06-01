import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { SearchPage, ReportPage, NotFound } from '@data-platforms/db-frontend-lib/pages';
import { EditReportPage } from './pages/EditReportPage';
import { HomePage } from './pages/HomePage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* wo-frontend home */}
        <Route path="/" element={<HomePage />} />

        {/* Pages shared from db-frontend-lib */}
        <Route path="/search" element={<SearchPage />} />
        <Route path="/report/:id" element={<ReportPage />} />

        {/* wo-frontend specific routes */}
        <Route path="/edit/:id" element={<EditReportPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />


        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

