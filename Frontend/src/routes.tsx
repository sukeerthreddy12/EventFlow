import { Navigate, Route, Routes } from "react-router-dom";
import PublicLayout from "./layouts/PublicLayout";
import AttendeeLayout from "./layouts/AttendeeLayout";
import OrganiserLayout from "./layouts/OrganiserLayout";
import RequireAuth from "./auth/RequireAuth";
import RequireRole from "./auth/RequireRole";
import Landing from "./pages/public/Landing";
import Login from "./pages/public/Login";
import Register from "./pages/public/Register";
import VerifyEmail from "./pages/public/VerifyEmail";
import ForgotPassword from "./pages/public/ForgotPassword";
import ResetPassword from "./pages/public/ResetPassword";
import EventCatalog from "./pages/attendee/EventCatalog";
import EventDetail from "./pages/attendee/EventDetail";
import MyRegistrations from "./pages/attendee/MyRegistrations";
import MyEvents from "./pages/organiser/MyEvents";
import EventForm from "./pages/organiser/EventForm";
import CheckIn from "./pages/organiser/CheckIn";
import TicketView from "./pages/attendee/TicketView";

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/verify-email" element={<VerifyEmail />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
      </Route>

      <Route path="/app" element={<AttendeeLayout />}>
        <Route index element={<Navigate to="events" replace />} />
        <Route path="events" element={<EventCatalog />} />
        <Route path="events/:id" element={<EventDetail />} />
        <Route element={<RequireAuth />}>
          <Route element={<RequireRole roles={["ATTENDEE", "ADMIN"]} />}>
            <Route path="my-registrations" element={<MyRegistrations />} />
            <Route path="tickets/:registrationId" element={<TicketView />} />
          </Route>
        </Route>
      </Route>

      <Route element={<RequireAuth />}>
        <Route element={<RequireRole roles={["ORGANISER", "ADMIN"]} />}>
          <Route path="/org" element={<OrganiserLayout />}>
            <Route index element={<Navigate to="events" replace />} />
            <Route path="events" element={<MyEvents />} />
            <Route path="events/new" element={<EventForm />} />
            <Route path="events/:id" element={<EventForm />} />
            <Route path="events/:id/check-in" element={<CheckIn />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
