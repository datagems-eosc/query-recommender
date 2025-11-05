# qr-api
This project contains the API specifications for the Query Recommender system.

# Sample usage
curl -X POST -H "Content-Type: application/json" --data '@qr_api/tests/sample_query.json' http://localhost:5000/api/v1/recommend-next-query