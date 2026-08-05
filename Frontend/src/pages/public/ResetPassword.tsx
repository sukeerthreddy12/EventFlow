import { useMemo, useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import { confirmPasswordReset } from "../../api/accounts";

export default function ResetPassword() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const initialToken = useMemo(() => params.get("token") ?? "", [params]);

  const [token, setToken] = useState(initialToken);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setMessage(null);

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await confirmPasswordReset({
        token: token.trim(),
        new_password: newPassword,
        new_password_confirm: confirmPassword,
      });
      setMessage(res.message);
      setTimeout(() => navigate("/login"), 800);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const data = err.response?.data;
        setError(
          typeof data === "object"
            ? JSON.stringify(data)
            : "Reset failed.",
        );
      } else {
        setError("Reset failed.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="layout-main--padded" style={{ maxWidth: 420 }}>
      <h1 className="page-title">Reset password</h1>
      <p className="page-sub">
        Paste the token from your email, or open the reset link which fills it
        automatically.
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
        <label>
          New password
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            minLength={8}
          />
        </label>
        <label>
          Confirm password
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            minLength={8}
          />
        </label>

        {error && <p className="state-msg state-msg--error">{error}</p>}
        {message && <p className="state-msg">{message}</p>}

        <button className="btn btn-primary" type="submit" disabled={submitting}>
          {submitting ? "Saving…" : "Update password"}
        </button>
      </form>

      <p className="page-sub">
        <Link to="/login">Back to sign in</Link>
      </p>
    </div>
  );
}
