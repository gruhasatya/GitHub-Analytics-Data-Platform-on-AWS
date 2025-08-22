SELECT r.repo_name, COUNT(*) AS total_events
FROM github_analytics_db.fact_events f
JOIN github_analytics_db.dim_repo r ON f.repo_id = r.repo_id
GROUP BY r.repo_name
ORDER BY total_events DESC
LIMIT 10;
