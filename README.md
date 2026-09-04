The documentation is available at: [https://datagems-eosc.github.io/query-recommender/latest/](https://datagems-eosc.github.io/query-recommender/latest/)

## Environment variables

| Variable | Description |
|---|---|
| `LLM_TOKEN` | Bearer token for the LLM API |
| `LLM_API_URL` | Full URL of the LLM chat completions endpoint |
| `USER_PROFILER_API_URL` | Base URL of the User Profiler API, used to fetch a user's interest keywords for recommendations. Defaults to `http://localhost:8000`. In the cluster this is `http://user-profiler-service:5000` (namespace `univr`). |

If `USER_PROFILER_API_URL` is unreachable, or the given `user_id` doesn't exist, recommendations are generated with an empty keyword set instead of failing.