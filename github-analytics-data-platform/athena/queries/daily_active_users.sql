SELECT d.date, COUNT(DISTINCT f.actor_id) AS unique_users
FROM github_analytics_db.fact_events f
JOIN github_analytics_db.dim_date d ON f.event_date = d.date
GROUP BY d.date
ORDER BY d.date;
