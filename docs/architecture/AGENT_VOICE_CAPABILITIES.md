# Agent Voice Capabilities
## OpenClaw Voice Integration for Adamus

### What's Possible
```yaml
capabilities:
  - send_voice_message: 'OpenClaw speaks updates via ElevenLabs'
  - receive_voice: 'Future — voice commands to Adamus'
  - phone_call: 'Critical alerts as actual phone calls'
  - heartbeat_audio: 'Spoken status updates'
```

### Current Status
```yaml
enabled: false
why: 'Nice to have, not critical for Week 0'
when: 'Enable after core system working'

priority: 'Low'
```

### Setup (When Ready)
```bash
# 1. Get ElevenLabs API key
# 2. Add to .env: ELEVENLABS_API_KEY=...
# 3. Configure OpenClaw voice in config.yaml
# 4. Test: 'Adamus, announce yourself'
```

### Use Cases
```yaml
emergency_call:
  trigger: 'Production down or security breach'
  action: 'OpenClaw calls Augustus phone'
  message: 'Emergency: [specific issue]'

heartbeat:
  trigger: 'Every 2 hours during job'
  action: 'Telegram voice note'
  message: 'Completed X features, Y PRs ready'
```

**Status**: PLANNED — Activate post Week 0