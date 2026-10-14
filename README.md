# Email action-item agent

A runnable Python agent for a personal Gmail mailbox. It reads matching emails,
extracts action items and quoted deadlines, and writes Markdown and JSON reports.
The model chooses tool calls in a bounded loop; Python executes and validates them.

## 1. Install (Mac, Linux; Python 3.10+)

Unzip this project, open Terminal in its folder, and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 2. Configure OpenAI

Create an API key at https://platform.openai.com/api-keys and enable API billing.
The agent uses your OpenAI API account; configure billing separately from ChatGPT.
Enter the key without putting it directly in your shell history:

```bash
read -s -p 'OpenAI API key: ' OPENAI_API_KEY
export OPENAI_API_KEY
echo
```

The command above is for Bash. In macOS's default zsh, use:

```zsh
read -s 'OPENAI_API_KEY?OpenAI API key: '
export OPENAI_API_KEY
echo
```

The default model is `gpt-4o-mini`; change it using `--model` or `OPENAI_MODEL`
if your API account offers a different Responses-compatible tool-calling model.

## 3. Try synthetic emails first

```bash
python agent.py --sample
cat output/report.md
```

This requires the model API key and incurs API usage, but requires no Gmail access.
Expected action items: return a permission form (October 16, 2026) and review a
 design document (no deadline). The sample includes an injection attempt and FYIs.

## 4. Connect Gmail

1. Open https://console.cloud.google.com/ and create/select a project.
2. Enable the Gmail API.
3. Configure Google Auth platform branding and audience. For personal Gmail,
   use External and add your Gmail account as a test user while in Testing.
4. Configure Data Access with `https://www.googleapis.com/auth/gmail.readonly`.
5. Create an OAuth client with application type **Desktop app**.
6. Download its JSON and save it as `credentials.json` beside `agent.py`.
7. Run the command below. A browser opens for you to select and authorize Gmail.

```bash
python agent.py --query 'in:inbox newer_than:1d -from:me' --limit 10
cat output/report.md
```

Read access does not mark messages read. This implementation cannot send mail,
change labels, delete mail, or create external tasks. OAuth credentials are cached
locally in `token.json`; delete it to switch accounts. Testing-mode OAuth access
may need periodic reauthorization. Workspace administrators can restrict access.

## 5. Evaluate

Offline implementation tests (no credentials or third-party packages required):

```bash
python -m unittest -v
```

Live behavior eval (model API usage; synthetic emails only):

```bash
python eval_agent.py
```

The live eval checks task selection, deadlines, FYIs, completed requests, and an
injection attempt. Run it repeatedly when changing prompts or models; a passing
fixture set is not a guarantee for every real email.

## 6. Customize and run again

```bash
python agent.py --query 'in:inbox newer_than:7d -from:me' --limit 25 --max-steps 70 --output weekly
```

`newer_than:1d` is a rolling day, not necessarily midnight-to-now. For a specific
calendar date, supply Gmail's `after:YYYY/MM/DD before:YYYY/MM/DD` search operators.
The time context defaults to America/Los_Angeles; override with `--timezone`.
There are at most 25 emails per run. A report says when more emails match; it is
not a full-mailbox scan. Increase scope deliberately or split date ranges.

Reports overwrite the files in the selected output folder. Run in a new output
folder to preserve earlier reports. Repeated runs can show the same task: this
starter has no task-completion database or cross-run deduplication.

For daily automation, schedule this same CLI with a local scheduler after OAuth
setup. Supply an API key securely to that process, use absolute paths, and set the
working directory to this project. Scheduling is not enabled by this package.

## How the agent works

1. Python searches Gmail with the user-controlled query and limit.
2. The model receives the matching message IDs.
3. It calls `read_email`; Python fetches and returns a message body.
4. It repeats until every selected email has been read.
5. It calls `submit_report` with extracted tasks.
6. Python rejects unread sources, fabricated quotes and fabricated deadline text.
7. Python writes a report with usage totals, coverage limits and truncation notes.

The two tool schemas, instructions, and execution loop are in `agent.py`.
`test_agent.py` tests execution and validation; `eval_agent.py` tests model behavior.
No agent framework is required beyond the model SDK and Gmail client libraries.

## Limits and privacy

Selected email bodies are sent to the OpenAI API for analysis. Responses requests
use `store=False`; this does not override the provider's applicable data policies.
Use only a mailbox whose content you are authorized to process. Credentials and
reports are excluded from git; token and output permissions are restricted locally.

Attachments are skipped. Plain text is preferred over HTML; HTML-only mail is
converted to text. Bodies over 24,000 characters are truncated and flagged.
The agent does not inspect full threads or resolve later replies outside the query,
so review the original conversation before acting on a task. Relative deadlines
remain as quoted text; reminders and normalized due dates are not created.
Exact-quote validation establishes textual provenance, not semantic correctness.
Model instructions reduce injection risk; read-only tool permissions enforce the
lack of mailbox mutations. Reports still need human review.

Each model request has a 60-second timeout and up to two retries; Gmail uses up to
two retries. Step and output-token limits bound a run, but are not a dollar budget.
Check usage in report.json and configure API account spending controls separately.

## Troubleshooting

- Missing packages: activate `.venv` and reinstall requirements.
- Missing credentials.json: download a Desktop OAuth client, not a service account.
- OAuth access denied: check test-user registration and Workspace admin policy.
- Expired/revoked token: delete token.json and authorize again.
- API errors: check key, billing, selected model access, and network connectivity.
- Step limit: lower `--limit` or raise `--max-steps` (maximum 100).
- No valid report: rerun the live eval; inspect the source emails and adjust scope.

## Official references

- OpenAI function calling: https://developers.openai.com/api/docs/guides/function-calling
- Gmail Python/OAuth setup: https://developers.google.com/workspace/gmail/api/quickstart/python

Validation of this delivered package: offline tests were run. Live Gmail and
OpenAI execution require your credentials and were not run during creation.
