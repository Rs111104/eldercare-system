Secrets handling

- `.env` must never be committed. Use `.env.example` as the template.
- Secrets should be stored in a secrets manager (AWS Secrets Manager, GitHub Secrets, Vault).
- To remove a committed `.env` from git history, run `scripts/remove_env_from_git_history.sh` and follow the instructions.
