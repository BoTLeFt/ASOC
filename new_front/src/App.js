import Table from "./Table";
import Dashboard from "./Dashboard";
import LoginForm from "./LoginForm";
import LogoutPage from "./LogoutPage";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom"

export default function App() {
  return (
    <Router>
      <div>
        <nav>
          <ul>
            <li>
              <Link to="/">Table</Link>
            </li>
            <li>
              <Link to="/login">Login</Link>
            </li>
            <li>
              <Link to="/logout">logout</Link>
            </li>
          </ul>
        </nav>

        <Routes>
          <Route path="/" element={<RenderTable />} />
          <Route path="/login" element={<Login />} />
          <Route path="/logout" element={<Logout />} />
        </Routes>
      </div>
    </Router>
  );
}

function Login() {
  return (
    <div>
      <LoginForm />
    </div>
  );
}

function RenderTable() {
  return (
    <div className="Table">
      <Dashboard />
      <Table />
    </div>
  );
}

function Logout() {
  return (
    <div>
      <LogoutPage />
    </div>
  );
}