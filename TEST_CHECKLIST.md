# Submission Test Checklist

## Connection
- [ ] Monday token works
- [ ] Deals board ID is correct
- [ ] Work Orders board ID is correct
- [ ] Invalid token gives a readable error
- [ ] Invalid board ID gives a readable error

## BI
- [ ] “How is the energy pipeline this quarter?” returns an answer
- [ ] Pipeline total is based on live board values
- [ ] Sector filter works
- [ ] Date filter works
- [ ] Work-order question returns operational metrics
- [ ] Mixed question reads both boards

## Resilience
- [ ] Blank amount does not crash
- [ ] Blank date does not crash
- [ ] Inconsistent date formats do not crash
- [ ] Unknown columns are reported
- [ ] Missing recognized values are reported

## Hosted
- [ ] Public URL opens without local setup
- [ ] Secrets are configured in the host
- [ ] API keys are not visible in source
- [ ] Chat interface works in an incognito window

## Submission
- [ ] Hosted URL
- [ ] DECISION_LOG.md (<=2 pages when exported)
- [ ] Source ZIP
- [ ] README with setup instructions
