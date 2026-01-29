#!/bin/bash
# Daily Morning Report Generator
# Run this manually or set up via cron: 0 8 * * * /home/ubuntu/clawd/daily-report.sh

echo "========================================="
echo "🌅 DAILY MORNING REPORT - $(date '+%Y-%m-%d')"
echo "========================================="
echo ""

# QC Restaurants Status
echo "📊 QC RESTAURANTS STATUS"
echo "------------------------"
if [ -f /home/ubuntu/clawd/hourly-progress.md ]; then
    echo "Last report: $(head -5 /home/ubuntu/clawd/hourly-progress.md | grep -E "^[0-9]|Trust|Overall" | head -4)"
else
    echo "No report found"
fi
echo ""

# BestGrowthApps Status
echo "📝 BESTGROWTHAPPS STATUS"
echo "------------------------"
echo "Check manually:"
echo "  - Google Search Console for impressions"
echo "  - Affiliate dashboard for clicks"
echo "  - WordPress admin for published articles"
echo ""

# Tasks
echo "📋 TODAY'S TASKS"
echo "---------------"
echo "  - Check QC Restaurants site status"
echo "  - Monitor BestGrowthApps traffic"
echo "  - Continue content creation"
echo ""

echo "========================================="
echo "Report generated at $(date)"
echo "Full reports: /home/ubuntu/clawd/*.md"
echo "========================================="
