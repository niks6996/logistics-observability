# Optional Slack notifications

The default lab proves Prometheus alert state transitions only. Alertmanager uses a null receiver.
No Slack messages have been sent or tested by this project bundle.

To enable notifications yourself, create a Slack incoming webhook and store it as a Kubernetes Secret
named `slack-webhook` in the monitoring namespace with a key named `url`. Never commit the URL.
Mount it using `alertmanager.alertmanagerSpec.secrets: [slack-webhook]` in a private Helm override.
Add a receiver under `alertmanager.config.receivers`:

```yaml
- name: slack
  slack_configs:
    - api_url_file: /etc/alertmanager/secrets/slack-webhook/url
      send_resolved: true
```

Add a child route matching `project="logistics"` to receiver `slack`.
Keep the default null route for unrelated cluster alerts. Apply your private override using Helm,
then repeat a fault-and-recovery test. Record both notifications with secrets redacted.
Check the webhook's destination channel before enabling this integration.
