import { useMemo, useState, type FormEvent } from "react";
import {
  Link,
  useLocation,
  useNavigate,
  useSearchParams,
} from "react-router-dom";
import axios from "axios";
import { verifyEmail } from "../../api/accounts";

export default function VerifyEmail() {
  const navigate = useNavigate();
  const location = useLocation();
  const [params] = useSearchParams();
  const emailFromRegister = (location.state as { email?: string } | null)
    ?.email;

  const initialToken = useMemo(() => params.get("token") ?? "", [params]);
  const [token, setToken] = useState(initialToken);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setSubmitting(true);
    try {
      const res = await verifyEmail(token.trim());
      setMessage(res.message);
      setTimeout(() => navigate("/login"), 800);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const data = err.response?.data;
        setError(
          typeof data === "object"
            ? JSON.stringify(data)
            : "Verification failed.",
        );
      } else {
        setError("Verification failed.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="layout-main--padded" style={{ maxWidth: 420 }}>
      <h1 className="page-title">Verify email</h1>
      <p className="page-sub">
        {emailFromRegister
          ? `We sent a link for ${emailFromRegister}. In local dev, check the Django runserver terminal for the token.`
          : "Paste the token from your email (or Django terminal), or open the verify link."}
      </p>

      <form onSubmit={onSubmit} className="auth-form">
        <label>
          Token
          <input
            value={token}
            onChange={(e) => setToken(e.target.value)}
            required
          />
        </label>

        {error && <p className="state-msg state-msg--error">{error}</p>}
        {message && <p className="state-msg">{message}</p>}

        <button className="btn btn-primary" type="submit" disabled={submitting}>
          {submitting ? "Verifying…" : "Verify"}
        </button>
      </form>

      <p className="page-sub">
        Ready? <Link to="/login">Sign in</Link>
      </p>
    </div>
  );
}
