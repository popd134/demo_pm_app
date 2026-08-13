import { Button, Card, SkeletonLines } from "../components/ui";
import { LoginForm } from "../components/auth/LoginForm";
import { PreferencesForm } from "../components/settings/PreferencesForm";
import { SavedLocationsManager } from "../components/settings/SavedLocationsManager";
import { useAuth } from "../context/AuthContext";

/**
 * Settings page (WBS 1.6.2): manage saved locations, preferred units and alert rules.
 * Gated behind authentication; shows a login/register form when signed out.
 */
export function SettingsPage() {
  const { status, user, logout } = useAuth();

  return (
    <div>
      <h2 className="section-heading">Settings</h2>

      {status === "loading" && (
        <Card>
          <SkeletonLines lines={3} />
        </Card>
      )}

      {status === "anonymous" && (
        <Card title="Sign in" subtitle="Sign in to manage your preferences and saved locations.">
          <LoginForm />
        </Card>
      )}

      {status === "authenticated" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-lg)" }}>
          <Card
            title="Account"
            actions={
              <Button variant="ghost" onClick={logout}>
                Sign out
              </Button>
            }
          >
            <p className="section-subtle">
              Signed in as <strong>{user?.email}</strong> ({user?.role}).
            </p>
          </Card>

          <Card title="Preferences" subtitle="Preferred units and alert thresholds">
            <PreferencesForm />
          </Card>

          <Card title="Saved locations" subtitle="Locations pinned to your account">
            <SavedLocationsManager />
          </Card>
        </div>
      )}
    </div>
  );
}
