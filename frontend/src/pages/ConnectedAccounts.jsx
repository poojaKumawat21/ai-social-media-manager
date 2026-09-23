import React, { useEffect, useState } from "react";
import { CheckCircle2, Link2 } from "lucide-react";

import api from "../services/api";

import "./ConnectedAccounts.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const initialAccounts = [
  {
    id: 1,
    name: "Instagram",
    username: "@yourbrand",
    description:
      "Connect your Instagram account to publish and manage posts.",
    connected: false,
  },
  {
    id: 2,
    name: "Facebook",
    username: "Your Facebook Page",
    description:
      "Publish content directly to your Facebook page.",
    connected: false,
  },
  {
    id: 3,
    name: "LinkedIn",
    username: "Your LinkedIn Page",
    description:
      "Share professional content with your LinkedIn audience.",
    connected: false,
  },
  {
    id: 4,
    name: "X",
    username: "@yourbrand",
    description:
      "Create and publish short-form content on X.",
    connected: false,
  },
];

function ConnectedAccounts() {
  const [accounts, setAccounts] = useState(initialAccounts);

  const getPlatformIcon = () => {
    return <Link2 size={22} />;
  };

  // ============================================================
  // CONNECT ACCOUNT
  // ============================================================

  const handleConnect = async (account) => {
    try {
      const platform = account.name.toLowerCase();

      // ----------------------------------------------------------
      // INSTAGRAM
      // ----------------------------------------------------------
      if (platform === "instagram") {
        const result = await api.get(
          "/social-accounts/oauth/instagram/start"
        );

        const authorizationUrl =
          result?.authorization_url ||
          result?.data?.authorization_url;

        if (!authorizationUrl) {
          throw new Error(
            "Instagram authorization URL was not returned."
          );
        }

        window.location.href = authorizationUrl;
        return;
      }

      // ----------------------------------------------------------
      // LINKEDIN
      // ----------------------------------------------------------
      if (platform === "linkedin") {
        const result = await api.get(
          "/social-accounts/oauth/linkedin/start"
        );

        const authorizationUrl =
          result?.authorization_url ||
          result?.data?.authorization_url;

        if (!authorizationUrl) {
          throw new Error(
            "LinkedIn authorization URL was not returned."
          );
        }

        window.location.href = authorizationUrl;
        return;
      }

      // ----------------------------------------------------------
      // X
      // ----------------------------------------------------------
      if (platform === "x") {
        const result = await api.get(
          "/social-accounts/oauth/x/start"
        );

        const authorizationUrl =
          result?.authorization_url ||
          result?.data?.authorization_url;

        if (!authorizationUrl) {
          throw new Error(
            "X authorization URL was not returned."
          );
        }

        window.location.href = authorizationUrl;
        return;
      }

      // ----------------------------------------------------------
      // OTHER / NOT AVAILABLE
      // ----------------------------------------------------------
      alert(
        `${account.name} connection is not available yet.`
      );
    } catch (error) {
      console.error(
        `Failed to connect ${account.name}:`,
        error
      );

      const errorMessage =
        error?.response?.data?.detail ||
        error?.message ||
        `Could not connect ${account.name}. Please try again.`;

      alert(errorMessage);
    }
  };

  // ============================================================
  // LOAD CONNECTED ACCOUNTS
  // ============================================================

  useEffect(() => {
    const loadConnectedAccounts = async () => {
      try {
        const result = await api.get("/social-accounts");

        const connectedAccounts =
          result?.accounts ||
          result?.data?.accounts ||
          result?.data ||
          result ||
          [];

        setAccounts((currentAccounts) =>
          currentAccounts.map((account) => {
            const connectedAccount = Array.isArray(
              connectedAccounts
            )
              ? connectedAccounts.find(
                  (item) =>
                    item?.platform?.toLowerCase() ===
                    account.name.toLowerCase()
                )
              : null;

            return {
              ...account,
              connected: !!connectedAccount,
              username:
                connectedAccount?.account_name ||
                account.username,
            };
          })
        );
      } catch (error) {
        console.error(
          "Failed to load connected accounts:",
          error
        );
      }
    };

    loadConnectedAccounts();
  }, []);

  // ============================================================
  // UI
  // ============================================================

  return (
    <div className="connected-accounts-page">
      <div className="connected-header">
        <div>
          <h1>Connected Accounts</h1>

          <p>
            Connect and manage your social media accounts
            from one place.
          </p>
        </div>
      </div>

      <div className="connected-summary">
        <div className="connected-summary-icon">
          <Link2 size={20} />
        </div>

        <div>
          <span>Connected Platforms</span>

          <strong>
            {
              accounts.filter(
                (account) => account.connected
              ).length
            }{" "}
            / {accounts.length}
          </strong>
        </div>
      </div>

      <div className="connected-accounts-grid">
        {accounts.map((account) => (
          <div
            className="connected-account-card"
            key={account.id}
          >
            <div className="account-card-top">
              <div
                className={`account-platform-icon ${account.name.toLowerCase()}`}
              >
                {getPlatformIcon(account.name)}
              </div>

              {account.connected && (
                <div className="account-connected-status">
                  <CheckCircle2 size={14} />
                  Connected
                </div>
              )}
            </div>

            <div className="account-card-content">
              <h2>{account.name}</h2>

              <span className="account-username">
                {account.username}
              </span>

              <p>{account.description}</p>
            </div>

            <button
              type="button"
              className={
                account.connected
                  ? "account-connect-button connected"
                  : "account-connect-button"
              }
              onClick={() =>
                handleConnect(account)
              }
            >
              {account.connected
                ? "Connected"
                : "Connect"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ConnectedAccounts;