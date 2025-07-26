# Agents overview for BoatBooking

This repository uses Codex agents to coordinate development across modules.

## Active agents

- **Architect_BoatRental** - handles overall architecture and repository standards.
- **Mobile_App_Agent** - manages all code under `mobile-app/` using React Native and Expo.
- **Backend_Agent** - responsible for serverless backend inside `backend/` and Amplify resources.
- **AdminPanel_Agent** - oversees the Next.js admin panel inside `admin-panel/`.

These roles are defined in `.codegpt/agents.yaml`. The main module configuration in `.codegpt.yaml` references this file via `agents_file` so Codex can automatically assign tasks based on the changed paths.

## Testing policy

- Do **not** remove or modify existing tests in `__tests__`, `__mocks__`, or `__snapshots__`.
- Always run `npm run test` and `npm run test:coverage` before pushing changes.
- Maintain coverage above 80%.

