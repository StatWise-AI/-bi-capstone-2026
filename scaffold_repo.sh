#!/usr/bin/env bash
# scaffold_repo.sh
# Reads groups.csv (folder_name,github_usernames...) and creates
# groups/<folder_name>/{app,powerbi,data} with a starter README for each
# group. Optional — you can also create folders one at a time through the
# GitHub web UI (see INSTRUCTOR_SETUP.md, Step 3, Option A).
#
# Run once, from the repo root, after cloning:
#   chmod +x scaffold_repo.sh && ./scaffold_repo.sh

set -e

CSV_FILE="groups.csv"

if [ ! -f "$CSV_FILE" ]; then
    echo "Error: $CSV_FILE not found. Put it in the repo root before running this script."
    exit 1
fi

mkdir -p groups

# skip header row, then process each group
tail -n +2 "$CSV_FILE" | while IFS=',' read -r folder_name rest; do
    [ -z "$folder_name" ] && continue

    group_dir="groups/${folder_name}"
    mkdir -p "${group_dir}/app" "${group_dir}/powerbi" "${group_dir}/data"

    if [ ! -f "${group_dir}/README.md" ]; then
        cat > "${group_dir}/README.md" << EOF
# ${folder_name}

## Team members
- (list names here)

## Live links
- Power BI report: (paste your published link here)
- Companion app (AI agent + what-if): (paste your Streamlit Cloud URL here)

## Summary
(1 paragraph: what your dashboard shows and your top recommendation)
EOF
    fi

    echo "Scaffolded ${group_dir}"
done

echo ""
echo "Done. Commit and push:"
echo "  git add groups/"
echo "  git commit -m \"Scaffold group folders\""
echo "  git push origin main"
