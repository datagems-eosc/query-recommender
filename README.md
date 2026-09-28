The documentation is available at: [https://datagems-eosc.github.io/query-recommender/latest/](https://datagems-eosc.github.io/query-recommender/latest/)

## Environment variables

| Variable | Description |
|---|---|
| `LLM_TOKEN` | Bearer token for the LLM API |
| `LLM_API_URL` | Full URL of the LLM chat completions endpoint |
| `USER_PROFILER_API_URL` | Base URL of the User Profiler API, used to fetch a user's interest keywords for recommendations. Defaults to `http://localhost:8000`. In the cluster this is `http://user-profiler-service:5000` (namespace `univr`). |

If `USER_PROFILER_API_URL` is unreachable, or the given `user_id` doesn't exist, recommendations are generated with an empty keyword set instead of failing.

## Streamlit demo

`app.py` is a chatbot-style demo: type a natural language query and the API returns 3 recommended next queries, shown as buttons. Clicking one sends it as the next query.

```bash
pip install streamlit        # not included in the project dependencies
streamlit run app.py
```

In the sidebar you can choose which API to use:

| Option | URL |
|---|---|
| Local | `http://localhost:5000/api/v1` (override with the `QR_API_URL` environment variable) |
| Remote (dev) | `https://datagems-dev.scayle.es/qr/api/v1` |
| Custom | any base URL you enter |

To use the local option, start the API first with `python -m qr_api.main` (it listens on port 5000). The sidebar also has an optional user ID, sent as `context.user_id`, a request timeout, an API status check and a button to clear the chat.