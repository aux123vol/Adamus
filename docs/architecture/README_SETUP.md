# README: Setup Guide
## Complete Setup from Zero to Running Adamus

---

## Prerequisites

```bash
# Check Node.js version (need 22+)
node --version

# Check Python (need 3.11+)
python3 --version

# Check Git
git --version

# Check if Claude Code installed
claude --version
```

---

## Step 1: Install Claude Code

```bash
# CORRECT package name (common mistake: wrong name)
npm install -g @anthropic-ai/claude-code

# Verify
claude --version
```

---

## Step 2: Extract Architecture Docs

```bash
# Download adamus_complete_v2.tar.gz from conversation

# Find where it downloaded
find ~ -name "adamus_complete_v2.tar.gz" 2>/dev/null

# Extract (replace path with actual download location)
tar -xzf ~/Downloads/adamus_complete_v2.tar.gz

# You'll see: adamus_systems/ folder
ls adamus_systems/ | wc -l
# Should show 90+ files
```

---

## Step 3: Setup Project

```bash
# Create or enter project (already exists from earlier)
cd ~/adamus

# Create folder structure
mkdir -p src/{coordinator,war_room,business_ai,cambi_ai,tech_ai}
mkdir -p config logs tests docs

# Copy architecture docs
cp -r ~/adamus_systems/* docs/architecture/
# OR (if extracted to different location)
cp -r /path/where/you/extracted/adamus_systems/* docs/architecture/

# Verify
ls docs/architecture/ | wc -l
# Should show 90+
```

---

## Step 4: Configure API Key

```bash
# Create .env file
cat > .env << 'EOF'
ANTHROPIC_API_KEY=sk-ant-YOUR-KEY-HERE
TELEGRAM_TOKEN=YOUR-TELEGRAM-TOKEN
