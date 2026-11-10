import { Route, Routes } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout";
import ComingSoon from "./pages/ComingSoon";
import Dashboard from "./pages/Dashboard";
import DesignSystem from "./pages/DesignSystem";
import Stock from "./pages/Stock";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/stocks/:symbol" element={<Stock />} />
        <Route path="/design" element={<DesignSystem />} />
        <Route path="/markets" element={<ComingSoon title="Markets">Browse every stock and index by exchange and sector. Until then, use the search box to open any stock.</ComingSoon>} />
        <Route path="/watchlist" element={<ComingSoon title="Watchlist">Follow the stocks you care about in one list.</ComingSoon>} />
        <Route path="/portfolio" element={<ComingSoon title="Portfolio">Track a paper portfolio and see its risk and correlations.</ComingSoon>} />
        <Route path="/analysis" element={<ComingSoon title="Analysis">Return distributions and statistical tests such as ADF, ARCH and Jarque Bera.</ComingSoon>} />
        <Route path="/risk" element={<ComingSoon title="Risk">Volatility, drawdown, value at risk and GARCH family models.</ComingSoon>} />
        <Route path="/forecast" element={<ComingSoon title="Forecast">Compare naive, ARIMA, GARCH, LSTM and hybrid volatility forecasts.</ComingSoon>} />
        <Route path="/settings" element={<ComingSoon title="Settings">Preferences will appear here.</ComingSoon>} />
        <Route path="*" element={<ComingSoon title="Page not found">That address does not exist. Use the sidebar to continue.</ComingSoon>} />
      </Route>
    </Routes>
  );
}
