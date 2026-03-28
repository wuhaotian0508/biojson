# Function Examples

Auto-generated standalone examples for every method in `TokenTracker`.

## token_tracker.py

| Method | Description | Run |
|--------|-------------|-----|
| `TokenTracker.__init__` | Initialize a thread-safe API token usage tracker | `python examples/token_tracker/TokenTracker___init__.py` |
| `TokenTracker.add` | Record token usage from an API response (thread-safe) | `python examples/token_tracker/TokenTracker_add.py` |
| `TokenTracker._aggregate` | Aggregate token stats, optionally filtered by stage | `python examples/token_tracker/TokenTracker__aggregate.py` |
| `TokenTracker.get_summary` | Get a dict summarizing token usage grouped by stage, plus a total | `python examples/token_tracker/TokenTracker_get_summary.py` |
| `TokenTracker.print_summary` | Print a formatted table of total token usage and call count | `python examples/token_tracker/TokenTracker_print_summary.py` |
| `TokenTracker.save_report` | Save a detailed JSON usage report to disk | `python examples/token_tracker/TokenTracker_save_report.py` |
| `TokenTracker.merge` | Merge another TokenTracker's records into this one (thread-safe) | `python examples/token_tracker/TokenTracker_merge.py` |
