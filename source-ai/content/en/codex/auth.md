---
title: Authentication
source_id: codex/auth
product: codex
lang: en
canonical_url: https://developers.openai.com/codex/auth
owner: OpenAI
content_sha256: f58241b4827ad593bda425cfccd251c0bac4c0e066dfd924e6766cc4a4887ae9
---
[Official source](https://developers.openai.com/codex/auth)

Content owner: OpenAI

# Authentication

> For the complete documentation index, see [llms.txt](https://learn.chatgpt.com/llms.txt). Markdown versions of documentation pages are available by appending `.md` to the page URL.

## OpenAI authentication

<a id="sign-in-with-chatgpt"></a>



Codex supports two ways to sign in when using OpenAI models:

- Sign in with ChatGPT for subscription access
- Sign in with an API key for usage-based access

The ChatGPT desktop app, Codex CLI, and IDE extension support both sign-in
methods for local work. Codex cloud requires signing in with ChatGPT.

Your sign-in method also determines which admin controls and data-handling policies apply.

- When you sign in with ChatGPT, Codex usage follows your ChatGPT workspace
  permissions, role-based access control (RBAC), and ChatGPT Enterprise
  retention and residency settings.
- With an API key, usage follows your API organization's retention and
  data-sharing settings instead.

For managed workspaces, authentication is only one layer of access. Workspace
membership and provisioning determine who can sign in, while seats and
workspace roles determine which product surfaces and features they can use.
For local work in the ChatGPT desktop app, Codex CLI, or IDE extension,
permission profiles constrain what the agent can do on the device. See
[Groups and provisioning](https://learn.chatgpt.com/docs/enterprise/groups-and-provisioning)
and [Roles and workspace permissions](https://learn.chatgpt.com/docs/enterprise/roles-and-workspace-permissions)
to plan those controls.

### Sign in with ChatGPT

When you sign in with ChatGPT from the ChatGPT desktop app, Codex CLI, or IDE extension, the sign-in flow opens a browser window. After you sign in, the browser returns your credentials to Codex.







#### ChatGPT desktop app

On the signed-out screen, select **Continue to sign in**, then complete the
browser flow.







<a id="sign-in-with-an-api-key"></a>



### Sign in with an API key

You can also sign in to the ChatGPT desktop app, Codex CLI, or IDE extension with an API key. Get your API key from the [OpenAI dashboard](https://platform.openai.com/api-keys).





#### ChatGPT desktop app

On the signed-out screen, select **Sign in another way**, enter your key, then
select **Continue**.









OpenAI bills API key usage through your OpenAI Platform account at standard API rates. See the [API pricing page](https://openai.com/api/pricing/).

API key authentication supports local Codex workflows, but some features that
rely on ChatGPT workspace access or cloud services are limited or unavailable.
Compare support by plan in
[Feature availability](https://learn.chatgpt.com/docs/pricing#feature-availability).

In Codex CLI and Codex in the ChatGPT desktop app, API key authentication
includes access to supported OpenAI-curated plugins. Some plugins aren't
available because their connection flows require unsupported OAuth
capabilities. See [Use plugins](https://learn.chatgpt.com/docs/plugins#api-key-availability).

When you sign in with an API key, Codex uses standard API pricing instead of
included ChatGPT plan credits.

Use API key authentication for programmatic Codex CLI workflows, such as CI/CD
jobs. Don't expose Codex execution in untrusted or public environments.



### Check authentication or sign out





Open the profile menu to see the active account or API key status. Select
**Log out** to clear the current credentials.









### Use Codex access tokens for enterprise automation

In ChatGPT Enterprise workspaces, admins can grant the access token
permission so permitted members can create Codex access tokens for trusted,
non-interactive Codex local workflows. Use an access token when automation
needs ChatGPT workspace access, ChatGPT-managed Codex entitlements, or
enterprise workspace controls without a browser sign-in.

Access tokens are intended for trusted scripts, schedulers, and private CI
runners. For general OpenAI API calls, continue to use Platform API keys.

For setup steps, permissions, rotation, and revocation guidance, see
[Access tokens](https://learn.chatgpt.com/docs/enterprise/access-tokens).







## Secure your Codex cloud account

Codex cloud interacts directly with your codebase, so it needs stronger security than many other ChatGPT features. Enable multi-factor authentication (MFA).

If you use a social login provider (Google, Microsoft, Apple), you aren't required to enable MFA on your ChatGPT account, but you can set it up with your social login provider.

For setup instructions, see:

- [Google](https://support.google.com/accounts/answer/185839)
- [Microsoft](https://support.microsoft.com/en-us/topic/what-is-multifactor-authentication-e5e39437-121c-be60-d123-eda06bddf661)
- [Apple](https://support.apple.com/en-us/102660)

If you access ChatGPT through single sign-on (SSO), your organization's SSO administrator should enforce MFA for all users.

If you log in using an email and password, you must set up MFA on your account before accessing Codex cloud.

If your account supports more than one login method and one of them is email and password, you must set up MFA before accessing Codex, even if you sign in another way.



<a id="login-caching"></a>



## Login caching

When you sign in to the ChatGPT desktop app, Codex CLI, or IDE extension using either ChatGPT or an API key, your login details are cached and reused. The CLI and extension share the same cached login details. If you log out from either one, you'll need to sign in again the next time you start the CLI or extension.

Codex caches login details locally in a plaintext file at `~/.codex/auth.json` or in your OS-specific credential store.

For sign in with ChatGPT sessions, Codex refreshes tokens automatically during use before they expire, so active sessions usually continue without requiring another browser login.



<a id="credential-storage"></a>
<a id="enforce-a-login-method-or-workspace"></a>



## Credential storage

Use `cli_auth_credentials_store` to control where the Codex CLI stores cached credentials:

```toml
# file | keyring | auto

cli_auth_credentials_store = "keyring"
```

- `file` stores credentials in `auth.json` under `CODEX_HOME` (defaults to `~/.codex`).
- `keyring` stores credentials in your operating system credential store.
- `auto` uses the OS credential store when available, otherwise falls back to `auth.json`.

See the [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference) for the complete
`config.toml` schema.

If you use file-based storage, treat `~/.codex/auth.json` like a password: it
  contains access tokens. Don't commit it, paste it into tickets, or share it in
  chat.

## Enforce a login method or workspace

In managed environments, admins may restrict how users are allowed to authenticate:

```toml
# Only allow ChatGPT login or only allow API key login.

forced_login_method = "chatgpt" # or "api"

# When using ChatGPT login, restrict users to a specific workspace.

forced_chatgpt_workspace_id = "00000000-0000-0000-0000-000000000000"
```

If the active credentials don't match the configured restrictions, Codex logs the user out and exits.

These settings are commonly applied via managed configuration rather than per-user setup. See [Managed configuration](https://learn.chatgpt.com/docs/enterprise/managed-configuration).







## Alternative model providers

When you define a [custom model provider](https://learn.chatgpt.com/docs/config-file/config-advanced#custom-model-providers) in your configuration file, you can choose one of these authentication methods:

- **OpenAI authentication**: Set `requires_openai_auth = true` to use OpenAI authentication. You can then sign in with ChatGPT or an API key. This is useful when you access OpenAI models through an LLM proxy server. When `requires_openai_auth = true`, Codex ignores `env_key`.
- **Environment variable authentication**: Set `env_key = "<ENV_VARIABLE_NAME>"` to use a provider-specific API key from the local environment variable named `<ENV_VARIABLE_NAME>`.
- **No authentication**: If you don't set `requires_openai_auth` (or set it to `false`) and you don't set `env_key`, Codex assumes the provider doesn't require authentication. This is useful for local models.
